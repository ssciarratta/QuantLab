"""Adapter: perfiles legacy → detector registrable."""

from __future__ import annotations

from datetime import UTC, datetime

from quantlab.research.alpha.detectors.base import DetectorContext
from quantlab.research.alpha.detectors.registry import register_detector
from quantlab.research.alpha.models import (
    AlphaSignal,
    SignalDirection,
    SignalScope,
)
from quantlab.research.alpha.profiles import build_profile, score_with_profile
from quantlab.research.alpha.signals import stable_signal_id


class LegacyProfileDetector:
    """Envuelve ``build_profile`` / ``score_with_profile`` sin cambiar scoring."""

    def __init__(self, profile_name: str = "legacy_v1") -> None:
        self._profile_name = profile_name.strip().lower()

    @property
    def detector_id(self) -> str:
        return f"legacy_{self._profile_name}"

    @property
    def signal_type(self) -> str:
        return self._profile_name

    @property
    def scope(self) -> SignalScope:
        return SignalScope.INDIVIDUAL

    def required_min_bars(self) -> int:
        return 3

    def detect(self, ctx: DetectorContext) -> tuple[AlphaSignal, ...]:
        profile = build_profile(self._profile_name)
        rows = score_with_profile(ctx.bars_by_instrument, profile)
        ts = ctx.as_of or datetime.now(tz=UTC)
        signals: list[AlphaSignal] = []
        for row in rows:
            if row.excluded:
                continue
            sym = row.instrument_id
            signals.append(
                AlphaSignal(
                    signal_id=stable_signal_id(
                        signal_type=self.signal_type,
                        scope=SignalScope.INDIVIDUAL,
                        symbols=(sym,),
                        timestamp=ts,
                        raw_score=row.composite,
                        lag=None,
                        lookback=ctx.lookback_bars,
                    ),
                    timestamp=ts,
                    signal_type=self.signal_type,
                    scope=SignalScope.INDIVIDUAL,
                    symbols=(sym,),
                    direction=SignalDirection.LONG,
                    raw_score=row.composite,
                    lookback=ctx.lookback_bars,
                    timeframe=ctx.timeframe,
                    metadata={"base_score": row.base_score},
                )
            )
        return tuple(signals)


def register_legacy_detectors() -> None:
    """Registra perfiles principales como detectores (idempotente)."""
    from quantlab.research.alpha.detectors.registry import global_registry

    reg = global_registry()
    for name in ("legacy_v1", "momentum", "mean_reversion", "market_making"):
        det = LegacyProfileDetector(name)
        if det.detector_id not in reg.list_ids():
            register_detector(det)
