"""Market domain types with enforced invariants and deep immutability."""

from __future__ import annotations

import enum
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import MappingProxyType

from quantlab.core.types.json_types import JsonValue, freeze_json


class OrderSide(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(enum.Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


class TimeInForce(enum.Enum):
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"


class OrderStatus(enum.Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


def _require_positive(value: float, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")


def _require_non_negative(value: float, name: str) -> None:
    if value < 0:
        raise ValueError(f"{name} must be non-negative, got {value}")


def _require_non_empty(value: str, name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{name} must not be empty")


def _require_tz_aware(dt: datetime, name: str) -> None:
    if dt.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")


@dataclass(frozen=True)
class Instrument:
    """A tradeable instrument with validated invariants.

    Metadata is stored as a deeply immutable MappingProxyType.
    """

    symbol: str
    base_asset: str
    quote_asset: str
    tick_size: float
    lot_size: float
    min_notional: float
    metadata: MappingProxyType[str, JsonValue] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        _require_non_empty(self.symbol, "symbol")
        _require_non_empty(self.base_asset, "base_asset")
        _require_non_empty(self.quote_asset, "quote_asset")
        _require_positive(self.tick_size, "tick_size")
        _require_positive(self.lot_size, "lot_size")
        _require_non_negative(self.min_notional, "min_notional")
        if self.base_asset == self.quote_asset:
            raise ValueError("base_asset and quote_asset must differ")
        if not isinstance(self.metadata, MappingProxyType):
            object.__setattr__(self, "metadata", freeze_json(self.metadata))

    @classmethod
    def create(
        cls,
        *,
        symbol: str,
        base_asset: str,
        quote_asset: str,
        tick_size: float,
        lot_size: float,
        min_notional: float = 0.0,
        metadata: Mapping[str, JsonValue] | None = None,
    ) -> Instrument:
        frozen_meta: MappingProxyType[str, JsonValue] = (
            MappingProxyType(dict(metadata)) if metadata else MappingProxyType({})
        )
        return cls(
            symbol=symbol,
            base_asset=base_asset,
            quote_asset=quote_asset,
            tick_size=tick_size,
            lot_size=lot_size,
            min_notional=min_notional,
            metadata=frozen_meta,
        )


@dataclass(frozen=True)
class Bar:
    """OHLCV bar with validated invariants.

    Enforces: timestamps tz-aware, high >= open/close/low,
    low <= open/close, positive prices, non-negative volume.
    """

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str

    def __post_init__(self) -> None:
        _require_tz_aware(self.timestamp, "timestamp")
        _require_positive(self.open, "open")
        _require_positive(self.high, "high")
        _require_positive(self.low, "low")
        _require_positive(self.close, "close")
        _require_non_negative(self.volume, "volume")
        if self.high < self.open:
            raise ValueError(f"high ({self.high}) must be >= open ({self.open})")
        if self.high < self.close:
            raise ValueError(f"high ({self.high}) must be >= close ({self.close})")
        if self.high < self.low:
            raise ValueError(f"high ({self.high}) must be >= low ({self.low})")
        if self.low > self.open:
            raise ValueError(f"low ({self.low}) must be <= open ({self.open})")
        if self.low > self.close:
            raise ValueError(f"low ({self.low}) must be <= close ({self.close})")
        _require_non_empty(self.symbol, "symbol")


@dataclass(frozen=True)
class BookLevel:
    """A single level in an order book."""

    price: float
    quantity: float

    def __post_init__(self) -> None:
        _require_positive(self.price, "price")
        _require_non_negative(self.quantity, "quantity")


@dataclass(frozen=True)
class Trade:
    """An executed trade from market data."""

    symbol: str
    price: float
    quantity: float
    timestamp: datetime
    side: OrderSide

    def __post_init__(self) -> None:
        _require_non_empty(self.symbol, "symbol")
        _require_positive(self.price, "price")
        _require_positive(self.quantity, "quantity")
        _require_tz_aware(self.timestamp, "timestamp")


@dataclass(frozen=True)
class Fill:
    """An order fill (execution confirmation)."""

    order_id: str
    price: float
    quantity: float
    timestamp: datetime
    side: OrderSide
    fee: float = 0.0

    def __post_init__(self) -> None:
        _require_non_empty(self.order_id, "order_id")
        _require_positive(self.price, "price")
        _require_positive(self.quantity, "quantity")
        _require_tz_aware(self.timestamp, "timestamp")
        _require_non_negative(self.fee, "fee")


@dataclass(frozen=True)
class Order:
    """An order with validated invariants."""

    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    filled_quantity: float = 0.0
    price: float | None = None
    time_in_force: TimeInForce = TimeInForce.GTC
    status: OrderStatus = OrderStatus.PENDING
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        _require_non_empty(self.order_id, "order_id")
        _require_non_empty(self.symbol, "symbol")
        _require_positive(self.quantity, "quantity")
        _require_non_negative(self.filled_quantity, "filled_quantity")
        if self.filled_quantity > self.quantity:
            raise ValueError(
                f"filled_quantity ({self.filled_quantity}) must be <= quantity ({self.quantity})"
            )
        if self.order_type == OrderType.LIMIT:
            if self.price is None:
                raise ValueError("LIMIT order requires a price")
            _require_positive(self.price, "price")
        if self.price is not None and self.order_type == OrderType.MARKET:
            pass  # market orders may optionally carry a price hint
        _require_tz_aware(self.timestamp, "timestamp")
