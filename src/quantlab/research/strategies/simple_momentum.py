"""Estrategia bar-based simple momentum (Fase 6 / 5A)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from quantlab.core.contracts.strategy import StrategyContext
from quantlab.core.types.enums import IntentType, OrderSide, OrderType, TimeInForce
from quantlab.core.types.market import Bar, MarketEvent
from quantlab.core.types.orders import OrderIntent


class SimpleMomentumStrategy:
    """Compra si el close sube N barras consecutivas; vende si baja N.

    Baseline 5A — no market making. Long-only (no short).
    """

    def __init__(self, parameters: dict[str, Any] | None = None) -> None:
        self._parameters = dict(parameters or {})
        self._closes: list[Decimal] = []
        self._position = Decimal("0")

    def on_event(self, event: MarketEvent, context: StrategyContext) -> tuple[OrderIntent, ...]:
        return ()

    def on_bar(self, bar: Bar, context: StrategyContext) -> tuple[OrderIntent, ...]:
        lookback = int(self._parameters.get("lookback", 3))
        qty = Decimal(str(self._parameters.get("quantity", "1")))
        self._closes.append(bar.close)
        if len(self._closes) < lookback + 1:
            return (
                OrderIntent(
                    intent_id="noop-warmup",
                    intent_type=IntentType.NO_ACTION,
                    instrument_id=bar.instrument_id,
                ),
            )

        window = self._closes[-(lookback + 1) :]
        up = all(window[i] > window[i - 1] for i in range(1, len(window)))
        down = all(window[i] < window[i - 1] for i in range(1, len(window)))

        # Sync posición desde contexto si existe
        if context.portfolio_state is not None:
            held = Decimal("0")
            for p in context.portfolio_state.positions:
                if p.instrument_id == bar.instrument_id:
                    held = p.quantity
            self._position = held

        if up and self._position <= 0:
            self._position = qty
            return (
                OrderIntent(
                    intent_id=f"mom-buy-{len(self._closes)}",
                    intent_type=IntentType.PLACE_ORDER,
                    instrument_id=bar.instrument_id,
                    side=OrderSide.BUY,
                    quantity=qty,
                    price=bar.high,
                    order_type=OrderType.LIMIT,
                    time_in_force=TimeInForce.GTC,
                ),
            )
        if down and self._position > 0:
            sell_qty = self._position
            self._position = Decimal("0")
            return (
                OrderIntent(
                    intent_id=f"mom-sell-{len(self._closes)}",
                    intent_type=IntentType.PLACE_ORDER,
                    instrument_id=bar.instrument_id,
                    side=OrderSide.SELL,
                    quantity=sell_qty,
                    price=bar.low,
                    order_type=OrderType.LIMIT,
                    time_in_force=TimeInForce.GTC,
                ),
            )
        return (
            OrderIntent(
                intent_id="noop",
                intent_type=IntentType.NO_ACTION,
                instrument_id=bar.instrument_id,
            ),
        )

    def get_parameters(self) -> dict[str, Any]:
        return dict(self._parameters)

    def set_parameters(self, params: dict[str, Any]) -> None:
        self._parameters = dict(params)

    def get_state(self) -> dict[str, Any]:
        return {"position": str(self._position), "n_closes": len(self._closes)}

    def reset(self) -> None:
        self._closes.clear()
        self._position = Decimal("0")
