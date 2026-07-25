"""Estrategia buy-once para demos/tests Fase 4."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from quantlab.core.contracts.strategy import StrategyContext
from quantlab.core.types.enums import IntentType, OrderSide, OrderType, TimeInForce
from quantlab.core.types.market import Bar, MarketEvent
from quantlab.core.types.orders import OrderIntent


class BuyOnceStrategy:
    """Compra una sola vez en la primera barra; luego NO_ACTION."""

    def __init__(self, parameters: dict[str, Any] | None = None) -> None:
        self._parameters = dict(parameters or {})
        self._bought = False

    def on_event(self, event: MarketEvent, context: StrategyContext) -> tuple[OrderIntent, ...]:
        return ()

    def on_bar(self, bar: Bar, context: StrategyContext) -> tuple[OrderIntent, ...]:
        if self._bought:
            return (
                OrderIntent(
                    intent_id="noop",
                    intent_type=IntentType.NO_ACTION,
                    instrument_id=bar.instrument_id,
                ),
            )
        self._bought = True
        qty = Decimal(str(self._parameters.get("quantity", "1")))
        # Precio límite alto para asegurar fill en ImmediateBarFillModel
        price = Decimal(str(self._parameters.get("price", str(bar.high))))
        return (
            OrderIntent(
                intent_id="buy-once-1",
                intent_type=IntentType.PLACE_ORDER,
                instrument_id=bar.instrument_id,
                side=OrderSide.BUY,
                quantity=qty,
                price=price,
                order_type=OrderType.LIMIT,
                time_in_force=TimeInForce.GTC,
            ),
        )

    def get_parameters(self) -> dict[str, Any]:
        return dict(self._parameters)

    def set_parameters(self, params: dict[str, Any]) -> None:
        self._parameters = dict(params)

    def get_state(self) -> dict[str, Any]:
        return {"bought": self._bought}

    def reset(self) -> None:
        self._bought = False
