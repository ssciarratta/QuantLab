"""Protocolo base y contexto para detectores Alpha."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from quantlab.core.types.market import Bar
from quantlab.research.alpha.models import AlphaSignal, SignalScope


@dataclass(frozen=True, slots=True)
class DetectorContext:
    """Datos de entrada compartidos (inmutable)."""

    bars_by_instrument: Mapping[str, Sequence[Bar]]
    timeframe: str
    lookback_bars: int
    venue: str
    market_type: str
    as_of: datetime | None = None
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DetectorRunConfig:
    """Qué detectores ejecutar y con qué overrides."""

    enabled: tuple[str, ...] = ()
    disabled: tuple[str, ...] = ()
    overrides: dict[str, dict[str, Any]] = field(default_factory=dict)


@runtime_checkable
class AlphaDetector(Protocol):
    """Contrato mínimo de un detector autocontenido."""

    @property
    def detector_id(self) -> str: ...

    @property
    def signal_type(self) -> str: ...

    @property
    def scope(self) -> SignalScope: ...

    def required_min_bars(self) -> int: ...

    def detect(self, ctx: DetectorContext) -> tuple[AlphaSignal, ...]: ...
