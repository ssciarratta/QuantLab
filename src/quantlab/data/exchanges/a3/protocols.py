"""Protocolo del backend A3 (permite fakes sin pyRofex en tests)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from quantlab.data.exchanges.a3.models import (
    A3AccountSummaryDTO,
    A3InstrumentDTO,
    A3MarketSnapshotDTO,
    A3OrderAckDTO,
    A3PositionDTO,
    A3TradeDTO,
)


class A3Backend(Protocol):
    def connect(self) -> None: ...

    def close(self) -> None: ...

    def health_check(self) -> dict[str, Any]: ...

    def get_instruments(self) -> list[A3InstrumentDTO]: ...

    def get_instrument_details(self, symbol: str) -> A3InstrumentDTO: ...

    def get_market_snapshot(self, symbol: str, depth: int = 5) -> A3MarketSnapshotDTO: ...

    def get_historical_trades(
        self, symbol: str, start: datetime, end: datetime
    ) -> list[A3TradeDTO]: ...

    def place_order(
        self,
        *,
        symbol: str,
        side: str,
        size: str,
        order_type: str,
        price: str | None,
        client_order_id: str,
    ) -> A3OrderAckDTO: ...

    def cancel_order(self, order_id: str) -> A3OrderAckDTO: ...

    def get_order_status(self, order_id: str) -> A3OrderAckDTO: ...

    def get_orders(self) -> list[A3OrderAckDTO]: ...

    def get_account_summary(self) -> A3AccountSummaryDTO: ...

    def get_positions(self) -> list[A3PositionDTO]: ...
