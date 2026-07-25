"""Cobertura extra: ImmediateBarFillModel (paths no cubiertos por test_bar_engine)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from quantlab.core.types.enums import IntentType, OrderSide, OrderType, TimeInForce
from quantlab.core.types.market import Bar
from quantlab.core.types.orders import OrderIntent
from quantlab.simulation.fill_model import ImmediateBarFillModel


def _bar(
    close: str = "100",
    *,
    high: str | None = None,
    low: str | None = None,
    instrument_id: str = "a3:TEST",
) -> Bar:
    t0 = datetime(2024, 1, 1, tzinfo=UTC)
    c = Decimal(close)
    return Bar(
        instrument_id=instrument_id,
        open=c,
        high=Decimal(high) if high else c + Decimal("1"),
        low=Decimal(low) if low else c - Decimal("1"),
        close=c,
        volume=Decimal("100"),
        timestamp_open=t0,
        timestamp_close=t0 + timedelta(minutes=1),
        timeframe="1m",
    )


def _place(
    *,
    side: OrderSide = OrderSide.BUY,
    order_type: OrderType = OrderType.LIMIT,
    quantity: Decimal = Decimal("1"),
    price: Decimal | None = Decimal("100"),
    instrument_id: str = "a3:TEST",
) -> OrderIntent:
    kwargs: dict[str, Any] = {
        "intent_id": "i1",
        "intent_type": IntentType.PLACE_ORDER,
        "instrument_id": instrument_id,
        "side": side,
        "quantity": quantity,
        "order_type": order_type,
    }
    if order_type is OrderType.LIMIT:
        kwargs["price"] = price
        kwargs["time_in_force"] = TimeInForce.GTC
    return OrderIntent(**kwargs)


def _raw_intent(**fields: Any) -> OrderIntent:
    """Bypass __post_init__ para forzar intents incompletos / tipos no soportados."""
    intent = object.__new__(OrderIntent)
    defaults: dict[str, Any] = {
        "intent_id": "raw",
        "intent_type": IntentType.PLACE_ORDER,
        "instrument_id": "a3:TEST",
        "side": OrderSide.BUY,
        "quantity": Decimal("1"),
        "price": None,
        "order_type": OrderType.LIMIT,
        "time_in_force": TimeInForce.GTC,
        "replace_target_id": None,
    }
    defaults.update(fields)
    for key, value in defaults.items():
        object.__setattr__(intent, key, value)
    return intent


def test_model_id_constant() -> None:
    assert ImmediateBarFillModel.model_id == "fill.immediate_bar.v1"


def test_not_place_no_action() -> None:
    model = ImmediateBarFillModel()
    intent = OrderIntent(
        intent_id="n1",
        intent_type=IntentType.NO_ACTION,
        instrument_id="a3:TEST",
    )
    d = model.evaluate(intent, _bar())
    assert not d.filled
    assert d.reason == "not_place"
    assert d.price is None and d.quantity is None


def test_not_place_cancel_order() -> None:
    model = ImmediateBarFillModel()
    intent = OrderIntent(
        intent_id="c1",
        intent_type=IntentType.CANCEL_ORDER,
        instrument_id="a3:TEST",
        replace_target_id="ord-1",
    )
    d = model.evaluate(intent, _bar())
    assert d.reason == "not_place"
    assert not d.filled


def test_incomplete_intent_missing_fields() -> None:
    model = ImmediateBarFillModel()
    for fields in (
        {"quantity": None},
        {"side": None},
        {"order_type": None},
    ):
        d = model.evaluate(_raw_intent(**fields), _bar())
        assert d.reason == "incomplete_intent"
        assert not d.filled


def test_market_fills_at_close() -> None:
    model = ImmediateBarFillModel()
    bar = _bar("101.5", high="103", low="100")
    d = model.evaluate(_place(order_type=OrderType.MARKET, price=None), bar)
    assert d.filled
    assert d.price == Decimal("101.5")
    assert d.quantity == Decimal("1")
    assert d.reason == "market_close"


def test_limit_without_price() -> None:
    model = ImmediateBarFillModel()
    d = model.evaluate(_raw_intent(price=None, order_type=OrderType.LIMIT), _bar())
    assert d.reason == "limit_without_price"
    assert not d.filled


def test_limit_sell_touch() -> None:
    model = ImmediateBarFillModel()
    intent = _place(side=OrderSide.SELL, price=Decimal("101"))
    bar = _bar("100", high="102", low="99")
    d = model.evaluate(intent, bar)
    assert d.filled
    assert d.price == Decimal("101")
    assert d.reason == "limit_sell_touch"


def test_limit_sell_not_touched() -> None:
    model = ImmediateBarFillModel()
    intent = _place(side=OrderSide.SELL, price=Decimal("105"))
    bar = _bar("100", high="102", low="99")
    d = model.evaluate(intent, bar)
    assert not d.filled
    assert d.reason == "limit_sell_not_touched"


def test_unsupported_order_type() -> None:
    model = ImmediateBarFillModel()
    d = model.evaluate(_raw_intent(order_type="stop"), _bar())  # type: ignore[arg-type]
    assert d.reason == "unsupported_order_type"
    assert not d.filled
