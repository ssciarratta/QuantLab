"""Detector z-score de spread (pair trading signal)."""

from __future__ import annotations

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
    log_spread,
    ols_hedge_ratio,
    spread_zscore,
)
from quantlab.research.alpha.pairwise.universe import generate_pair_candidates
from quantlab.research.alpha.signals import stable_signal_id


class PairSpreadDetector:
    @property
    def detector_id(self) -> str:
        return "pair_spread"

    @property
    def signal_type(self) -> str:
        return "pair_spread"

    @property
    def scope(self) -> SignalScope:
        return SignalScope.PAIR

    def required_min_bars(self) -> int:
        return 80

    def detect(self, ctx: DetectorContext) -> tuple[AlphaSignal, ...]:
        min_bars = int(ctx.config.get("min_bars", self.required_min_bars()))
        max_pairs = int(ctx.config.get("max_pairs", 100))
        z_window = int(ctx.config.get("z_window", 48))
        entry_z = float(ctx.config.get("entry_z", 2.0))

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
            beta = ols_hedge_ratio(list(aligned.closes_a), list(aligned.closes_b))
            spread = log_spread(list(aligned.closes_a), list(aligned.closes_b), beta)
            zs = spread_zscore(spread, z_window)
            if not zs:
                continue
            z_cur = zs[-1]
            if abs(z_cur) < entry_z:
                continue
            direction = SignalDirection.LONG_SHORT
            out.append(
                AlphaSignal(
                    signal_id=stable_signal_id(
                        signal_type=self.signal_type,
                        scope=SignalScope.PAIR,
                        symbols=(pc.leg_a, pc.leg_b),
                        timestamp=ts,
                        raw_score=abs(z_cur),
                        lag=None,
                        lookback=z_window,
                    ),
                    timestamp=ts,
                    signal_type=self.signal_type,
                    scope=SignalScope.PAIR,
                    symbols=(pc.leg_a, pc.leg_b),
                    direction=direction,
                    raw_score=abs(z_cur),
                    confidence=min(1.0, abs(z_cur) / 4.0),
                    lookback=z_window,
                    timeframe=ctx.timeframe,
                    metadata={
                        "hedge_ratio": beta,
                        "spread_z": z_cur,
                        "estimated_cost_bps": cost_bps,
                    },
                )
            )
        return tuple(out)


register_detector(PairSpreadDetector())
