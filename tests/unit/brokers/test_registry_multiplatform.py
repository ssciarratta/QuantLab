"""Registry multiplataforma: a3 + binance + paper."""

from __future__ import annotations

from decimal import Decimal

import pytest

from quantlab.brokers import (
    BrokerRegistry,
    OperatingMode,
    PaperBroker,
    get_default_registry,
    resolve_mode,
)
from quantlab.brokers.a3 import A3BrokerPort
from quantlab.brokers.binance import FakeBinanceBroker
from quantlab.brokers.registry import register_builtin_brokers
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import IntentType, OrderSide, OrderType
from quantlab.core.types.orders import OrderIntent


def test_default_registry_has_builtin_venues() -> None:
    reg = get_default_registry()
    venues = reg.list_venues()
    assert "a3" in venues
    assert "binance" in venues
    assert "paper" in venues


def test_create_a3_tester() -> None:
    broker = get_default_registry().create("a3", OperatingMode.TESTER)
    assert isinstance(broker, A3BrokerPort)
    assert broker.venue_id == "a3"
    broker.connect()
    symbols = [i.symbol for i in broker.list_instruments()]
    assert "DLR/DIC24" in symbols


def test_create_a3_paper_wraps_paper_broker() -> None:
    broker = get_default_registry().create("a3", OperatingMode.PAPER)
    assert isinstance(broker, PaperBroker)
    assert broker.venue_id == "paper"


def test_create_binance_tester_fills() -> None:
    broker = get_default_registry().create("binance", OperatingMode.TESTER)
    assert isinstance(broker, FakeBinanceBroker)
    broker.connect()
    symbols = {i.symbol for i in broker.list_instruments()}
    assert symbols == {"BTCUSDT", "ETHUSDT"}
    ack = broker.submit(
        OrderIntent(
            intent_id="b1",
            intent_type=IntentType.PLACE_ORDER,
            instrument_id="BTCUSDT",
            side=OrderSide.BUY,
            quantity=Decimal("0.01"),
            order_type=OrderType.MARKET,
        )
    )
    assert ack.status == "FILLED"
    assert ack.venue == "binance"


def test_create_binance_paper_wraps() -> None:
    broker = get_default_registry().create("binance", OperatingMode.PAPER)
    assert isinstance(broker, PaperBroker)
    snap = broker.get_snapshot("ETHUSDT")
    assert snap.last == Decimal("3000.50")


def test_create_rejects_live() -> None:
    with pytest.raises(ValidationError, match="LIVE_BLOCKED"):
        get_default_registry().create("a3", OperatingMode.LIVE)


def test_create_unknown_venue() -> None:
    reg = register_builtin_brokers(BrokerRegistry())
    with pytest.raises(ValidationError, match="venue desconocido"):
        reg.create("ibkr", OperatingMode.TESTER)


def test_resolve_real_uses_paper_factory_path() -> None:
    mode = resolve_mode("real")
    assert mode is OperatingMode.PAPER
    broker = get_default_registry().create("paper", mode)
    assert isinstance(broker, PaperBroker)
