"""Enumeraciones compartidas del dominio QuantLab."""

from enum import StrEnum


class InstrumentStatus(StrEnum):
    ACTIVE = "active"
    DELISTED = "delisted"


class EventType(StrEnum):
    BAR = "bar"
    TRADE = "trade"
    ORDER_BOOK_SNAPSHOT = "order_book_snapshot"
    ORDER_BOOK_DELTA = "order_book_delta"
    TIMER = "timer"
    ORDER_ACCEPTED = "order_accepted"
    ORDER_REJECTED = "order_rejected"
    PARTIAL_FILL = "partial_fill"
    FULL_FILL = "full_fill"
    CANCELED = "canceled"
    EXPIRED = "expired"
    BALANCE_UPDATE = "balance_update"
    POSITION_UPDATE = "position_update"


class IntentType(StrEnum):
    PLACE_ORDER = "place_order"
    CANCEL_ORDER = "cancel_order"
    REPLACE_ORDER = "replace_order"
    NO_ACTION = "no_action"


class OrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    LIMIT = "limit"
    MARKET = "market"


class TimeInForce(StrEnum):
    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"


class OrderStatus(StrEnum):
    PENDING = "pending"
    OPEN = "open"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class LiquidityType(StrEnum):
    MAKER = "maker"
    TAKER = "taker"


class FeeType(StrEnum):
    MAKER = "maker"
    TAKER = "taker"
    FUNDING = "funding"
    OTHER = "other"


class ClockMode(StrEnum):
    EVENT_DRIVEN = "event_driven"
    STEP = "step"


class ClockSpeed(StrEnum):
    REALTIME = "realtime"
    ACCELERATED = "accelerated"


class ExperimentStatus(StrEnum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    APPROVED = "approved"
    REJECTED = "rejected"


class BookSide(StrEnum):
    BID = "bid"
    ASK = "ask"


class BookChangeAction(StrEnum):
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"
