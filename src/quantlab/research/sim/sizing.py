"""Validación de tamaño de trade para sim multi-venue."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from quantlab.core.exceptions import ValidationError

_ZERO = Decimal("0")


def validate_trade_size(
    capital: Decimal,
    per_trade: Decimal,
    leverage: Decimal,
    *,
    min_notional: Decimal | None = None,
    market_type: str = "futures",
) -> dict[str, Any]:
    """Valida margen/notional para un trade.

    v1: ``per_trade`` siempre en USD absoluto (no soporta sufijo %).
    Futures: notional = per_trade × leverage.
    Spot: notional = per_trade.
    """
    errors: list[str] = []
    mt = market_type.strip().lower()

    if capital <= _ZERO:
        errors.append("capital debe ser > 0")
    if per_trade <= _ZERO:
        errors.append("per_trade debe ser > 0")
    if leverage < Decimal("1"):
        errors.append("leverage debe ser >= 1")

    margin = per_trade
    if mt == "futures":
        notional = per_trade * leverage
    elif mt == "spot":
        notional = per_trade
    else:
        raise ValidationError(f"market_type inválido: {market_type!r}")

    if per_trade > capital:
        errors.append("per_trade excede capital disponible")
    if notional <= _ZERO:
        errors.append("notional inválido")
    if min_notional is not None and notional < min_notional:
        errors.append(f"notional {notional} < mínimo {min_notional}")

    return {
        "ok": len(errors) == 0,
        "margin": str(margin),
        "notional": str(notional),
        "errors": errors,
    }
