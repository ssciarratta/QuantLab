"""Trading domain types: events, intents, contexts, results."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import MappingProxyType

from quantlab.core.types.json_types import JsonValue, freeze_json
from quantlab.core.types.market import (
    Instrument,
    OrderSide,
    OrderType,
    TimeInForce,
    _require_non_empty,
    _require_non_negative,
    _require_positive,
    _require_tz_aware,
)


class MarketEventType(enum.Enum):
    BAR = "BAR"
    TRADE = "TRADE"
    BOOK_UPDATE = "BOOK_UPDATE"
    FILL = "FILL"


class IntentType(enum.Enum):
    PLACE_ORDER = "PLACE_ORDER"
    CANCEL_ORDER = "CANCEL_ORDER"
    REPLACE_ORDER = "REPLACE_ORDER"
    NO_ACTION = "NO_ACTION"


@dataclass(frozen=True)
class MarketEvent:
    """An event from the market, carrying an immutable payload."""

    event_type: MarketEventType
    timestamp: datetime
    symbol: str
    payload: MappingProxyType[str, JsonValue] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        _require_tz_aware(self.timestamp, "timestamp")
        _require_non_empty(self.symbol, "symbol")
        if not isinstance(self.payload, MappingProxyType):
            object.__setattr__(self, "payload", freeze_json(self.payload))

    @classmethod
    def create(
        cls,
        *,
        event_type: MarketEventType,
        timestamp: datetime,
        symbol: str,
        payload: dict[str, object] | None = None,
    ) -> MarketEvent:
        frozen = (
            MappingProxyType({str(k): freeze_json(v) for k, v in payload.items()})
            if payload
            else MappingProxyType({})
        )
        return cls(
            event_type=event_type,
            timestamp=timestamp,
            symbol=symbol,
            payload=frozen,
        )


@dataclass(frozen=True)
class StrategyContext:
    """Read-only context passed to strategies. Parameters are deeply immutable."""

    timestamp: datetime
    balance_available: float
    balance_locked: float
    position: float
    parameters: MappingProxyType[str, JsonValue] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        _require_tz_aware(self.timestamp, "timestamp")
        _require_non_negative(self.balance_available, "balance_available")
        _require_non_negative(self.balance_locked, "balance_locked")
        if not isinstance(self.parameters, MappingProxyType):
            object.__setattr__(self, "parameters", freeze_json(self.parameters))

    @classmethod
    def create(
        cls,
        *,
        timestamp: datetime,
        balance_available: float,
        balance_locked: float,
        position: float = 0.0,
        parameters: dict[str, object] | None = None,
    ) -> StrategyContext:
        frozen = (
            MappingProxyType({str(k): freeze_json(v) for k, v in parameters.items()})
            if parameters
            else MappingProxyType({})
        )
        return cls(
            timestamp=timestamp,
            balance_available=balance_available,
            balance_locked=balance_locked,
            position=position,
            parameters=frozen,
        )


@dataclass(frozen=True)
class OrderIntent:
    """Validated intent from a strategy.

    Validation rules by intent type:
    - PLACE_ORDER: requires instrument, side, quantity (>0), order_type,
      price (>0) for LIMIT, optional time_in_force.
    - CANCEL_ORDER: requires target_order_id. No incompatible fields.
    - REPLACE_ORDER: requires target_order_id + new valid values.
    - NO_ACTION: must not contain price, quantity, side, order_type, or target ids.
    """

    intent_type: IntentType
    instrument: Instrument | None = None
    side: OrderSide | None = None
    quantity: float | None = None
    order_type: OrderType | None = None
    price: float | None = None
    time_in_force: TimeInForce | None = None
    target_order_id: str | None = None
    new_quantity: float | None = None
    new_price: float | None = None

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        it = self.intent_type

        if it == IntentType.PLACE_ORDER:
            self._validate_place_order()
        elif it == IntentType.CANCEL_ORDER:
            self._validate_cancel_order()
        elif it == IntentType.REPLACE_ORDER:
            self._validate_replace_order()
        elif it == IntentType.NO_ACTION:
            self._validate_no_action()

    def _validate_place_order(self) -> None:
        if self.instrument is None:
            raise ValueError("PLACE_ORDER requires instrument")
        if self.side is None:
            raise ValueError("PLACE_ORDER requires side")
        if self.quantity is None:
            raise ValueError("PLACE_ORDER requires quantity")
        _require_positive(self.quantity, "quantity")
        if self.order_type is None:
            raise ValueError("PLACE_ORDER requires order_type")
        if self.order_type == OrderType.LIMIT:
            if self.price is None:
                raise ValueError("LIMIT order requires price")
            _require_positive(self.price, "price")
        if self.target_order_id is not None:
            raise ValueError("PLACE_ORDER must not have target_order_id")
        if self.new_quantity is not None or self.new_price is not None:
            raise ValueError("PLACE_ORDER must not have replacement fields")

    def _validate_cancel_order(self) -> None:
        if self.target_order_id is None:
            raise ValueError("CANCEL_ORDER requires target_order_id")
        _require_non_empty(self.target_order_id, "target_order_id")
        incompatible = {
            "instrument": self.instrument,
            "side": self.side,
            "quantity": self.quantity,
            "order_type": self.order_type,
            "price": self.price,
            "time_in_force": self.time_in_force,
            "new_quantity": self.new_quantity,
            "new_price": self.new_price,
        }
        present = [k for k, v in incompatible.items() if v is not None]
        if present:
            raise ValueError(f"CANCEL_ORDER must not include: {', '.join(present)}")

    def _validate_replace_order(self) -> None:
        if self.target_order_id is None:
            raise ValueError("REPLACE_ORDER requires target_order_id")
        _require_non_empty(self.target_order_id, "target_order_id")
        if self.new_quantity is None and self.new_price is None:
            raise ValueError("REPLACE_ORDER requires at least new_quantity or new_price")
        if self.new_quantity is not None:
            _require_positive(self.new_quantity, "new_quantity")
        if self.new_price is not None:
            _require_positive(self.new_price, "new_price")

    def _validate_no_action(self) -> None:
        forbidden = {
            "price": self.price,
            "quantity": self.quantity,
            "side": self.side,
            "order_type": self.order_type,
            "target_order_id": self.target_order_id,
            "new_quantity": self.new_quantity,
            "new_price": self.new_price,
            "instrument": self.instrument,
        }
        present = [k for k, v in forbidden.items() if v is not None]
        if present:
            raise ValueError(f"NO_ACTION must not contain: {', '.join(present)}")


@dataclass(frozen=True)
class TimeRange:
    """A time range with validated invariants."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        _require_tz_aware(self.start, "start")
        _require_tz_aware(self.end, "end")
        if self.start >= self.end:
            raise ValueError(f"start ({self.start}) must be before end ({self.end})")


