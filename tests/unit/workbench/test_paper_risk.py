"""Tests PaperRiskLimits fail-closed."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from quantlab.brokers.types import BrokerSnapshot
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import IntentType, OrderSide, OrderType
from quantlab.core.types.orders import OrderIntent
from quantlab.workbench.risk import PaperRiskLimits


def _snap(symbol: str = "BTCUSDT", mid: str = "100") -> BrokerSnapshot:
    px = Decimal(mid)
    return BrokerSnapshot(
        symbol=symbol,
        bid=px - Decimal("1"),
        ask=px + Decimal("1"),
        last=px,
        ts=datetime(2024, 1, 1, tzinfo=UTC),
    )


def _place(symbol: str = "BTCUSDT", qty: str = "1") -> OrderIntent:
    return OrderIntent(
        intent_id="r1",
        intent_type=IntentType.PLACE_ORDER,
        instrument_id=symbol,
        side=OrderSide.BUY,
        quantity=Decimal(qty),
        order_type=OrderType.MARKET,
    )


def test_risk_passes_within_limits() -> None:
    risk = PaperRiskLimits(max_qty=Decimal("10"), max_notional=Decimal("5000"))
    risk.check_intent(_place(qty="2"), _snap(mid="100"))


def test_risk_rejects_max_qty() -> None:
    risk = PaperRiskLimits(max_qty=Decimal("5"), max_notional=Decimal("1000000"))
    with pytest.raises(ValidationError, match="max_qty"):
        risk.check_intent(_place(qty="6"), _snap())


def test_risk_rejects_max_notional() -> None:
    risk = PaperRiskLimits(max_qty=Decimal("1000"), max_notional=Decimal("500"))
    with pytest.raises(ValidationError, match="max_notional"):
        risk.check_intent(_place(qty="10"), _snap(mid="100"))


def test_risk_rejects_symbol() -> None:
    risk = PaperRiskLimits(allowed_symbols=frozenset({"AAA"}))
    with pytest.raises(ValidationError, match="no permitido"):
        risk.check_intent(_place(symbol="BBB"), _snap(symbol="BBB"))
