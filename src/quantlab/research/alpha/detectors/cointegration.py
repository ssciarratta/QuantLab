"""Detector de cointegración pairwise (ADF proxy + half-life)."""

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
from quantlab.research.alpha.pairwise.stats import (
    adf_pvalue_proxy,
    half_life_bars,
    log_spread,
    ols_hedge_ratio,
    spread_zscore,
)
from quantlab.research.alpha.pairwise.universe import generate_pair_candidates
from quantlab.research.alpha.signals import stable_signal_id


class CointegrationDetector:
    @property
    def detector_id(self) -> str:
        return "cointegration"

    @property
    def signal_type(self) -> str:
        return "cointegration"

    @property
    def scope(self) -> SignalScope:
        return SignalScope.PAIR

    def required_min_bars(self) -> int:
        return 120

    def detect(self, ctx: DetectorContext) -> tuple[AlphaSignal, ...]:
        min_bars = int(ctx.config.get("min_bars", self.required_min_bars()))
        max_pairs = int(ctx.config.get("max_pairs", 80))
        adf_max_p = float(ctx.config.get("adf_max_p", 0.05))
        z_window = int(ctx.config.get("z_window", 48))
        min_hl = float(ctx.config.get("min_half_life", 5))
        max_hl = float(ctx.config.get("max_half_life", 500))

        pairs = generate_pair_candidates(
            ctx.bars_by_instrument,
            max_pairs=max_pairs,
            min_bars=min_bars,
        )
        ts = ctx.as_of or datetime.now(tz=UTC)
        cost_bps = estimate_pair_cost_bps(venue=ctx.venue, market_type=ctx.market_type)
        out: list[AlphaSignal] = []

        for pc in pairs:
            aligned = align_pair_bars(
                ctx.bars_by_instrument[pc.leg_a],
                ctx.bars_by_instrument[pc.leg_b],
            )
            if aligned is None:
                continue
            ca = list(aligned.closes_a)
            cb = list(aligned.closes_b)
            beta = ols_hedge_ratio(
                [math.log(c) for c in ca if c > 0],
                [math.log(c) for c in cb if c > 0],
            )
            spread = log_spread(ca, cb, beta)
            if len(spread) < min_bars:
                continue
            pval = adf_pvalue_proxy(spread)
            if pval > adf_max_p:
                continue
            hl = half_life_bars(spread)
            if hl is None or hl < min_hl or hl > max_hl:
                continue
            zs = spread_zscore(spread, z_window)
            if not zs:
                continue
            z_cur = zs[-1]
            if abs(z_cur) > 4.0:
                continue
            raw = 1.0 - pval
            out.append(
                AlphaSignal(
                    signal_id=stable_signal_id(
                        signal_type=self.signal_type,
                        scope=SignalScope.PAIR,
                        symbols=(pc.leg_a, pc.leg_b),
                        timestamp=ts,
                        raw_score=raw,
                        lag=None,
                        lookback=len(spread),
                    ),
                    timestamp=ts,
                    signal_type=self.signal_type,
                    scope=SignalScope.PAIR,
                    symbols=(pc.leg_a, pc.leg_b),
                    direction=SignalDirection.LONG_SHORT,
                    raw_score=raw,
                    confidence=1.0 - pval,
                    lookback=len(spread),
                    timeframe=ctx.timeframe,
                    metadata={
                        "hedge_ratio": beta,
                        "adf_pvalue": pval,
                        "half_life_bars": hl,
                        "spread_z": z_cur,
                        "estimated_cost_bps": cost_bps,
                    },
                )
            )
        return tuple(out)


register_detector(CointegrationDetector())
