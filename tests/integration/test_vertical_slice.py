"""Integration test: vertical slice with injected strategy.

Validates the full pipeline: config → logging → strategy → intents.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import MappingProxyType

from quantlab.cli import DummyStrategy
from quantlab.core.interfaces.strategy import Strategy
from quantlab.core.types.json_types import JsonObject
from quantlab.core.types.trading import (
    IntentType,
    MarketEvent,
    MarketEventType,
    OrderIntent,
    StrategyContext,
)
from quantlab.infra.config import load_config
from quantlab.infra.logging import setup_logging
from quantlab.infra.utils import compute_lockfile_hash, get_git_commit


class PassThroughStrategy:
    """Strategy that always returns NO_ACTION for testing."""

    def on_event(
        self,
        event: MarketEvent,
        context: StrategyContext,
    ) -> tuple[OrderIntent, ...]:
        return (OrderIntent(intent_type=IntentType.NO_ACTION),)

    def get_parameters(self) -> JsonObject:
        return MappingProxyType({})

    def reset(self) -> None:
        pass


def _run_vertical_slice(strategy: Strategy) -> list[OrderIntent]:
    """Run vertical slice with an injected strategy."""
    config = load_config()
    setup_logging(config)

    commit = get_git_commit()
    lockfile_hash = compute_lockfile_hash()
    assert isinstance(commit, str)
    assert isinstance(lockfile_hash, str)

    now = datetime.now(UTC)
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

    intents = strategy.on_event(event, context)
    return list(intents)


class TestVerticalSlice:
    def test_with_dummy_strategy(self):
        intents = _run_vertical_slice(DummyStrategy())
        assert len(intents) == 1
        assert intents[0].intent_type == IntentType.PLACE_ORDER

    def test_with_passthrough_strategy(self):
        intents = _run_vertical_slice(PassThroughStrategy())
        assert len(intents) == 1
        assert intents[0].intent_type == IntentType.NO_ACTION

    def test_config_loads(self):
        config = load_config()
        assert config is not None

    def test_git_commit_available(self):
        commit = get_git_commit()
        assert commit != ""

    def test_lockfile_hash_computed(self):
        lh = compute_lockfile_hash()
        assert isinstance(lh, str)
        assert len(lh) > 0
