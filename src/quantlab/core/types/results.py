"""Resultados neutrales de simulación y métricas."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.orders import Fill, Order
from quantlab.core.types.portfolio import PortfolioState
from quantlab.core.types.serialization import dataclass_to_dict
from quantlab.core.types.validation import freeze_mapping, require_aware


@dataclass(frozen=True, slots=True)
class EquityPoint:
    """Punto de la curva de equity."""

    timestamp: datetime
    equity: Decimal

    def __post_init__(self) -> None:
        require_aware(self.timestamp, "timestamp")
        if self.equity.is_nan() or self.equity.is_infinite():
            raise ValidationError("equity no puede ser NaN ni Infinity")


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """Contrato neutral de salida de simulación."""

    experiment_id: str
    equity_curve: tuple[EquityPoint, ...]
    fills: tuple[Fill, ...]
    orders: tuple[Order, ...]
    portfolio_snapshots: tuple[PortfolioState, ...]
    events_log: tuple[dict[str, Any], ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)
    metrics_summary: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", freeze_mapping(self.metadata))
        prev_ts: datetime | None = None
        for point in self.equity_curve:
            if prev_ts is not None and point.timestamp <= prev_ts:
                raise ValidationError("equity_curve requiere timestamps estrictamente ascendentes")
            prev_ts = point.timestamp

    def to_dict(self) -> dict[str, Any]:
        return dataclass_to_dict(self)


@dataclass(frozen=True, slots=True)
class MetricsResult:
    """Contrato neutral de salida del motor de métricas."""

    experiment_id: str
    metrics: Mapping[str, float | int | str]
    computed_at: datetime
    metrics_version: str
    benchmarks: Mapping[str, float | int | str] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "metrics", freeze_mapping(self.metrics))
        if self.benchmarks is not None:
            object.__setattr__(self, "benchmarks", freeze_mapping(self.benchmarks))

    def to_dict(self) -> dict[str, Any]:
        return dataclass_to_dict(self)
