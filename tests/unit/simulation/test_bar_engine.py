"""Tests del motor de simulación Fase 4."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from quantlab.core.types.enums import IntentType, OrderSide, OrderType, TimeInForce
from quantlab.core.types.market import Bar
from quantlab.core.types.orders import OrderIntent
from quantlab.research.strategies.buy_once import BuyOnceStrategy
from quantlab.simulation import BarSimulationEngine, SimulationConfig
from quantlab.simulation.fill_model import ImmediateBarFillModel


def _bar(i: int, close: str, *, high: str | None = None, low: str | None = None) -> Bar:
    t0 = datetime(2024, 1, 1, tzinfo=UTC) + timedelta(minutes=i)
    c = Decimal(close)
    return Bar(
        instrument_id="a3:TEST",
        open=c,
        high=Decimal(high) if high else c + Decimal("1"),
        low=Decimal(low) if low else c - Decimal("1"),
        close=c,
        volume=Decimal("100"),
        timestamp_open=t0,
        timestamp_close=t0 + timedelta(minutes=1),
        timeframe="1m",
    )


def test_fill_limit_buy_touch() -> None:
    model = ImmediateBarFillModel()
    intent = OrderIntent(
        intent_id="i1",
        intent_type=IntentType.PLACE_ORDER,
        instrument_id="a3:TEST",
        side=OrderSide.BUY,
        quantity=Decimal("1"),
        price=Decimal("100"),
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.GTC,
    )
    bar = _bar(0, "101", high="102", low="99")
    d = model.evaluate(intent, bar)
    assert d.filled and d.price == Decimal("100")


def test_fill_limit_buy_no_touch() -> None:
    model = ImmediateBarFillModel()
    intent = OrderIntent(
        intent_id="i1",
        intent_type=IntentType.PLACE_ORDER,
        instrument_id="a3:TEST",
        side=OrderSide.BUY,
        quantity=Decimal("1"),
        price=Decimal("90"),
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.GTC,
    )
    bar = _bar(0, "101", high="102", low="99")
    assert not model.evaluate(intent, bar).filled


def test_engine_buy_once_produces_fill_and_equity() -> None:
    bars = [_bar(i, str(100 + i)) for i in range(5)]
    engine = BarSimulationEngine(
        SimulationConfig(experiment_id="exp-1", initial_cash=Decimal("10000"))
    )
    strategy = BuyOnceStrategy({"quantity": "2"})
    result = engine.run(strategy, bars)
    assert len(result.fills) == 1
    assert result.fills[0].quantity == Decimal("2")
    assert len(result.equity_curve) == 5
    assert result.equity_curve[0].equity > 0
    assert result.metadata["engine"] == "BarSimulationEngine"
