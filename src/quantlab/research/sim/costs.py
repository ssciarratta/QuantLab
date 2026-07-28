"""Costos extra de simulación (fijos o % notional)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Literal

from quantlab.core.exceptions import ValidationError

ExtraCostKind = Literal["fixed_usd", "percent_notional"]
_ZERO = Decimal("0")
_HUNDRED = Decimal("100")


@dataclass(frozen=True, slots=True)
class ExtraCost:
    name: str
    kind: ExtraCostKind
    amount: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "amount": str(self.amount),
        }


def apply_extra_costs(
    *,
    costs: Sequence[ExtraCost],
    notional: Decimal,
) -> Decimal:
    """Suma costos extra en USD (fixed_usd + percent_notional × notional)."""
    total = _ZERO
    for cost in costs:
        if cost.amount < _ZERO:
            raise ValidationError(f"costo extra negativo: {cost.name!r}")
        if cost.kind == "fixed_usd":
            total += cost.amount
        elif cost.kind == "percent_notional":
            total += notional * cost.amount / _HUNDRED
        else:
            raise ValidationError(f"kind de costo inválido: {cost.kind!r}")
    return total