@dataclass(frozen=True)
class Balance:
    """Account balance with consistency invariants."""

    available: float
    locked: float
    total: float

    def __post_init__(self) -> None:
        _require_non_negative(self.available, "available")
        _require_non_negative(self.locked, "locked")
        _require_non_negative(self.total, "total")
        expected = round(self.available + self.locked, 10)
        actual = round(self.total, 10)
        if abs(expected - actual) > 1e-9:
            raise ValueError(
                f"total ({self.total}) must equal available + locked "
                f"({self.available} + {self.locked} = {self.available + self.locked})"
            )


@dataclass(frozen=True)
class SimulationResult:
    """Results from a simulation run. All fields are deeply immutable."""

    experiment_id: str
    timestamp: datetime
    metadata: MappingProxyType[str, JsonValue] = field(
        default_factory=lambda: MappingProxyType({})
    )
    events_log: tuple[MappingProxyType[str, JsonValue], ...] = ()

    def __post_init__(self) -> None:
        _require_non_empty(self.experiment_id, "experiment_id")
        _require_tz_aware(self.timestamp, "timestamp")
        if not isinstance(self.metadata, MappingProxyType):
            object.__setattr__(self, "metadata", freeze_json(self.metadata))
        if not isinstance(self.events_log, tuple):
            frozen_events = tuple(freeze_json(e) for e in self.events_log)
            object.__setattr__(self, "events_log", frozen_events)

    @classmethod
    def create(
        cls,
        *,
        experiment_id: str,
        timestamp: datetime | None = None,
        metadata: dict[str, object] | None = None,
        events_log: list[dict[str, object]] | None = None,
    ) -> SimulationResult:
        ts = timestamp or datetime.now(UTC)
        frozen_meta: MappingProxyType[str, JsonValue] = (
            MappingProxyType({str(k): freeze_json(v) for k, v in metadata.items()})
            if metadata
            else MappingProxyType({})
        )
        frozen_events = (
            tuple(
                MappingProxyType({str(k): freeze_json(v) for k, v in e.items()})
                for e in events_log
            )
            if events_log
            else ()
        )
        return cls(
            experiment_id=experiment_id,
            timestamp=ts,
            metadata=frozen_meta,
            events_log=frozen_events,
        )


@dataclass(frozen=True)
class MetricsResult:
    """Result of metrics calculation. All fields deeply immutable."""

    experiment_id: str
    timestamp: datetime
    metrics: MappingProxyType[str, JsonValue] = field(default_factory=lambda: MappingProxyType({}))
    benchmarks: MappingProxyType[str, JsonValue] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        _require_non_empty(self.experiment_id, "experiment_id")
        _require_tz_aware(self.timestamp, "timestamp")
        if not isinstance(self.metrics, MappingProxyType):
            object.__setattr__(self, "metrics", freeze_json(self.metrics))
        if not isinstance(self.benchmarks, MappingProxyType):
            object.__setattr__(self, "benchmarks", freeze_json(self.benchmarks))

    @classmethod
    def create(
        cls,
        *,
        experiment_id: str,
        timestamp: datetime | None = None,
        metrics: dict[str, object] | None = None,
        benchmarks: dict[str, object] | None = None,
    ) -> MetricsResult:
        ts = timestamp or datetime.now(UTC)
        frozen_metrics: MappingProxyType[str, JsonValue] = (
            MappingProxyType({str(k): freeze_json(v) for k, v in metrics.items()})
            if metrics
            else MappingProxyType({})
        )
        frozen_benchmarks: MappingProxyType[str, JsonValue] = (
            MappingProxyType({str(k): freeze_json(v) for k, v in benchmarks.items()})
            if benchmarks
            else MappingProxyType({})
        )
        return cls(
            experiment_id=experiment_id,
            timestamp=ts,
            metrics=frozen_metrics,
            benchmarks=frozen_benchmarks,
        )
