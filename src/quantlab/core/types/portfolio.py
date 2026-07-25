"""Portfolio, balances y estado de ejecución."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import ClockMode, ClockSpeed, OrderStatus
from quantlab.core.types.orders import Fill
from quantlab.core.types.validation import (
    require_aware,
    require_non_empty_str,
    require_non_negative,
)


@dataclass(frozen=True, slots=True)
class Position:
    """Exposición neta en un instrumento."""

    instrument_id: str
    quantity: Decimal
    avg_entry_price: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    updated_at: datetime

    def __post_init__(self) -> None:
        require_non_empty_str(self.instrument_id, "instrument_id")
        require_aware(self.updated_at, "updated_at")


@dataclass(frozen=True, slots=True)
class Balance:
    """Saldo de un activo."""

    asset: str
    available: Decimal
    locked: Decimal
    total: Decimal
    updated_at: datetime

    def __post_init__(self) -> None:
        require_non_empty_str(self.asset, "asset")
        require_non_negative(self.available, "available")
        require_non_negative(self.locked, "locked")
        require_non_negative(self.total, "total")
        require_aware(self.updated_at, "updated_at")
        if self.available + self.locked != self.total:
            raise ValidationError("available + locked debe ser igual a total")


@dataclass(frozen=True, slots=True)
class PortfolioState:
    """Snapshot agregado de portfolio."""

    timestamp: datetime
    positions: tuple[Position, ...]
    balances: tuple[Balance, ...]
    total_equity: Decimal
    total_realized_pnl: Decimal
    total_unrealized_pnl: Decimal

    def __post_init__(self) -> None:
        require_aware(self.timestamp, "timestamp")


@dataclass(frozen=True, slots=True)
class ExecutionReport:
    """Reporte del ciclo de vida de una orden."""

    order_id: str
    status: OrderStatus
    fills: tuple[Fill, ...]
    reject_reason: str | None
    timestamp: datetime

    def __post_init__(self) -> None:
        require_non_empty_str(self.order_id, "order_id")
        require_aware(self.timestamp, "timestamp")


@dataclass(frozen=True, slots=True)
class SimulationClock:
    """Reloj virtual de simulación."""

    current_time: datetime
    mode: ClockMode
    speed: ClockSpeed

    def __post_init__(self) -> None:
        require_aware(self.current_time, "current_time")
