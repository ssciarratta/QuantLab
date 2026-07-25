"""Tests unitarios de InventoryMMStrategy (sin backtester)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from quantlab.core.contracts.strategy import StrategyContext
from quantlab.core.types.enums import (
    ClockMode,
    ClockSpeed,
    EventType,
    IntentType,
    OrderSide,
)
from quantlab.core.types.market import MarketEvent
from quantlab.core.types.portfolio import SimulationClock
from quantlab.research.strategies.inventory_mm import InventoryMMStrategy


def _ctx(**params: Any) -> StrategyContext:
    return StrategyContext(
        clock=SimulationClock(
            current_time=datetime(2024, 6, 1, tzinfo=UTC),
            mode=ClockMode.EVENT_DRIVEN,
            speed=ClockSpeed.ACCELERATED,
        ),
        parameters=params,
    )


def _event(instrument_id: str = "MM:TEST") -> MarketEvent:
    return MarketEvent(
        event_id="e1",
        event_type=EventType.ORDER_BOOK_SNAPSHOT,
        timestamp=datetime(2024, 6, 1, tzinfo=UTC),
        instrument_id=instrument_id,
    )


def test_noop_without_book() -> None:
    strat = InventoryMMStrategy({"quantity": "1", "half_spread": "0.5"})
    intents = strat.on_event(_event(), _ctx())
    assert len(intents) == 1
    assert intents[0].intent_type is IntentType.NO_ACTION
    assert intents[0].intent_id == "mm-noop"


def test_skew_inventory_lowers_quotes_when_long() -> None:
    strat = InventoryMMStrategy({"quantity": "1", "half_spread": "0.5", "max_pos": "10"})
    # mid=100; skew=1 → bid=99, ask=100
    intents = strat.on_event(
        _event(),
        _ctx(best_bid="99", best_ask="101", inventory_skew="1", inventory="2"),
    )
    places = [i for i in intents if i.intent_type is IntentType.PLACE_ORDER]
    bid = next(i for i in places if i.side is OrderSide.BUY)
    ask = next(i for i in places if i.side is OrderSide.SELL)
    assert bid.price == Decimal("99")
    assert ask.price == Decimal("100")


def test_skew_inventory_raises_quotes_when_short() -> None:
    strat = InventoryMMStrategy({"quantity": "1", "half_spread": "0.5", "max_pos": "10"})
    # mid=100; skew=-1 → bid=100, ask=101
    intents = strat.on_event(
        _event(),
        _ctx(best_bid="99", best_ask="101", inventory_skew="-1", inventory="2"),
    )
    places = [i for i in intents if i.intent_type is IntentType.PLACE_ORDER]
    bid = next(i for i in places if i.side is OrderSide.BUY)
    ask = next(i for i in places if i.side is OrderSide.SELL)
    assert bid.price == Decimal("100")
    assert ask.price == Decimal("101")


def test_max_pos_suppresses_bid() -> None:
    strat = InventoryMMStrategy({"quantity": "1", "half_spread": "0.5", "max_pos": "5"})
    intents = strat.on_event(
        _event(),
        _ctx(best_bid="99", best_ask="101", inventory="5"),
    )
    places = [i for i in intents if i.intent_type is IntentType.PLACE_ORDER]
    assert all(i.side is OrderSide.SELL for i in places)
    assert len(places) == 1
    assert places[0].intent_id == "mm-ask-1"
    assert places[0].quantity == Decimal("1")


def test_zero_inventory_bid_only() -> None:
    strat = InventoryMMStrategy({"quantity": "2", "half_spread": "0.5", "max_pos": "10"})
    intents = strat.on_event(
        _event(),
        _ctx(best_bid="99", best_ask="101", inventory="0"),
    )
    places = [i for i in intents if i.intent_type is IntentType.PLACE_ORDER]
    assert len(places) == 1
    assert places[0].side is OrderSide.BUY
    assert places[0].intent_id == "mm-bid-1"
    assert places[0].quantity == Decimal("2")


def test_cancel_previous_quotes_on_requote() -> None:
    strat = InventoryMMStrategy({"quantity": "1", "half_spread": "0.5", "max_pos": "10"})
    book = dict(best_bid="99", best_ask="101", inventory="3")
    first = strat.on_event(_event(), _ctx(**book))
    place_ids = [i.intent_id for i in first if i.intent_type is IntentType.PLACE_ORDER]
    assert place_ids == ["mm-bid-1", "mm-ask-1"]
    assert strat.get_state()["quotes"] == place_ids

    second = strat.on_event(_event(), _ctx(**book))
    cancels = [i for i in second if i.intent_type is IntentType.CANCEL_ORDER]
    assert len(cancels) == 2
    assert {c.replace_target_id for c in cancels} == set(place_ids)
    assert {c.intent_id for c in cancels} == {f"cancel-{qid}" for qid in place_ids}
    places = [i for i in second if i.intent_type is IntentType.PLACE_ORDER]
    assert [p.intent_id for p in places] == ["mm-bid-2", "mm-ask-2"]
    assert strat.get_state()["quotes"] == ["mm-bid-2", "mm-ask-2"]
