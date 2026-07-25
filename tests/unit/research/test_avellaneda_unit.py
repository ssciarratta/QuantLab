"""Tests unitarios de AvellanedaStoikovStrategy / quote_prices (sin backtester)."""

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
from quantlab.research.strategies.avellaneda_stoikov import (
    AvellanedaStoikovStrategy,
    quote_prices,
)


def _ctx(**params: Any) -> StrategyContext:
    return StrategyContext(
        clock=SimulationClock(
            current_time=datetime(2024, 6, 1, tzinfo=UTC),
            mode=ClockMode.EVENT_DRIVEN,
            speed=ClockSpeed.ACCELERATED,
        ),
        parameters=params,
    )


def _event(instrument_id: str = "AS:TEST") -> MarketEvent:
    return MarketEvent(
        event_id="e1",
        event_type=EventType.ORDER_BOOK_SNAPSHOT,
        timestamp=datetime(2024, 6, 1, tzinfo=UTC),
        instrument_id=instrument_id,
    )


def test_noop_without_book() -> None:
    strat = AvellanedaStoikovStrategy({"quantity": "1"})
    intents = strat.on_event(_event(), _ctx())
    assert len(intents) == 1
    assert intents[0].intent_type is IntentType.NO_ACTION
    assert intents[0].intent_id == "as-noop-book"


def test_noop_invalid_params_gamma() -> None:
    strat = AvellanedaStoikovStrategy({"gamma": 0, "quantity": "1"})
    intents = strat.on_event(
        _event(),
        _ctx(best_bid="99", best_ask="101", inventory="0"),
    )
    assert intents[0].intent_type is IntentType.NO_ACTION
    assert intents[0].intent_id == "as-noop-params"


def test_noop_invalid_params_kappa_and_horizon() -> None:
    for bad in ({"kappa": 0}, {"horizon_events": 0}, {"sigma": -0.01}):
        strat = AvellanedaStoikovStrategy({"quantity": "1", **bad})
        intents = strat.on_event(
            _event(),
            _ctx(best_bid="99", best_ask="101", inventory="0"),
        )
        assert intents[0].intent_id == "as-noop-params"


def test_quote_prices_inventory_lowers_when_long() -> None:
    mid = 100.0
    r0, bid0, ask0 = quote_prices(mid=mid, inventory=0.0, tau=1.0)
    r_long, bid_long, ask_long = quote_prices(mid=mid, inventory=5.0, tau=1.0)
    assert r_long < r0
    assert bid_long < bid0
    assert ask_long < ask0
    assert ask0 > bid0
    assert isinstance(bid0, Decimal)


def test_strategy_quotes_with_inventory() -> None:
    strat = AvellanedaStoikovStrategy(
        {"quantity": "1", "gamma": 0.1, "sigma": 0.02, "kappa": 1.5, "max_pos": "10"}
    )
    intents = strat.on_event(
        _event(),
        _ctx(best_bid="99", best_ask="101", inventory="2"),
    )
    places = [i for i in intents if i.intent_type is IntentType.PLACE_ORDER]
    assert len(places) == 2
    bid = next(i for i in places if i.side is OrderSide.BUY)
    ask = next(i for i in places if i.side is OrderSide.SELL)
    assert bid.price is not None and ask.price is not None
    assert ask.price > bid.price
    # Inventario largo → reservation bajo mid (100) → quotes más bajos
    r, expected_bid, expected_ask = quote_prices(
        mid=100.0, inventory=2.0, gamma=0.1, sigma=0.02, kappa=1.5, tau=0.99
    )
    assert r < Decimal("100")
    assert bid.price == expected_bid
    assert ask.price == expected_ask


def test_zero_inventory_bid_only() -> None:
    strat = AvellanedaStoikovStrategy({"quantity": "1", "max_pos": "10"})
    intents = strat.on_event(
        _event(),
        _ctx(best_bid="99", best_ask="101", inventory="0"),
    )
    places = [i for i in intents if i.intent_type is IntentType.PLACE_ORDER]
    assert len(places) == 1
    assert places[0].side is OrderSide.BUY
    assert places[0].intent_id == "as-bid-1"


def test_horizon_shrinks_tau_and_tightens_quotes() -> None:
    """Con más eventos, τ baja → half-spread AS más chico (ceteris paribus)."""
    mid = 100.0
    _, bid_early, ask_early = quote_prices(mid=mid, inventory=0.0, tau=1.0)
    _, bid_late, ask_late = quote_prices(mid=mid, inventory=0.0, tau=0.1)
    spread_early = ask_early - bid_early
    spread_late = ask_late - bid_late
    assert spread_late < spread_early

    strat = AvellanedaStoikovStrategy(
        {
            "quantity": "1",
            "gamma": 0.1,
            "sigma": 0.02,
            "kappa": 1.5,
            "horizon_events": 10,
            "max_pos": "10",
        }
    )
    book = dict(best_bid="99", best_ask="101", inventory="1")
    first = strat.on_event(_event(), _ctx(**book))
    places1 = [i for i in first if i.intent_type is IntentType.PLACE_ORDER]
    bid1 = next(i for i in places1 if i.side is OrderSide.BUY)
    ask1 = next(i for i in places1 if i.side is OrderSide.SELL)
    spread1 = ask1.price - bid1.price  # type: ignore[operator]

    for _ in range(7):
        strat.on_event(_event(), _ctx(**book))
    late = strat.on_event(_event(), _ctx(**book))
    places_late = [i for i in late if i.intent_type is IntentType.PLACE_ORDER]
    bid_l = next(i for i in places_late if i.side is OrderSide.BUY)
    ask_l = next(i for i in places_late if i.side is OrderSide.SELL)
    spread_l = ask_l.price - bid_l.price  # type: ignore[operator]
    assert spread_l < spread1
    assert strat.get_state()["n"] == 9
