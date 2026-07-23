"""CLI entry points for QuantLab."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from types import MappingProxyType

from quantlab.core.types.json_types import JsonObject
from quantlab.core.types.market import Instrument, OrderSide, OrderType
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


class DummyStrategy:
    """Minimal strategy for vertical slice testing.

    Implements the Strategy Protocol via on_event().
    """

    def on_event(
        self,
        event: MarketEvent,
        context: StrategyContext,
    ) -> tuple[OrderIntent, ...]:
        if event.event_type == MarketEventType.BAR:
            instrument = Instrument.create(
                symbol=event.symbol,
                base_asset="BTC",
                quote_asset="USDT",
                tick_size=0.01,
                lot_size=0.001,
            )
            return (
                OrderIntent(
                    intent_type=IntentType.PLACE_ORDER,
                    instrument=instrument,
                    side=OrderSide.BUY,
                    quantity=0.001,
                    order_type=OrderType.LIMIT,
                    price=50000.0,
                ),
            )
        return (OrderIntent(intent_type=IntentType.NO_ACTION),)

    def get_parameters(self) -> JsonObject:
        return MappingProxyType({"dummy_param": 1.0})

    def reset(self) -> None:
        pass


def vertical_slice() -> None:
    """Execute the vertical slice: config → logging → strategy → intents."""
    print("=" * 60)
    print("QuantLab Vertical Slice")
    print("=" * 60)

    config = load_config()
    logger = setup_logging(config)
    logger.info("vertical_slice_start", environment=config.environment.value)

    commit = get_git_commit()
    lockfile_hash = compute_lockfile_hash()
    logger.info("reproducibility_info", commit=commit, lockfile_hash=lockfile_hash)

    now = datetime.now(UTC)
    event = MarketEvent.create(
        event_type=MarketEventType.BAR,
        timestamp=now,
        symbol="BTC-USDT",
        payload={"open": 50000.0, "high": 51000.0, "low": 49500.0, "close": 50500.0},
    )

    context = StrategyContext.create(
        timestamp=now,
        balance_available=10000.0,
        balance_locked=0.0,
        position=0.0,
        parameters={"risk_factor": 0.02},
    )

    strategy = DummyStrategy()
    intents = strategy.on_event(event, context)

    for i, intent in enumerate(intents):
        logger.info(
            "order_intent",
            index=i,
            type=intent.intent_type.value,
            side=intent.side.value if intent.side else None,
            quantity=intent.quantity,
        )

    print(f"\nCommit: {commit}")
    print(f"Lockfile hash: {lockfile_hash}")
    print(f"Environment: {config.environment.value}")
    print("Events processed: 1")
    print(f"Intents generated: {len(intents)}")
    print("\nVertical slice: PASSED")
    print("=" * 60)
    sys.exit(0)
