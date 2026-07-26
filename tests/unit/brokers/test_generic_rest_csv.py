"""Generic CSV / REST MD brokers (Fase 24)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from quantlab.brokers.generic.csv_md import GenericCsvMdBroker
from quantlab.brokers.generic.rest_skeleton import FakeRestMdBroker
from quantlab.brokers.mode import OperatingMode
from quantlab.brokers.registry import get_default_registry, reset_default_registry
from quantlab.brokers.types import BrokerSnapshot
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import IntentType, OrderSide, OrderType
from quantlab.core.types.orders import OrderIntent
from quantlab.execution.live_gate import LIVE_BLOCKED


@pytest.fixture(autouse=True)
def _reset_reg() -> None:
    reset_default_registry()
    yield
    reset_default_registry()


def test_generic_csv_demo_rows() -> None:
    broker = GenericCsvMdBroker(mode=OperatingMode.TESTER)
    broker.connect()
    symbols = {i.symbol for i in broker.list_instruments()}
    assert "DEMO/AAA" in symbols
    snap = broker.get_snapshot("DEMO/AAA")
    assert snap.bid == Decimal("100.00")
    assert snap.ask == Decimal("100.50")
    h = broker.health()
    assert h["md_provider"] == "generic-csv"


def test_generic_csv_from_file(tmp_path: Path) -> None:
    path = tmp_path / "md.csv"
    path.write_text(
        "symbol,bid,ask,last\nFOO,1.0,1.1,1.05\nBAR,2.0,2.2,2.1\n",
        encoding="utf-8",
    )
    broker = GenericCsvMdBroker(csv_path=path, mode=OperatingMode.TESTER)
    assert {i.symbol for i in broker.list_instruments()} == {"FOO", "BAR"}
    assert broker.get_snapshot("FOO").last == Decimal("1.05")


def test_generic_csv_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="no encontrado"):
        GenericCsvMdBroker(csv_path=tmp_path / "missing.csv", mode=OperatingMode.TESTER)


def test_generic_csv_submit_cancel_blocked() -> None:
    assert LIVE_BLOCKED is True
    broker = GenericCsvMdBroker(mode=OperatingMode.TESTER)
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        broker.submit(
            OrderIntent(
                intent_id="c",
                intent_type=IntentType.PLACE_ORDER,
                instrument_id="DEMO/AAA",
                side=OrderSide.BUY,
                quantity=Decimal("1"),
                order_type=OrderType.MARKET,
            )
        )
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        broker.cancel("x")


def test_fake_rest_defaults() -> None:
    broker = FakeRestMdBroker(mode=OperatingMode.TESTER)
    broker.connect()
    symbols = {i.symbol for i in broker.list_instruments()}
    assert symbols == {"REST/FOO", "REST/BAR", "REST/BAZ"}
    assert broker.health()["md_provider"] == "generic-rest-fake"


def test_fake_rest_custom_snapshots() -> None:
    now = datetime.now(tz=UTC)
    snaps = {
        "X": BrokerSnapshot(
            symbol="X",
            bid=Decimal("1"),
            ask=Decimal("2"),
            last=Decimal("1.5"),
            ts=now,
        )
    }
    broker = FakeRestMdBroker(mode=OperatingMode.TESTER, snapshots=snaps)
    assert broker.get_snapshot("X").last == Decimal("1.5")
    with pytest.raises(ValidationError, match="desconocido"):
        broker.get_snapshot("NOPE")


def test_fake_rest_submit_cancel_blocked() -> None:
    broker = FakeRestMdBroker(mode=OperatingMode.PAPER)
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        broker.submit(
            OrderIntent(
                intent_id="r",
                intent_type=IntentType.PLACE_ORDER,
                instrument_id="REST/FOO",
                side=OrderSide.SELL,
                quantity=Decimal("1"),
                order_type=OrderType.MARKET,
            )
        )
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        broker.cancel("r1")


def test_registry_creates_generic_venues() -> None:
    reg = get_default_registry()
    assert "generic_csv" in reg.list_venues()
    assert "generic_rest" in reg.list_venues()
    csv_b = reg.create("generic_csv", OperatingMode.TESTER)
    assert csv_b.venue_id == "generic_csv"
    rest_b = reg.create("generic_rest", OperatingMode.TESTER)
    assert rest_b.venue_id == "generic_rest"
    # LIVE still blocked at registry
    with pytest.raises(ValidationError, match="LIVE_BLOCKED"):
        reg.create("generic_csv", OperatingMode.LIVE)
