"""Estrategia mínima para vertical slice de Fase 2."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import uuid4

from quantlab.core.contracts.strategy import StrategyContext
from quantlab.core.types.enums import EventType, IntentType, OrderSide, OrderType, TimeInForce
from quantlab.core.types.market import Bar, MarketEvent
from quantlab.core.types.orders import OrderIntent


class DummyStrategy:
    """Estrategia de demostración: reacciona a barras con una intención place_order."""

    def __init__(self, parameters: dict[str, Any] | None = None) -> None:
        self._parameters: dict[str, Any] = dict(parameters or {})
        self._events_seen: int = 0

    def on_event(self, event: MarketEvent, context: StrategyContext) -> tuple[OrderIntent, ...]:
        self._events_seen += 1
        if event.event_type is EventType.BAR:
            return (self._build_place_intent(event.instrument_id),)
        if event.event_type is EventType.TIMER:
            return (
                OrderIntent(
                    intent_id=str(uuid4()),
                    intent_type=IntentType.NO_ACTION,
                    instrument_id=event.instrument_id,
                ),
            )
        return ()

    def on_bar(self, bar: Bar, context: StrategyContext) -> tuple[OrderIntent, ...]:
        return (self._build_place_intent(bar.instrument_id),)

    def get_parameters(self) -> dict[str, Any]:
        return dict(self._parameters)

    def set_parameters(self, params: dict[str, Any]) -> None:
        self._parameters = dict(params)

    def get_state(self) -> dict[str, Any]:
        return {"events_seen": self._events_seen}

    def reset(self) -> None:
        self._events_seen = 0

    def _build_place_intent(self, instrument_id: str) -> OrderIntent:
        qty = Decimal(str(self._parameters.get("quantity", "0.01")))
        price = Decimal(str(self._parameters.get("price", "100.0")))
        return OrderIntent(
            intent_id=str(uuid4()),
            intent_type=IntentType.PLACE_ORDER,
            instrument_id=instrument_id,
            side=OrderSide.BUY,
            quantity=qty,
            price=price,
            order_type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
        )
