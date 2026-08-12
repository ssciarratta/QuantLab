"""Registro de detectores Alpha — extensible sin editar archivo central."""

from __future__ import annotations

from dataclasses import dataclass, field

from quantlab.core.exceptions import ValidationError
from quantlab.research.alpha.detectors.base import (
    AlphaDetector,
    DetectorContext,
    DetectorRunConfig,
)
from quantlab.research.alpha.models import AlphaSignal


@dataclass
class DetectorRegistry:
    """Registro in-memory de detectores; thread-unsafe (lab single-process)."""

    _detectors: dict[str, AlphaDetector] = field(default_factory=dict)

    def register(self, detector: AlphaDetector) -> None:
        did = detector.detector_id.strip().lower()
        if not did:
            raise ValidationError("detector_id vacío")
        self._detectors[did] = detector

    def get(self, detector_id: str) -> AlphaDetector:
        key = detector_id.strip().lower()
        if key not in self._detectors:
            raise ValidationError(f"detector desconocido: {detector_id!r}")
        return self._detectors[key]

    def list_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._detectors))

    def list_detectors(self) -> tuple[AlphaDetector, ...]:
        return tuple(self._detectors[k] for k in sorted(self._detectors))

    def resolve_enabled(self, config: DetectorRunConfig) -> tuple[AlphaDetector, ...]:
        if config.enabled:
            ids = [i.strip().lower() for i in config.enabled]
        else:
            disabled = {d.strip().lower() for d in config.disabled}
            ids = [i for i in sorted(self._detectors) if i not in disabled]
        out: list[AlphaDetector] = []
        for did in ids:
            if did not in self._detectors:
                raise ValidationError(f"detector desconocido en enabled: {did!r}")
            out.append(self._detectors[did])
        return tuple(out)

    def run_all(
        self,
        ctx: DetectorContext,
        config: DetectorRunConfig,
    ) -> tuple[AlphaSignal, ...]:
        signals: list[AlphaSignal] = []
        for det in self.resolve_enabled(config):
            min_bars = det.required_min_bars()
            too_short = [
                iid
                for iid, bars in ctx.bars_by_instrument.items()
                if len(bars) < min_bars
            ]
            if det.scope.value == "individual" and too_short:
                continue
            override = config.overrides.get(det.detector_id, {})
            if override:
                ctx = DetectorContext(
                    bars_by_instrument=ctx.bars_by_instrument,
                    timeframe=ctx.timeframe,
                    lookback_bars=ctx.lookback_bars,
                    venue=ctx.venue,
                    market_type=ctx.market_type,
                    as_of=ctx.as_of,
                    config={**ctx.config, **override},
                )
            signals.extend(det.detect(ctx))
        return tuple(signals)


_GLOBAL_REGISTRY = DetectorRegistry()


def global_registry() -> DetectorRegistry:
    return _GLOBAL_REGISTRY


def register_detector(detector: AlphaDetector) -> AlphaDetector:
    """Decorador/función para registrar al importar módulo detector."""
    _GLOBAL_REGISTRY.register(detector)
    return detector
