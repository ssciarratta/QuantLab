"""Fill parcial / cancel / replace — políticas 5B."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantlab.core.types.enums import IntentType, OrderSide, OrderType
from quantlab.core.types.market import Trade
from quantlab.core.types.orders import OrderIntent


@dataclass(frozen=True, slots=True)
class PartialFillDecision:
    filled: bool
    fill_qty: Decimal
    fill_price: Decimal | None
    remaining_qty: Decimal
    reason: str
    liquidity_maker: bool = False


@dataclass
class RestingOrder:
    """Orden resting en el libro simulado."""

    order_id: str
    intent: OrderIntent
    remaining: Decimal
    status: str = "open"


class PartialFillModel:
    """Match contra trades del tape (fill parcial permitido)."""

    model_id: str = "fill.partial_trade.v1"

    def __init__(self, *, max_fill_ratio: Decimal = Decimal("1")) -> None:
        if max_fill_ratio <= 0 or max_fill_ratio > 1:
            raise ValueError("max_fill_ratio must be in (0, 1]")
        self._max_ratio = max_fill_ratio

    def match_trade(self, order: RestingOrder, trade: Trade) -> PartialFillDecision:
        intent = order.intent
        zero = Decimal("0")
        if intent.instrument_id != trade.instrument_id:
            return PartialFillDecision(False, zero, None, order.remaining, "instrument_mismatch")
        if intent.intent_type is not IntentType.PLACE_ORDER:
            return PartialFillDecision(False, zero, None, order.remaining, "not_place")
        if intent.side is None or intent.quantity is None or intent.order_type is None:
            return PartialFillDecision(False, zero, None, order.remaining, "incomplete")

        available = (trade.quantity * self._max_ratio).quantize(Decimal("0.00000001"))
        if available <= 0:
            return PartialFillDecision(False, zero, None, order.remaining, "no_liquidity")

        if intent.order_type is OrderType.MARKET:
            take = min(order.remaining, available)
            return PartialFillDecision(
                True, take, trade.price, order.remaining - take, "market_trade"
            )

        if intent.order_type is OrderType.LIMIT and intent.price is not None:
            limit = intent.price
            if intent.side is OrderSide.BUY and trade.price <= limit:
                take = min(order.remaining, available)
                return PartialFillDecision(
                    True,
                    take,
                    limit,
                    order.remaining - take,
                    "limit_buy_partial",
                    liquidity_maker=True,
                )
            if intent.side is OrderSide.SELL and trade.price >= limit:
                take = min(order.remaining, available)
                return PartialFillDecision(
                    True,
                    take,
                    limit,
                    order.remaining - take,
                    "limit_sell_partial",
                    liquidity_maker=True,
                )
            return PartialFillDecision(False, zero, None, order.remaining, "limit_not_touched")

        return PartialFillDecision(False, zero, None, order.remaining, "unsupported")
