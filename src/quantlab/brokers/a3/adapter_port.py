"""A3BrokerPort — MD/cuenta vía FakeA3Backend; execution plane fail-closed."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from quantlab.brokers.mode import ModeGuard, OperatingMode
from quantlab.brokers.types import (
    BrokerAccount,
    BrokerAck,
    BrokerInstrument,
    BrokerPosition,
    BrokerSnapshot,
)
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.orders import OrderIntent
from quantlab.data.exchanges.a3.fake_backend import FakeA3Backend
from quantlab.execution.live_gate import assert_live_routing_blocked


class A3BrokerPort:
    """Puerto A3 orientado a market data / account read.

    ``submit`` / ``cancel`` SIEMPRE llaman ``assert_live_routing_blocked()``
    (incluso en PAPER). Para fills PAPER usar ``PaperBroker`` envolviendo este port.
    """

    def __init__(
        self,
        backend: FakeA3Backend | None = None,
        mode: OperatingMode = OperatingMode.TESTER,
    ) -> None:
        ModeGuard.validate_boot(mode)
        self._backend: FakeA3Backend = backend if backend is not None else FakeA3Backend()
        self._mode = mode

    @property
    def venue_id(self) -> str:
        return "a3"

    @property
    def mode(self) -> OperatingMode:
        return self._mode

    def connect(self) -> dict[str, object]:
        self._backend.connect()
        return {"ok": True, "venue": self.venue_id, "mode": self._mode.value}

    def close(self) -> dict[str, object]:
        self._backend.close()
        return {"ok": True, "venue": self.venue_id, "closed": True}

    def health(self) -> dict[str, object]:
        raw: dict[str, Any] = dict(self._backend.health_check())
        raw["venue"] = self.venue_id
        raw["mode"] = self._mode.value
        raw["md_only"] = True
        return raw

    def list_instruments(self) -> list[BrokerInstrument]:
        out: list[BrokerInstrument] = []
        for inst in self._backend.get_instruments():
            out.append(
                BrokerInstrument(
                    symbol=inst.symbol,
                    description=inst.description or "",
                    currency=inst.currency or "",
                    status=inst.status or "UNKNOWN",
                )
            )
        return out

    def get_snapshot(self, symbol: str) -> BrokerSnapshot:
        snap = self._backend.get_market_snapshot(symbol)
        bid = snap.bids[0].price if snap.bids else Decimal("0")
        ask = snap.offers[0].price if snap.offers else Decimal("0")
        last = snap.last_price if snap.last_price is not None else Decimal("0")
        return BrokerSnapshot(
            symbol=snap.symbol,
            bid=bid,
            ask=ask,
            last=last,
            ts=snap.timestamp,
        )

    def get_account(self) -> BrokerAccount:
        acct = self._backend.get_account_summary()
        cash = acct.available if acct.available is not None else Decimal("0")
        return BrokerAccount(
            cash=cash,
            currency=acct.currency or "",
            equity=None,
        )

    def get_positions(self) -> list[BrokerPosition]:
        return [
            BrokerPosition(
                symbol=p.symbol,
                quantity=p.quantity,
                avg_price=p.avg_price,
            )
            for p in self._backend.get_positions()
        ]

    def submit(self, intent: OrderIntent) -> BrokerAck:
        # MD-only execution plane: siempre fail-closed (PAPER → PaperBroker).
        assert_live_routing_blocked()
        raise ValidationError("A3BrokerPort is MD-only; use PaperBroker for PAPER fills")

    def cancel(self, order_id: str) -> BrokerAck:
        assert_live_routing_blocked()
        raise ValidationError("A3BrokerPort is MD-only; use PaperBroker for PAPER cancels")
