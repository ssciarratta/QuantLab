"""DTOs neutrales del broker plane (no venue-specific)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class BrokerInstrument:
    symbol: str
    description: str
    currency: str
    status: str


@dataclass(frozen=True, slots=True)
class BrokerSnapshot:
    symbol: str
    bid: Decimal
    ask: Decimal
    last: Decimal
    ts: datetime


@dataclass(frozen=True, slots=True)
class BrokerAccount:
    cash: Decimal
    currency: str
    equity: Decimal | None = None


@dataclass(frozen=True, slots=True)
class BrokerPosition:
    symbol: str
    quantity: Decimal
    avg_price: Decimal | None = None


@dataclass(frozen=True, slots=True)
class BrokerAck:
    order_id: str
    client_order_id: str
    status: str
    message: str = ""
    venue: str = ""


@dataclass(frozen=True, slots=True)
class PaperFill:
    fill_id: str
    order_id: str
    symbol: str
    side: str
    quantity: Decimal
    price: Decimal
    ts: datetime
    source: str = "paper_broker"
