"""Correlación rezagada con corrección Benjamini-Hochberg (FDR)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime

from quantlab.research.alpha.detectors.base import DetectorContext
from quantlab.research.alpha.detectors.registry import register_detector
from quantlab.research.alpha.models import (
    AlphaSignal,
    SignalDirection,
    SignalScope,
)
from quantlab.research.alpha.pairwise.align import align_pair_bars
from quantlab.research.alpha.pairwise.costs import estimate_pair_cost_bps
from quantlab.research.alpha.pairwise.universe import PairCandidate, generate_pair_candidates
from quantlab.research.alpha.signals import stable_signal_id


def _returns(closes: tuple[float, ...]) -> list[float]:
    if len(closes) < 2:
        return []
    return [
        (closes[i] / closes[i - 1] - 1.0) if closes[i - 1] else 0.0 for i in range(1, len(closes))
    ]


def _pearson(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    if n < 4:
        return 0.0
    ma = sum(a[:n]) / n
    mb = sum(b[:n]) / n
    num = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    da = math.sqrt(sum((a[i] - ma) ** 2 for i in range(n)))
    db = math.sqrt(sum((b[i] - mb) ** 2 for i in range(n)))
    if da == 0 or db == 0:
        return 0.0
    return num / (da * db)


def _corr_pvalue(r: float, n: int) -> float:
    """Aproximación two-tailed sin scipy."""
    if n < 4 or abs(r) >= 1.0:
        return 1.0
    t = abs(r) * math.sqrt((n - 2) / max(1e-12, 1.0 - r * r))
    # Surrogate p ~ 2 * exp(-0.717 * t - 0.416 * t^2) for moderate t
    p = 2.0 * math.exp(-0.717 * t - 0.416 * t * t)
    return min(1.0, max(0.0, p))


def benjamini_hochberg(
    p_values: list[float],
    *,
    alpha: float = 0.10,
) -> list[bool]:
    """Retorna máscara de rechazos bajo FDR."""
    m = len(p_values)
    if m == 0:
        return []
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    thresholds = [(i + 1) / m * alpha for i in range(m)]
    max_k = -1
    for k, ((_idx, p), thr) in enumerate(zip(indexed, thresholds, strict=True)):
        if p <= thr:
            max_k = k
    if max_k < 0:
        return [False] * m
    reject_idx = {indexed[i][0] for i in range(max_k + 1)}
    return [i in reject_idx for i in range(m)]


@dataclass(frozen=True, slots=True)
class _LagTrial:
    pair: PairCandidate
    lag: int
    corr: float
    pvalue: float
    n_obs: int


class LaggedCorrelationDetector:
    @property
    def detector_id(self) -> str:
        return "lagged_correlation"

    @property
    def signal_type(self) -> str:
        return "lagged_correlation"

    @property
    def scope(self) -> SignalScope:
        return SignalScope.PAIR

    def required_min_bars(self) -> int:
        return 80

    def detect(self, ctx: DetectorContext) -> tuple[AlphaSignal, ...]:
        min_bars = int(ctx.config.get("min_bars", self.required_min_bars()))
        max_pairs = int(ctx.config.get("max_pairs", 100))
        lags_cfg = ctx.config.get("lags")
        lags: tuple[int, ...] = (
            tuple(int(x) for x in lags_cfg)
            if isinstance(lags_cfg, (list, tuple))
            else (0, 1, 2, 3, 4, 5, 6, 12, 24)
        )
        fdr_alpha = float(ctx.config.get("fdr_alpha", 0.10))
        min_abs_corr = float(ctx.config.get("min_abs_corr", 0.15))
        lookback = int(ctx.config.get("lookback", ctx.lookback_bars or 120))

        pairs = generate_pair_candidates(
            ctx.bars_by_instrument,
            max_pairs=max_pairs,
            min_bars=min_bars,
        )
        trials: list[_LagTrial] = []
        for pc in pairs:
            aligned = align_pair_bars(
                ctx.bars_by_instrument[pc.leg_a],
                ctx.bars_by_instrument[pc.leg_b],
            )
            if aligned is None:
                continue
            ra = _returns(aligned.closes_a)
            rb = _returns(aligned.closes_b)
            window_a = ra[-lookback:] if len(ra) >= lookback else ra
            window_b = rb[-lookback:] if len(rb) >= lookback else rb
            for lag in lags:
                if lag >= len(window_a) - 3:
                    continue
                a_slice = window_a[lag:]
                b_slice = window_b[: len(window_a) - lag]
                n = min(len(a_slice), len(b_slice))
                if n < 8:
                    continue
                corr = _pearson(a_slice[:n], b_slice[:n])
                if abs(corr) < min_abs_corr:
                    continue
                pval = _corr_pvalue(corr, n)
                trials.append(_LagTrial(pc, lag, corr, pval, n))

        if not trials:
            return ()

        reject = benjamini_hochberg([t.pvalue for t in trials], alpha=fdr_alpha)
        ts = ctx.as_of or datetime.now(tz=UTC)
        cost_bps = estimate_pair_cost_bps(venue=ctx.venue, market_type=ctx.market_type)
        out: list[AlphaSignal] = []
        for trial, ok in zip(trials, reject, strict=True):
            if not ok:
                continue
            out.append(
                AlphaSignal(
                    signal_id=stable_signal_id(
                        signal_type=self.signal_type,
                        scope=SignalScope.PAIR,
                        symbols=(trial.pair.leg_a, trial.pair.leg_b),
                        timestamp=ts,
                        raw_score=abs(trial.corr),
                        lag=trial.lag,
                        lookback=lookback,
                    ),
                    timestamp=ts,
                    signal_type=self.signal_type,
                    scope=SignalScope.PAIR,
                    symbols=(trial.pair.leg_a, trial.pair.leg_b),
                    direction=SignalDirection.LONG_SHORT,
                    raw_score=abs(trial.corr),
                    confidence=1.0 - trial.pvalue,
                    lookback=lookback,
                    lag=trial.lag,
                    timeframe=ctx.timeframe,
                    metadata={
                        "corr": trial.corr,
                        "pvalue": trial.pvalue,
                        "n_obs": trial.n_obs,
                        "fdr_alpha": fdr_alpha,
                        "estimated_cost_bps": cost_bps,
                    },
                )
            )
        return tuple(out)


register_detector(LaggedCorrelationDetector())
