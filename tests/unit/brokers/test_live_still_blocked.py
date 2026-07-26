"""Invariante: LIVE sigue bloqueado tras Fase 19."""

from __future__ import annotations

from decimal import Decimal

import pytest

from quantlab.brokers import ModeGuard, OperatingMode, get_default_registry
from quantlab.brokers.a3 import A3BrokerPort
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import IntentType, OrderSide, OrderType
from quantlab.core.types.orders import OrderIntent
from quantlab.execution.live_gate import LIVE_BLOCKED, assert_live_routing_blocked


def test_live_blocked_constant_true() -> None:
    assert LIVE_BLOCKED is True


def test_assert_live_routing_still_raises() -> None:
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        assert_live_routing_blocked()


def test_mode_guard_live_blocked() -> None:
    with pytest.raises(ValidationError, match="LIVE"):
        ModeGuard.validate_boot(OperatingMode.LIVE)


def test_registry_cannot_boot_live() -> None:
    with pytest.raises(ValidationError, match="LIVE_BLOCKED"):
        get_default_registry().create("binance", OperatingMode.LIVE)


def test_a3_broker_port_submit_cancel_fail_closed() -> None:
    port = A3BrokerPort(mode=OperatingMode.TESTER)
    intent = OrderIntent(
        intent_id="live-try",
        intent_type=IntentType.PLACE_ORDER,
        instrument_id="DLR/DIC24",
        side=OrderSide.BUY,
        quantity=Decimal("1"),
        order_type=OrderType.MARKET,
    )
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        port.submit(intent)
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        port.cancel("OID-1")


def test_a3_paper_mode_still_blocks_direct_submit() -> None:
    """PAPER no habilita submit en A3BrokerPort — solo PaperBroker."""
    port = A3BrokerPort(mode=OperatingMode.PAPER)
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        port.submit(
            OrderIntent(
                intent_id="p",
                intent_type=IntentType.PLACE_ORDER,
                instrument_id="DLR/DIC24",
                side=OrderSide.SELL,
                quantity=Decimal("1"),
                order_type=OrderType.MARKET,
            )
        )


def test_generic_venues_submit_still_blocked() -> None:
    for venue in ("generic_csv", "generic_rest"):
        broker = get_default_registry().create(venue, OperatingMode.TESTER)
        with pytest.raises(ValidationError, match="BLOQUEADO"):
            broker.submit(
                OrderIntent(
                    intent_id="g",
                    intent_type=IntentType.PLACE_ORDER,
                    instrument_id="X",
                    side=OrderSide.BUY,
                    quantity=Decimal("1"),
                    order_type=OrderType.MARKET,
                )
            )
        with pytest.raises(ValidationError, match="BLOQUEADO"):
            broker.cancel("OID")


def test_registry_rejects_live_for_generic() -> None:
    with pytest.raises(ValidationError, match="LIVE_BLOCKED"):
        get_default_registry().create("generic_rest", OperatingMode.LIVE)
