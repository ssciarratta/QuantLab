"""Position sizing (Fase 14)."""

from __future__ import annotations

from decimal import Decimal

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.validation import require_positive


def fixed_fractional(equity: Decimal, *, risk_fraction: Decimal, stop_distance: Decimal) -> Decimal:
    """qty = (equity * risk_fraction) / stop_distance."""
    require_positive(equity, "equity")
    require_positive(risk_fraction, "risk_fraction")
    require_positive(stop_distance, "stop_distance")
    if risk_fraction >= 1:
        raise ValidationError("risk_fraction debe ser < 1")
    return ((equity * risk_fraction) / stop_distance).quantize(Decimal("0.00000001"))


def volatility_target(
    equity: Decimal, *, target_vol: Decimal, realized_vol: Decimal, base_qty: Decimal
) -> Decimal:
    require_positive(equity, "equity")
    require_positive(target_vol, "target_vol")
    require_positive(realized_vol, "realized_vol")
    require_positive(base_qty, "base_qty")
    scale = target_vol / realized_vol
    return (base_qty * scale).quantize(Decimal("0.00000001"))
