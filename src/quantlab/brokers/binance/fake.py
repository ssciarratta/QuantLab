"""Fake Binance broker — venue tester in-memory (multiplataforma)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from quantlab.brokers.mode import ModeGuard, OperatingMode
from quantlab.brokers.types import (
    BrokerAccount,
    BrokerAck,
    BrokerInstrument,
    BrokerPosition,
    BrokerSnapshot,
)
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import IntentType
from quantlab.core.types.orders import OrderIntent


class FakeBinanceBroker:
    """Venue fake in-memory ``venue_id=binance`` para probar el registry.

    Fills in-memory solo en TESTER (simula venue fake, no live).
    En PAPER usar ``PaperBroker`` envolviendo este port como MD.
    """

    def __init__(self, mode: OperatingMode = OperatingMode.TESTER) -> None:
        ModeGuard.validate_boot(mode)
        self._mode = mode
        self._connected = False
        self._seq = 0
        self._instruments = [
            BrokerInstrument(
                symbol="BTCUSDT",
                description="Bitcoin / Tether",
                currency="USDT",
                status="ACTIVE",
            ),
            BrokerInstrument(
                symbol="ETHUSDT",
                description="Ethereum / Tether",
                currency="USDT",
                status="ACTIVE",
            ),
        ]
        self._snapshots: dict[str, BrokerSnapshot] = {
            "BTCUSDT": BrokerSnapshot(
                symbol="BTCUSDT",
                bid=Decimal("60000.00"),
                ask=Decimal("60010.00"),
                last=Decimal("60005.00"),
                ts=datetime(2024, 6, 1, 12, 0, tzinfo=UTC),
            ),
            "ETHUSDT": BrokerSnapshot(
                symbol="ETHUSDT",
                bid=Decimal("3000.00"),
                ask=Decimal("3001.00"),
                last=Decimal("3000.50"),
                ts=datetime(2024, 6, 1, 12, 0, tzinfo=UTC),
            ),
        }
        self._account = BrokerAccount(
            cash=Decimal("100000"),
            currency="USDT",
            equity=Decimal("100000"),
        )
        self._positions: list[BrokerPosition] = []

    @property
    def venue_id(self) -> str:
        return "binance"

    @property
    def mode(self) -> OperatingMode:
        return self._mode

    def connect(self) -> dict[str, object]:
        self._connected = True
        return {"ok": True, "venue": self.venue_id, "mode": self._mode.value}

    def close(self) -> dict[str, object]:
        self._connected = False
        return {"ok": True, "venue": self.venue_id, "closed": True}

    def health(self) -> dict[str, object]:
        return {
            "ok": self._connected,
            "venue": self.venue_id,
            "mode": self._mode.value,
            "provider": "binance-fake",
        }

    def list_instruments(self) -> list[BrokerInstrument]:
        return list(self._instruments)

    def get_snapshot(self, symbol: str) -> BrokerSnapshot:
        sym = symbol.strip().upper()
        if sym in self._snapshots:
            return self._snapshots[sym]
        try:
            from datetime import UTC, datetime
            from decimal import Decimal

            from quantlab.brokers.binance.public_md import BinancePublicClient

            client = BinancePublicClient()
            ticker = client.book_ticker(sym)
            bid = ticker.bid if ticker.bid is not None else Decimal("0")
            ask = ticker.ask if ticker.ask is not None else Decimal("0")
            last = (bid + ask) / Decimal("2") if bid > 0 and ask > 0 else bid or ask
            snap = BrokerSnapshot(
                symbol=sym,
                bid=bid,
                ask=ask,
                last=last,
                ts=datetime.now(tz=UTC),
            )
            self._snapshots[sym] = snap
            if not any(i.symbol == sym for i in self._instruments):
                self._instruments.append(
                    BrokerInstrument(
                        symbol=sym,
                        description=f"{sym} (MD público)",
                        currency="USDT",
                        status="ACTIVE",
                    )
                )
            return snap
        except Exception as exc:
            raise ValidationError(f"símbolo sin MD paper: {sym} ({exc})") from exc

    def get_account(self) -> BrokerAccount:
        return self._account

    def get_positions(self) -> list[BrokerPosition]:
        return list(self._positions)

    def submit(self, intent: OrderIntent) -> BrokerAck:
        if self._mode is not OperatingMode.TESTER:
            raise ValidationError(
                "FakeBinanceBroker solo ejecuta fills en TESTER; usar PaperBroker para PAPER"
            )
        if intent.intent_type is IntentType.NO_ACTION:
            return BrokerAck(
                order_id="",
                client_order_id=intent.intent_id,
                status="NO_ACTION",
                message="no-op",
                venue=self.venue_id,
            )
        if intent.intent_type is IntentType.CANCEL_ORDER:
            return self.cancel(intent.replace_target_id or "")
        if intent.intent_type is not IntentType.PLACE_ORDER:
            raise ValidationError(f"intent no soportado: {intent.intent_type}")
        if intent.quantity is None or intent.side is None:
            raise ValidationError("PLACE_ORDER requiere side y quantity")
        snap = self.get_snapshot(intent.instrument_id)
        price = (snap.bid + snap.ask) / Decimal("2")
        self._seq += 1
        order_id = f"BN-{self._seq}-{uuid.uuid4().hex[:8]}"
        return BrokerAck(
            order_id=order_id,
            client_order_id=intent.intent_id,
            status="FILLED",
            message=f"fake binance fill @ {price}",
            venue=self.venue_id,
        )

    def cancel(self, order_id: str) -> BrokerAck:
        if self._mode is not OperatingMode.TESTER:
            raise ValidationError(
                "FakeBinanceBroker solo cancela en TESTER; usar PaperBroker para PAPER"
            )
        return BrokerAck(
            order_id=order_id,
            client_order_id=order_id,
            status="CANCELED",
            message="fake cancel",
            venue=self.venue_id,
        )
