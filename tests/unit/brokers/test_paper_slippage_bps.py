"""Tests paper slippage_bps adverso (F25)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from quantlab.brokers.paper.broker import PaperBroker, apply_paper_slippage
from quantlab.brokers.types import (
    BrokerAccount,
    BrokerAck,
    BrokerInstrument,
    BrokerPosition,
    BrokerSnapshot,
)
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import IntentType, OrderSide, OrderType
from quantlab.core.types.orders import OrderIntent


class _MidMd:
    def __init__(self, bid: str = "100", ask: str = "102") -> None:
        self._snap = BrokerSnapshot(
            symbol="TEST",
            bid=Decimal(bid),
            ask=Decimal(ask),
            last=Decimal("101"),
            ts=datetime(2024, 1, 1, tzinfo=UTC),
        )

    @property
    def venue_id(self) -> str:
        return "md"

    def connect(self) -> dict[str, object]:
        return {"ok": True}

    def close(self) -> dict[str, object]:
        return {"ok": True}

    def health(self) -> dict[str, object]:
        return {"ok": True}

    def list_instruments(self) -> list[BrokerInstrument]:
        return []

    def get_snapshot(self, symbol: str) -> BrokerSnapshot:
        return self._snap

    def get_account(self) -> BrokerAccount:
        return BrokerAccount(cash=Decimal("0"), currency="USD")

    def get_positions(self) -> list[BrokerPosition]:
        return []

    def submit(self, intent: OrderIntent) -> BrokerAck:
        raise AssertionError("md submit")

    def cancel(self, order_id: str) -> BrokerAck:
        raise AssertionError("md cancel")


def _place(side: OrderSide = OrderSide.BUY) -> OrderIntent:
    return OrderIntent(
        intent_id="s1",
        intent_type=IntentType.PLACE_ORDER,
        instrument_id="TEST",
        side=side,
        quantity=Decimal("1"),
        order_type=OrderType.MARKET,
    )


def test_apply_slippage_zero_is_identity() -> None:
    assert apply_paper_slippage(Decimal("101"), "BUY", Decimal("0")) == Decimal("101")
    assert apply_paper_slippage(Decimal("101"), "SELL", Decimal("0")) == Decimal("101")


def test_apply_slippage_adverse_buy_sell() -> None:
    mid = Decimal("100")
    # 100 bps = 1%
    buy = apply_paper_slippage(mid, "BUY", Decimal("100"))
    sell = apply_paper_slippage(mid, "SELL", Decimal("100"))
    assert buy == Decimal("101")
    assert sell == Decimal("99")


def test_paper_broker_default_fill_at_mid() -> None:
    # bid=100 ask=102 → mid=101
    broker = PaperBroker(_MidMd(), slippage_bps=Decimal("0"))
    ack = broker.submit(_place(OrderSide.BUY))
    assert ack.status == "FILLED"
    fills_msg = ack.message
    assert "101" in fills_msg
    pos = broker.get_positions()
    assert len(pos) == 1
    assert pos[0].avg_price == Decimal("101")


def test_paper_broker_buy_worse_with_slip() -> None:
    broker = PaperBroker(_MidMd(), slippage_bps=Decimal("100"))  # 1%
    broker.submit(_place(OrderSide.BUY))
    # mid 101 * 1.01 = 102.01
    assert broker.get_positions()[0].avg_price == Decimal("101") * Decimal("1.01")


def test_paper_broker_sell_worse_with_slip() -> None:
    md = _MidMd()
    broker = PaperBroker(md, slippage_bps=Decimal("0"), initial_cash=Decimal("100000"))
    # seed long at mid
    broker.submit(_place(OrderSide.BUY))
    broker2 = PaperBroker(
        md,
        book=broker.book,
        slippage_bps=Decimal("100"),
    )
    broker2.submit(_place(OrderSide.SELL))
    # after sell qty 0; cash should reflect worse sell (mid * 0.99)
    # buy @ 101, sell @ 101 * 0.99 = 99.99 → loss of 1.01
    cash = broker2.book.cash
    expected = Decimal("100000") - Decimal("101") + (Decimal("101") * Decimal("0.99"))
    assert cash == expected


def test_paper_broker_rejects_negative_slippage() -> None:
    with pytest.raises(ValidationError, match="slippage_bps"):
        PaperBroker(_MidMd(), slippage_bps=Decimal("-1"))
