"""Fake A3 backend para tests offline (DLR + granos demo)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
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


def _inst(
    symbol: str,
    description: str,
    *,
    segment: str,
    underlying: str,
    maturity: str,
    multiplier: str = "1",
) -> A3InstrumentDTO:
    return A3InstrumentDTO(
        symbol=symbol,
        description=description,
        market="ROFX",
        segment=segment,
        currency="USD",
        cfi_code="FXXXXX",
        tick_size=Decimal("0.01"),
        contract_multiplier=Decimal(multiplier),
        lot_size=Decimal("1"),
        maturity=maturity,
        underlying=underlying,
        status="ACTIVE",
        raw={"symbol": symbol, "maturityDate": maturity},
    )


def _synth_trades(
    symbol: str,
    *,
    start: datetime,
    n: int,
    px0: Decimal,
    step_hours: int = 1,
) -> list[A3TradeDTO]:
    out: list[A3TradeDTO] = []
    px = px0
    for i in range(n):
        ts = start + timedelta(hours=i * step_hours)
        # camino suave + ruido mínimo determinista
        px = px + Decimal("0.05") * Decimal(str((i % 7) - 3))
        if px <= 0:
            px = px0
        out.append(
            A3TradeDTO(
                symbol=symbol,
                price=px,
                size=Decimal("1"),
                timestamp=ts,
                trade_id=f"{symbol}-{i}",
                aggressor="buy" if i % 2 == 0 else "sell",
                raw={"price": str(px), "size": "1", "datetime": ts.isoformat()},
            )
        )
    return out


class FakeA3Backend:
    def __init__(self) -> None:
        self.connected = False
        self.orders: dict[str, A3OrderAckDTO] = {}
        self.placed: list[A3OrderAckDTO] = []
        now = datetime.now(tz=UTC)
        self._instruments = [
            _inst(
                "DLR/DIC24",
                "Dolar Futuro DIC24",
                segment="DDF",
                underlying="USD",
                maturity="2024-12-01",
                multiplier="1000",
            ),
            _inst(
                "DLR/DIC25",
                "Dolar Futuro DIC25",
                segment="DDF",
                underlying="USD",
                maturity="2025-12-01",
                multiplier="1000",
            ),
            _inst(
                "SOJ/MAY26",
                "Soja Rosario MAY26",
                segment="DDA",
                underlying="SOY",
                maturity="2026-05-01",
            ),
            _inst(
                "SOJ/JUL26",
                "Soja Rosario JUL26",
                segment="DDA",
                underlying="SOY",
                maturity="2026-07-01",
            ),
            _inst(
                "MAI/JUL26",
                "Maíz Rosario JUL26",
                segment="DDA",
                underlying="CORN",
                maturity="2026-07-01",
            ),
            _inst(
                "MAI/DIC25",
                "Maíz Rosario DIC25",
                segment="DDA",
                underlying="CORN",
                maturity="2025-12-01",
            ),
            _inst(
                "TRI/DIC25",
                "Trigo Rosario DIC25",
                segment="DDA",
                underlying="WHEAT",
                maturity="2025-12-01",
            ),
            _inst(
                "TRI/MAR26",
                "Trigo Rosario MAR26",
                segment="DDA",
                underlying="WHEAT",
                maturity="2026-03-01",
            ),
        ]
        # Series demo densas (para armar velas 1h en sim compare = ancla «ahora»)
        # + bloque fijo 2024-06-03 para tests offline de DLR/DIC24
        start = now - timedelta(hours=120)
        self._trades: list[A3TradeDTO] = []
        fixed_start = datetime(2024, 6, 3, 14, 0, tzinfo=UTC)
        self._trades.extend(
            _synth_trades("DLR/DIC24", start=fixed_start, n=30, px0=Decimal("1000.5"))
        )
        self._trades.extend(
            _synth_trades("DLR/DIC24", start=start, n=120, px0=Decimal("1000.5"))
        )
        self._trades.extend(
            _synth_trades("DLR/DIC25", start=start, n=120, px0=Decimal("1050"))
        )
        self._trades.extend(
            _synth_trades("SOJ/MAY26", start=start, n=120, px0=Decimal("280"))
        )
        self._trades.extend(
            _synth_trades("SOJ/JUL26", start=start, n=120, px0=Decimal("275"))
        )
        self._trades.extend(
            _synth_trades("MAI/JUL26", start=start, n=120, px0=Decimal("160"))
        )
        self._trades.extend(
            _synth_trades("MAI/DIC25", start=start, n=120, px0=Decimal("155"))
        )
        self._trades.extend(
            _synth_trades("TRI/DIC25", start=start, n=120, px0=Decimal("210"))
        )
        self._trades.extend(
            _synth_trades("TRI/MAR26", start=start, n=120, px0=Decimal("215"))
        )

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
        last = next((t for t in reversed(self._trades) if t.symbol == symbol), None)
        px = last.price if last else Decimal("1000")
        return A3MarketSnapshotDTO(
            symbol=symbol,
            timestamp=datetime.now(tz=UTC),
            bids=(A3BookLevelDTO(price=px - Decimal("1"), size=Decimal("5")),),
            offers=(A3BookLevelDTO(price=px + Decimal("1"), size=Decimal("3")),),
            last_price=px,
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
        # Defensa en profundidad: Fake tampoco bypasea el live_gate research-prod.
        from quantlab.execution.live_gate import assert_live_routing_blocked

        assert_live_routing_blocked()
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
        from quantlab.execution.live_gate import assert_live_routing_blocked

        assert_live_routing_blocked()
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
