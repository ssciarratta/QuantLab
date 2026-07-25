"""Fake A3 backend para tests offline."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from quantlab.data.exchanges.a3.models import (
    A3AccountSummaryDTO,
    A3BookLevelDTO,
    A3InstrumentDTO,
    A3MarketSnapshotDTO,
    A3OrderAckDTO,
    A3PositionDTO,
    A3TradeDTO,
)


class FakeA3Backend:
    def __init__(self) -> None:
        self.connected = False
        self.orders: dict[str, A3OrderAckDTO] = {}
        self.placed: list[A3OrderAckDTO] = []
        now = datetime(2024, 6, 3, 15, 0, tzinfo=UTC)
        self._instruments = [
            A3InstrumentDTO(
                symbol="DLR/DIC24",
                description="Dolar Futuro DIC24",
                market="ROFX",
                segment="DDF",
                currency="USD",
                cfi_code="FXXXXX",
                tick_size=Decimal("0.001"),
                contract_multiplier=Decimal("1000"),
                lot_size=Decimal("1"),
                maturity="2024-12-01",
                underlying="USD",
                status="ACTIVE",
                raw={"symbol": "DLR/DIC24", "tickIncrement": "0.001", "minLotSize": "1"},
            )
        ]
        self._trades = [
            A3TradeDTO(
                symbol="DLR/DIC24",
                price=Decimal("1000.5"),
                size=Decimal("1"),
                timestamp=now,
                trade_id="t1",
                aggressor="buy",
                raw={"price": "1000.5", "size": "1", "datetime": now.isoformat()},
            ),
            A3TradeDTO(
                symbol="DLR/DIC24",
                price=Decimal("1001.0"),
                size=Decimal("2"),
                timestamp=now.replace(minute=0, second=30),
                trade_id="t2",
                aggressor="sell",
                raw={"price": "1001.0", "size": "2"},
            ),
            A3TradeDTO(
                symbol="DLR/DIC24",
                price=Decimal("1002.0"),
                size=Decimal("1"),
                timestamp=now.replace(minute=1, second=5),
                trade_id="t3",
                aggressor="buy",
                raw={"price": "1002.0", "size": "1"},
            ),
        ]

    def connect(self) -> None:
        self.connected = True

    def close(self) -> None:
        self.connected = False

    def health_check(self) -> dict[str, Any]:
        return {"ok": self.connected, "provider": "a3-fake"}

    def get_instruments(self) -> list[A3InstrumentDTO]:
        return list(self._instruments)

    def get_instrument_details(self, symbol: str) -> A3InstrumentDTO:
        for inst in self._instruments:
            if inst.symbol == symbol:
                return inst
        raise KeyError(symbol)

    def get_market_snapshot(self, symbol: str, depth: int = 5) -> A3MarketSnapshotDTO:
        return A3MarketSnapshotDTO(
            symbol=symbol,
            timestamp=datetime.now(tz=UTC),
            bids=(A3BookLevelDTO(price=Decimal("1000"), size=Decimal("5")),),
            offers=(A3BookLevelDTO(price=Decimal("1001"), size=Decimal("3")),),
            last_price=Decimal("1000.5"),
            last_size=Decimal("1"),
            open_interest=Decimal("100"),
            raw={"symbol": symbol, "depth": depth},
        )

    def get_historical_trades(
        self, symbol: str, start: datetime, end: datetime
    ) -> list[A3TradeDTO]:
        return [t for t in self._trades if t.symbol == symbol and start <= t.timestamp <= end]

    def place_order(
        self,
        *,
        symbol: str,
        side: str,
        size: str,
        order_type: str,
        price: str | None,
        client_order_id: str,
    ) -> A3OrderAckDTO:
        ack = A3OrderAckDTO(
            client_order_id=client_order_id,
            order_id=f"OID-{len(self.placed) + 1}",
            status="PENDING",
            symbol=symbol,
            raw={
                "side": side,
                "size": size,
                "order_type": order_type,
                "price": price,
            },
        )
        self.placed.append(ack)
        self.orders[ack.order_id or client_order_id] = ack
        return ack

    def cancel_order(self, order_id: str) -> A3OrderAckDTO:
        prev = self.orders.get(order_id)
        ack = A3OrderAckDTO(
            client_order_id=prev.client_order_id if prev else order_id,
            order_id=order_id,
            status="CANCELED",
            symbol=prev.symbol if prev else "",
            raw={"cancel": True},
        )
        self.orders[order_id] = ack
        return ack

    def get_order_status(self, order_id: str) -> A3OrderAckDTO:
        if order_id not in self.orders:
            raise KeyError(order_id)
        return self.orders[order_id]

    def get_orders(self) -> list[A3OrderAckDTO]:
        return list(self.orders.values())

    def get_account_summary(self) -> A3AccountSummaryDTO:
        return A3AccountSummaryDTO(
            account="SIM-001",
            currency="ARS",
            available=Decimal("100000"),
            raw={"account": "SIM-001"},
        )

    def get_positions(self) -> list[A3PositionDTO]:
        return [
            A3PositionDTO(
                symbol="DLR/DIC24",
                quantity=Decimal("0"),
                avg_price=None,
                raw={},
            )
        ]
