"""Slippage basado en libro (5B)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import OrderSide
from quantlab.core.types.market import OrderBookSnapshot
from quantlab.core.types.validation import require_non_negative


@dataclass(frozen=True, slots=True)
class BookSlippageModel:
    """Impacto por caminar el libro (levels) hasta cubrir quantity.

    Si no hay profundidad suficiente, usa el último nivel + penalty_bps.
    """

    penalty_bps: Decimal = Decimal("0")
    model_id: str = "slippage.book.v1"

    def __post_init__(self) -> None:
        require_non_negative(self.penalty_bps, "penalty_bps")
        if self.penalty_bps >= Decimal("10000"):
            raise ValidationError("penalty_bps debe ser < 10000")

    def apply(
        self,
        *,
        side: OrderSide,
        quantity: Decimal,
        book: OrderBookSnapshot,
    ) -> Decimal:
        levels = book.asks if side is OrderSide.BUY else book.bids
        if not levels:
            raise ValidationError("libro vacío para slippage")
        remaining = quantity
        cost = Decimal("0")
        last_px = levels[0].price
        for level in levels:
            if remaining <= 0:
                break
            take = min(remaining, level.quantity)
            cost += take * level.price
            remaining -= take
            last_px = level.price
        if remaining > 0:
            penalty = last_px * (self.penalty_bps / Decimal("10000"))
            px = last_px + penalty if side is OrderSide.BUY else last_px - penalty
            if px <= 0:
                raise ValidationError("precio post-penalty inválido")
            cost += remaining * px
            remaining = Decimal("0")
        return (cost / quantity).quantize(Decimal("0.00000001"))
