"""Tests de DummyStrategy."""

from datetime import UTC, datetime
from decimal import Decimal

from quantlab.core.contracts.strategy import StrategyContext
from quantlab.core.types.enums import ClockMode, ClockSpeed, EventType, IntentType
from quantlab.core.types.market import MarketEvent
from quantlab.core.types.portfolio import SimulationClock
from quantlab.research.strategies.dummy_strategy import DummyStrategy


def test_dummy_strategy_returns_place_on_bar_event() -> None:
    strategy = DummyStrategy()
    event = MarketEvent(
        event_id="e1",
        event_type=EventType.BAR,
        timestamp=datetime.now(tz=UTC),
        instrument_id="BTC-USDT",
    )
    context = StrategyContext(
        clock=SimulationClock(
            current_time=datetime.now(tz=UTC),
            mode=ClockMode.EVENT_DRIVEN,
            speed=ClockSpeed.ACCELERATED,
        )
    )
    intents = strategy.on_event(event, context)
    assert len(intents) == 1
    assert intents[0].intent_type is IntentType.PLACE_ORDER
    assert intents[0].quantity == Decimal("0.01")


def test_dummy_strategy_reset_clears_state() -> None:
    strategy = DummyStrategy()
    strategy.on_event(
        MarketEvent(
            event_id="e1",
            event_type=EventType.TIMER,
            timestamp=datetime.now(tz=UTC),
            instrument_id="X",
        ),
        StrategyContext(
            clock=SimulationClock(
                current_time=datetime.now(tz=UTC),
                mode=ClockMode.EVENT_DRIVEN,
                speed=ClockSpeed.ACCELERATED,
            )
        ),
    )
    assert strategy.get_state()["events_seen"] == 1
    strategy.reset()
    assert strategy.get_state()["events_seen"] == 0
