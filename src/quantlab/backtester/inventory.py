"""Inventory tracking para Market Making (5B)."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from quantlab.core.types.enums import OrderSide
from quantlab.core.types.validation import require_non_negative


@dataclass
class InventoryTracker:
    """Inventario neto + límites de sesgo (inventory skew)."""

    max_abs_position: Decimal
    position: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    avg_entry: Decimal = Decimal("0")
    fills: int = 0
    _meta: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_negative(self.max_abs_position, "max_abs_position")
        if self.max_abs_position <= 0:
            raise ValueError("max_abs_position must be > 0")

    def can_increase(self, side: OrderSide, qty: Decimal) -> bool:
        if side is OrderSide.BUY:
            return self.position + qty <= self.max_abs_position
        return self.position - qty >= -self.max_abs_position

    def apply(self, side: OrderSide, qty: Decimal, price: Decimal) -> None:
        if not self.can_increase(side, qty):
            raise ValueError("inventory_limit")
        if side is OrderSide.BUY:
            if self.position >= 0:
                new_qty = self.position + qty
                self.avg_entry = (
                    (self.avg_entry * self.position + price * qty) / new_qty
                    if new_qty > 0
                    else Decimal("0")
                )
                self.position = new_qty
            else:
                # reduce short
                cover = min(qty, -self.position)
                self.realized_pnl += (self.avg_entry - price) * cover
                self.position += qty
                if self.position > 0:
                    self.avg_entry = price
                elif self.position == 0:
                    self.avg_entry = Decimal("0")
        else:
            if self.position <= 0:
                new_qty = self.position - qty
                abs_pos = abs(self.position)
                abs_new = abs(new_qty)
                self.avg_entry = (
                    (self.avg_entry * abs_pos + price * qty) / abs_new
                    if abs_new > 0
                    else Decimal("0")
                )
                self.position = new_qty
            else:
                close = min(qty, self.position)
                self.realized_pnl += (price - self.avg_entry) * close
                self.position -= qty
                if self.position < 0:
                    self.avg_entry = price
                elif self.position == 0:
                    self.avg_entry = Decimal("0")
        self.fills += 1

    def skew_bias(self) -> Decimal:
        """Sesgo [-1, 1]: inventario largo → favorece sells."""
        if self.max_abs_position == 0:
            return Decimal("0")
        return (self.position / self.max_abs_position).quantize(Decimal("0.0001"))
