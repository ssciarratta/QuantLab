"""DTOs externos A3 (capa de integración — no son dominio)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True, slots=True)
class A3InstrumentDTO:
    symbol: str
    description: str | None
    market: str | None
    segment: str | None
    currency: str | None
    cfi_code: str | None
    tick_size: Decimal | None
    contract_multiplier: Decimal | None
    lot_size: Decimal | None
    maturity: str | None
    underlying: str | None
    status: str | None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class A3TradeDTO:
    symbol: str
    price: Decimal
    size: Decimal
    timestamp: datetime
    trade_id: str | None
    aggressor: str | None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class A3BookLevelDTO:
    price: Decimal
    size: Decimal


@dataclass(frozen=True, slots=True)
class A3MarketSnapshotDTO:
    symbol: str
    timestamp: datetime
    bids: tuple[A3BookLevelDTO, ...]
    offers: tuple[A3BookLevelDTO, ...]
    last_price: Decimal | None
    last_size: Decimal | None
    open_interest: Decimal | None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class A3OrderAckDTO:
    client_order_id: str
    order_id: str | None
    status: str
    symbol: str
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class A3PositionDTO:
    symbol: str
    quantity: Decimal
    avg_price: Decimal | None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class A3AccountSummaryDTO:
    account: str
    currency: str | None
    available: Decimal | None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class A3WsEnvelope:
    message_type: str
    received_at: datetime
    payload: dict[str, Any]
