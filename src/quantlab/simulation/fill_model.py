"""Política de fill bar-based baseline (DEC-045)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantlab.core.types.enums import IntentType, OrderSide, OrderType
from quantlab.core.types.market import Bar
from quantlab.core.types.orders import OrderIntent


@dataclass(frozen=True, slots=True)
class FillDecision:
    """Decisión de fill para una intención en la barra actual."""

    filled: bool
    price: Decimal | None
    quantity: Decimal | None
    reason: str


class ImmediateBarFillModel:
    """Fill inmediato en la misma barra (baseline 5A simplificado).

    - MARKET → close
    - LIMIT BUY → si low <= price, fill al precio límite
    - LIMIT SELL → si high >= price, fill al precio límite
    """

    model_id: str = "fill.immediate_bar.v1"

    def evaluate(self, intent: OrderIntent, bar: Bar) -> FillDecision:
        if intent.intent_type is not IntentType.PLACE_ORDER:
            return FillDecision(False, None, None, "not_place")
        if intent.instrument_id != bar.instrument_id:
            return FillDecision(False, None, None, "instrument_mismatch")
        if intent.quantity is None or intent.side is None or intent.order_type is None:
            return FillDecision(False, None, None, "incomplete_intent")

        qty = intent.quantity
        if intent.order_type is OrderType.MARKET:
            return FillDecision(True, bar.close, qty, "market_close")

        if intent.order_type is OrderType.LIMIT:
            if intent.price is None:
                return FillDecision(False, None, None, "limit_without_price")
            limit = intent.price
            if intent.side is OrderSide.BUY:
                if bar.low <= limit:
                    return FillDecision(True, limit, qty, "limit_buy_touch")
                return FillDecision(False, None, None, "limit_buy_not_touched")
            if intent.side is OrderSide.SELL:
                if bar.high >= limit:
                    return FillDecision(True, limit, qty, "limit_sell_touch")
                return FillDecision(False, None, None, "limit_sell_not_touched")

        return FillDecision(False, None, None, "unsupported_order_type")
