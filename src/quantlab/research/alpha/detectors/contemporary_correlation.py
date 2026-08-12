"""Correlación contemporánea entre pares (baseline)."""

from __future__ import annotations

import math
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
from quantlab.research.alpha.pairwise.universe import generate_pair_candidates
from quantlab.research.alpha.signals import stable_signal_id


def _returns(closes: tuple[float, ...]) -> tuple[float, ...]:
    if len(closes) < 2:
        return ()
    return tuple(
        (closes[i] / closes[i - 1] - 1.0) if closes[i - 1] else 0.0 for i in range(1, len(closes))
    )


def _pearson(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    n = min(len(a), len(b))
    if n < 3:
        return 0.0
    ma = sum(a[:n]) / n
    mb = sum(b[:n]) / n
    num = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    da = math.sqrt(sum((a[i] - ma) ** 2 for i in range(n)))
    db = math.sqrt(sum((b[i] - mb) ** 2 for i in range(n)))
    if da == 0 or db == 0:
        return 0.0
    return num / (da * db)


class ContemporaryCorrelationDetector:
    @property
    def detector_id(self) -> str:
        return "contemporary_correlation"

    @property
    def signal_type(self) -> str:
        return "contemporary_correlation"

    @property
    def scope(self) -> SignalScope:
        return SignalScope.PAIR

    def required_min_bars(self) -> int:
        return 50

    def detect(self, ctx: DetectorContext) -> tuple[AlphaSignal, ...]:
        min_bars = int(ctx.config.get("min_bars", self.required_min_bars()))
        max_pairs = int(ctx.config.get("max_pairs", 200))
        min_corr = float(ctx.config.get("min_abs_corr", 0.15))
        pairs = generate_pair_candidates(
            ctx.bars_by_instrument,
            max_pairs=max_pairs,
            min_bars=min_bars,
        )
        ts = ctx.as_of or datetime.now(tz=UTC)
        cost_bps = estimate_pair_cost_bps(venue=ctx.venue, market_type=ctx.market_type)
        out: list[AlphaSignal] = []
        lookback = ctx.lookback_bars or min_bars
        for pc in pairs:
            aligned = align_pair_bars(
                ctx.bars_by_instrument[pc.leg_a],
                ctx.bars_by_instrument[pc.leg_b],
            )
            if aligned is None:
                continue
            ra = _returns(aligned.closes_a)
            rb = _returns(aligned.closes_b)
            if len(ra) < 10:
                continue
            corr = _pearson(ra[-lookback:], rb[-lookback:])
            if abs(corr) < min_corr:
                continue
            out.append(
                AlphaSignal(
                    signal_id=stable_signal_id(
                        signal_type=self.signal_type,
                        scope=SignalScope.PAIR,
                        symbols=(pc.leg_a, pc.leg_b),
                        timestamp=ts,
                        raw_score=abs(corr),
                        lag=0,
                        lookback=lookback,
                    ),
                    timestamp=ts,
                    signal_type=self.signal_type,
                    scope=SignalScope.PAIR,
                    symbols=(pc.leg_a, pc.leg_b),
                    direction=SignalDirection.LONG_SHORT,
                    raw_score=abs(corr),
                    confidence=abs(corr),
                    lookback=lookback,
                    lag=0,
                    timeframe=ctx.timeframe,
                    metadata={"corr": corr, "estimated_cost_bps": cost_bps},
                )
            )
        return tuple(out)


register_detector(ContemporaryCorrelationDetector())
