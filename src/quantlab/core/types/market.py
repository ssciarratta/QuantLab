"""Eventos de mercado y series temporales."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import BookChangeAction, BookSide, EventType, OrderSide
from quantlab.core.types.validation import (
    require_aware,
    require_non_empty_str,
    require_non_negative,
    require_positive,
)


@dataclass(frozen=True, slots=True)
class Bar:
    """OHLCV agregado."""

    instrument_id: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    timestamp_open: datetime
    timestamp_close: datetime
    timeframe: str

    def __post_init__(self) -> None:
        require_non_empty_str(self.instrument_id, "instrument_id")
        require_non_empty_str(self.timeframe, "timeframe")
        for name in ("open", "high", "low", "close"):
            require_positive(getattr(self, name), name)
        require_non_negative(self.volume, "volume")
        require_aware(self.timestamp_open, "timestamp_open")
        require_aware(self.timestamp_close, "timestamp_close")
        if self.timestamp_close < self.timestamp_open:
            raise ValidationError("timestamp_close debe ser >= timestamp_open")
        if self.high < self.open or self.high < self.close or self.high < self.low:
            raise ValidationError("high debe ser >= open, close y low")
        if self.low > self.open or self.low > self.close or self.low > self.high:
            raise ValidationError("low debe ser <= open, close y high")


@dataclass(frozen=True, slots=True)
class Trade:
    """Tick de mercado ejecutado."""

    instrument_id: str
    price: Decimal
    quantity: Decimal
    side: OrderSide
    timestamp: datetime
    trade_id: str

    def __post_init__(self) -> None:
        require_non_empty_str(self.instrument_id, "instrument_id")
        require_non_empty_str(self.trade_id, "trade_id")
        require_positive(self.price, "price")
        require_positive(self.quantity, "quantity")
        require_aware(self.timestamp, "timestamp")


@dataclass(frozen=True, slots=True)
class BookLevel:
    """Nivel individual del libro de órdenes."""

    price: Decimal
    quantity: Decimal

    def __post_init__(self) -> None:
        require_positive(self.price, "price")
        require_non_negative(self.quantity, "quantity")


@dataclass(frozen=True, slots=True)
class OrderBookSnapshot:
    """Estado completo del libro."""

    instrument_id: str
    timestamp: datetime
    bids: tuple[BookLevel, ...]
    asks: tuple[BookLevel, ...]
    sequence_id: int

    def __post_init__(self) -> None:
        require_non_empty_str(self.instrument_id, "instrument_id")
        require_aware(self.timestamp, "timestamp")
        if self.sequence_id < 0:
            raise ValidationError("sequence_id no puede ser negativo")


@dataclass(frozen=True, slots=True)
class BookChange:
    """Cambio incremental del libro."""

    side: BookSide
    price: Decimal
    quantity: Decimal
    action: BookChangeAction

    def __post_init__(self) -> None:
        require_positive(self.price, "price")
        require_non_negative(self.quantity, "quantity")


@dataclass(frozen=True, slots=True)
class OrderBookDelta:
    """Delta incremental del libro."""

    instrument_id: str
    timestamp: datetime
    sequence_id: int
    changes: tuple[BookChange, ...]

    def __post_init__(self) -> None:
        require_non_empty_str(self.instrument_id, "instrument_id")
        require_aware(self.timestamp, "timestamp")
        if self.sequence_id < 0:
            raise ValidationError("sequence_id no puede ser negativo")


@dataclass(frozen=True, slots=True)
class MarketEvent:
    """Evento unificado del bus de simulación."""

    event_id: str
    event_type: EventType
    timestamp: datetime
    instrument_id: str
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty_str(self.event_id, "event_id")
        require_non_empty_str(self.instrument_id, "instrument_id")
        require_aware(self.timestamp, "timestamp")
