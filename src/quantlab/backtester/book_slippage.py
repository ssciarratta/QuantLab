"""Slippage basado en libro (5B) — lineal y raíz cuadrada."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import OrderSide
from quantlab.core.types.market import OrderBookSnapshot
from quantlab.core.types.validation import require_non_negative, require_positive


class SlippageMode(StrEnum):
    """Política de impacto cuando el tamaño excede profundidad L2."""

    LINEAR = "linear"
    SQUARE_ROOT = "square_root"


@dataclass(frozen=True, slots=True)
class BookSlippageModel:
    """Impacto por caminar el libro (levels) hasta cubrir quantity.

    - ``LINEAR``: último nivel + ``penalty_bps`` sobre el remanente (retrocompatible).
    - ``SQUARE_ROOT``: impacto $I \\propto \\sigma \\sqrt{V/\\mathrm{Depth}}$ sobre el remanente.
    """

    penalty_bps: Decimal = Decimal("0")
    mode: SlippageMode = SlippageMode.LINEAR
    volatility: Decimal = Decimal("0.01")
    impact_coefficient: Decimal = Decimal("1")
    model_id: str = "slippage.book.v1"

    def __post_init__(self) -> None:
        require_non_negative(self.penalty_bps, "penalty_bps")
        if self.penalty_bps >= Decimal("10000"):
            raise ValidationError("penalty_bps debe ser < 10000")
        require_non_negative(self.volatility, "volatility")
        require_positive(self.impact_coefficient, "impact_coefficient")

    def apply(
        self,
        *,
        side: OrderSide,
        quantity: Decimal,
        book: OrderBookSnapshot,
    ) -> Decimal:
        if quantity <= 0:
            raise ValidationError("quantity debe ser > 0")
        levels = book.asks if side is OrderSide.BUY else book.bids
        if not levels:
            raise ValidationError("libro vacío para slippage")
        depth = sum((level.quantity for level in levels), Decimal("0"))
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
            px = self._remainder_price(side=side, last_px=last_px, remaining=remaining, depth=depth)
            cost += remaining * px
        return (cost / quantity).quantize(Decimal("0.00000001"))

    def _remainder_price(
        self,
        *,
        side: OrderSide,
        last_px: Decimal,
        remaining: Decimal,
        depth: Decimal,
    ) -> Decimal:
        if self.mode is SlippageMode.LINEAR:
            penalty = last_px * (self.penalty_bps / Decimal("10000"))
            px = last_px + penalty if side is OrderSide.BUY else last_px - penalty
        else:
            # I = σ * c * sqrt(V / Depth); Depth visible total del lado (mín. remaining).
            base_depth = depth if depth > 0 else remaining
            ratio = remaining / base_depth
            impact = self.volatility * self.impact_coefficient * ratio.sqrt()
            px = (
                last_px * (Decimal("1") + impact)
                if side is OrderSide.BUY
                else last_px * (Decimal("1") - impact)
            )
        if px <= 0:
            raise ValidationError("precio post-penalty inválido")
        return px
