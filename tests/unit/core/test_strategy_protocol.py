"""Tests for Strategy Protocol — DEC-013.

Validates that:
- on_event() is the contract method (not on_bar)
- DummyStrategy satisfies the Protocol
- Strategy returns proper OrderIntent tuples
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import MappingProxyType

from quantlab.cli import DummyStrategy
from quantlab.core.interfaces.strategy import Strategy
from quantlab.core.types.trading import (
    IntentType,
    MarketEvent,
    MarketEventType,
    OrderIntent,
    StrategyContext,
)


class TestStrategyProtocol:
    def test_dummy_strategy_satisfies_protocol(self):
        """DummyStrategy must satisfy Strategy Protocol."""
        strategy: Strategy = DummyStrategy()
        assert hasattr(strategy, "on_event")
        assert hasattr(strategy, "get_parameters")
        assert hasattr(strategy, "reset")

    def test_no_on_bar_method(self):
        """Strategy Protocol must NOT have on_bar."""
        assert not hasattr(Strategy, "on_bar")

    def test_on_event_returns_tuple_of_intents(self):
        now = datetime.now(UTC)
        strategy = DummyStrategy()
        event = MarketEvent.create(
            event_type=MarketEventType.BAR,
            timestamp=now,
            symbol="BTC-USDT",
            payload={"open": 50000.0},
        )
        context = StrategyContext.create(
            timestamp=now,
            balance_available=10000.0,
            balance_locked=0.0,
        )
        result = strategy.on_event(event, context)
        assert isinstance(result, tuple)
        assert all(isinstance(i, OrderIntent) for i in result)

    def test_on_event_bar_produces_place_order(self):
        now = datetime.now(UTC)
        strategy = DummyStrategy()
        event = MarketEvent.create(
            event_type=MarketEventType.BAR,
            timestamp=now,
            symbol="BTC-USDT",
        )
        context = StrategyContext.create(
            timestamp=now,
            balance_available=10000.0,
            balance_locked=0.0,
        )
        result = strategy.on_event(event, context)
        assert len(result) == 1
        assert result[0].intent_type == IntentType.PLACE_ORDER

    def test_on_event_non_bar_produces_no_action(self):
        now = datetime.now(UTC)
        strategy = DummyStrategy()
        event = MarketEvent.create(
            event_type=MarketEventType.TRADE,
            timestamp=now,
            symbol="BTC-USDT",
        )
        context = StrategyContext.create(
            timestamp=now,
            balance_available=10000.0,
            balance_locked=0.0,
        )
        result = strategy.on_event(event, context)
        assert len(result) == 1
        assert result[0].intent_type == IntentType.NO_ACTION

    def test_get_parameters_returns_mapping(self):
        strategy = DummyStrategy()
        params = strategy.get_parameters()
        assert isinstance(params, MappingProxyType)

    def test_reset_is_callable(self):
        strategy = DummyStrategy()
        strategy.reset()
