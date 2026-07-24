"""Strategy Protocol — DEC-013.

Replaces the original on_bar() with a generic on_event() contract.
Strategies receive MarketEvent (which may wrap bars, trades, book updates)
and return a tuple of OrderIntent.

No separate on_bar() method exists; bar processing happens via
MarketEvent with event_type=BAR.
"""

from __future__ import annotations

from typing import Protocol

from quantlab.core.types.json_types import JsonObject
from quantlab.core.types.trading import MarketEvent, OrderIntent, StrategyContext


class Strategy(Protocol):
    """Universal strategy contract.

    All strategies must implement on_event to process market events
    and return trading intents.
    """

    def on_event(
        self,
        event: MarketEvent,
        context: StrategyContext,
    ) -> tuple[OrderIntent, ...]:
        """Process a market event and return zero or more order intents."""
        ...

    def get_parameters(self) -> JsonObject:
        """Return current strategy parameters (for optimization/serialization)."""
        ...

    def reset(self) -> None:
        """Reset internal state for a new simulation run."""
        ...
