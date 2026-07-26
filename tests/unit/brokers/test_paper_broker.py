"""Tests PaperBroker — fills locales, sin envío al venue MD."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from quantlab.brokers.a3.adapter_port import A3BrokerPort
from quantlab.brokers.paper.broker import PaperBroker
from quantlab.brokers.paper.journal import PaperFillJournal
from quantlab.brokers.types import (
    BrokerAccount,
    BrokerAck,
    BrokerInstrument,
    BrokerPosition,
    BrokerSnapshot,
)
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import IntentType, OrderSide, OrderType, TimeInForce
from quantlab.core.types.orders import OrderIntent
from quantlab.data.exchanges.a3.fake_backend import FakeA3Backend


class _RecordingMd:
    """MD stub que registra si alguien intenta submit/cancel venue."""

    def __init__(self) -> None:
        self.submit_calls = 0
        self.cancel_calls = 0
        self._snap = BrokerSnapshot(
            symbol="TEST",
            bid=Decimal("10"),
            ask=Decimal("12"),
            last=Decimal("11"),
            ts=datetime(2024, 1, 1, tzinfo=UTC),
        )

    @property
    def venue_id(self) -> str:
        return "fake-live-looking"

    def connect(self) -> dict[str, object]:
        return {"ok": True}

    def close(self) -> dict[str, object]:
        return {"ok": True}

    def health(self) -> dict[str, object]:
        return {"ok": True}

    def list_instruments(self) -> list[BrokerInstrument]:
        return [
            BrokerInstrument(
                symbol="TEST",
                description="t",
                currency="USD",
                status="ACTIVE",
            )
        ]

    def get_snapshot(self, symbol: str) -> BrokerSnapshot:
        return self._snap

    def get_account(self) -> BrokerAccount:
        return BrokerAccount(cash=Decimal("1"), currency="USD")

    def get_positions(self) -> list[BrokerPosition]:
        return []

    def submit(self, intent: OrderIntent) -> BrokerAck:
        self.submit_calls += 1
        raise AssertionError("PaperBroker must never call md_port.submit")

    def cancel(self, order_id: str) -> BrokerAck:
        self.cancel_calls += 1
        raise AssertionError("PaperBroker must never call md_port.cancel")


def _place(symbol: str = "TEST") -> OrderIntent:
    return OrderIntent(
        intent_id="i1",
        intent_type=IntentType.PLACE_ORDER,
        instrument_id=symbol,
        side=OrderSide.BUY,
        quantity=Decimal("2"),
        order_type=OrderType.MARKET,
    )


def test_paper_broker_fills_at_mid_never_calls_venue(tmp_path: Path) -> None:
    md = _RecordingMd()
    journal = PaperFillJournal(tmp_path / "fills.jsonl")
    broker = PaperBroker(md, journal=journal)
    assert broker.venue_id == "paper"

    ack = broker.submit(_place())
    assert ack.status == "FILLED"
    assert ack.venue == "paper"
    assert md.submit_calls == 0
    assert md.cancel_calls == 0

    fills = journal.list_fills()
    assert len(fills) == 1
    assert fills[0].price == Decimal("11")  # mid of 10/12
    assert fills[0].source == "paper_broker"
    assert fills[0].quantity == Decimal("2")


def test_paper_broker_no_action_and_cancel() -> None:
    md = _RecordingMd()
    broker = PaperBroker(md)
    noop = broker.submit(
        OrderIntent(
            intent_id="n1",
            intent_type=IntentType.NO_ACTION,
            instrument_id="TEST",
        )
    )
    assert noop.status == "NO_ACTION"

    cancel_ack = broker.submit(
        OrderIntent(
            intent_id="c1",
            intent_type=IntentType.CANCEL_ORDER,
            instrument_id="TEST",
            replace_target_id="missing",
        )
    )
    assert cancel_ack.status == "REJECTED"
    assert md.submit_calls == 0
    assert md.cancel_calls == 0


def test_paper_over_a3_does_not_hit_backend_place(tmp_path: Path) -> None:
    backend = FakeA3Backend()
    md = A3BrokerPort(backend=backend)
    md.connect()
    broker = PaperBroker(md, journal=PaperFillJournal(tmp_path / "j.jsonl"))
    ack = broker.submit(
        OrderIntent(
            intent_id="a3p",
            intent_type=IntentType.PLACE_ORDER,
            instrument_id="DLR/DIC24",
            side=OrderSide.BUY,
            quantity=Decimal("1"),
            price=Decimal("1000"),
            order_type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
        )
    )
    assert ack.status == "FILLED"
    assert backend.placed == []


def test_paper_delegates_md_reads() -> None:
    md = A3BrokerPort()
    md.connect()
    broker = PaperBroker(md)
    inst = broker.list_instruments()
    assert inst
    snap = broker.get_snapshot(inst[0].symbol)
    assert snap.bid > 0
    acct = broker.get_account()
    assert acct.cash > 0
    assert isinstance(broker.get_positions(), list)
    assert broker.health()["paper_broker"] is True


def test_a3_port_submit_still_blocked() -> None:
    port = A3BrokerPort()
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        port.submit(_place("DLR/DIC24"))
