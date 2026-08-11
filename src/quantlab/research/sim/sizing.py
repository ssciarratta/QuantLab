"""Validación de tamaño de trade y reporte de margen (pico / faltante)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Literal, Mapping, Sequence

from quantlab.core.exceptions import ValidationError

_ZERO = Decimal("0")
_ONE = Decimal("1")

CapitalMode = Literal["fixed", "unconstrained"]
CAPITAL_MODES: tuple[str, ...] = ("fixed", "unconstrained")


def _dec(raw: object, *, field: str = "value") -> Decimal:
    try:
        return Decimal(str(raw))
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError(f"{field} inválido: {raw!r}") from exc


def validate_trade_size(
    capital: Decimal,
    per_trade: Decimal,
    leverage: Decimal,
    *,
    min_notional: Decimal | None = None,
    market_type: str = "futures",
    capital_mode: CapitalMode | str = "fixed",
) -> dict[str, Any]:
    """Valida margen/notional para un trade.

    v1: ``per_trade`` siempre en USD absoluto (no soporta sufijo %).
    Futures: notional = per_trade × leverage.
    Spot: notional = per_trade.

    ``capital_mode``:
    - ``fixed``: capital > 0 y per_trade ≤ capital.
    - ``unconstrained``: no hay tope de caja; solo se valida per_trade/leverage.
    """
    errors: list[str] = []
    mt = market_type.strip().lower()
    mode = str(capital_mode).strip().lower()
    if mode not in CAPITAL_MODES:
        raise ValidationError(
            f"capital_mode inválido: {capital_mode!r}; "
            f"permitidos: {', '.join(CAPITAL_MODES)}"
        )

    if per_trade <= _ZERO:
        errors.append("per_trade debe ser > 0")
    if leverage < _ONE:
        errors.append("leverage debe ser >= 1")

    margin = per_trade
    if mt == "futures":
        notional = per_trade * leverage
    elif mt == "spot":
        notional = per_trade
    else:
        raise ValidationError(f"market_type inválido: {market_type!r}")

    if mode == "fixed":
        if capital <= _ZERO:
            errors.append("capital debe ser > 0")
        elif per_trade > capital:
            errors.append("per_trade excede capital disponible")

    if notional <= _ZERO:
        errors.append("notional inválido")
    if min_notional is not None and notional < min_notional:
        errors.append(f"notional {notional} < mínimo {min_notional}")

    return {
        "ok": len(errors) == 0,
        "capital_mode": mode,
        "margin": str(margin),
        "notional": str(notional),
        "errors": errors,
    }


def estimate_peak_margin_from_fills(
    fills: Sequence[Mapping[str, Any]] | None,
    *,
    leverage: Decimal,
    market_type: str = "futures",
    margin_per_trade: Decimal | None = None,
) -> dict[str, Any]:
    """Estima margen pico a partir de fills (posición neta × mark).

    Futures: margen ≈ |qty neta| × precio / leverage.
    Spot: margen ≈ |qty neta| × precio (caja inmovilizada).
    """
    mt = market_type.strip().lower()
    lev = leverage if leverage >= _ONE else _ONE
    net_qty = _ZERO
    peak_notional = _ZERO
    peak_margin = _ZERO
    open_bars = 0
    n_fills = 0

    for raw in fills or ():
        if not isinstance(raw, Mapping):
            continue
        side = str(raw.get("side") or raw.get("order_side") or "").strip().lower()
        try:
            qty = _dec(
                raw.get("quantity", raw.get("qty", raw.get("filled_quantity", "0"))),
                field="quantity",
            )
            px = _dec(raw.get("price", raw.get("fill_price", "0")), field="price")
        except ValidationError:
            continue
        if qty <= _ZERO or px <= _ZERO:
            continue
        n_fills += 1
        if side in ("buy", "long", "b"):
            net_qty += qty
        elif side in ("sell", "short", "s"):
            net_qty -= qty
        else:
            # Sin side no podemos armar posición neta; igual cuenta el fill
            # como exposición puntual (peor caso = notional de ese fill).
            notional = qty * px
            if mt == "futures":
                margin = notional / lev
            else:
                margin = notional
            if notional > peak_notional:
                peak_notional = notional
            if margin > peak_margin:
                peak_margin = margin
            continue
        notional = abs(net_qty) * px
        if mt == "futures":
            margin = notional / lev
        else:
            margin = notional
        if notional > peak_notional:
            peak_notional = notional
        if margin > peak_margin:
            peak_margin = margin
        if net_qty != _ZERO:
            open_bars += 1

    configured = margin_per_trade if margin_per_trade is not None else _ZERO
    # lots concurrentes aprox. vs margen configurado por trade
    peak_lots = _ONE
    if configured > _ZERO and peak_margin > _ZERO:
        peak_lots = (peak_margin / configured).quantize(Decimal("0.01"))
        if peak_lots < _ONE:
            peak_lots = _ONE

    return {
        "n_fills_used": n_fills,
        "peak_notional": str(peak_notional),
        "peak_margin": str(peak_margin),
        "margin_per_trade": str(configured) if margin_per_trade is not None else None,
        "peak_lots_vs_per_trade": str(peak_lots),
        "ended_flat": net_qty == _ZERO,
        "net_qty_end": str(net_qty),
    }


def build_margin_report(
    *,
    capital_mode: CapitalMode | str,
    initial_capital: Decimal | None,
    per_trade: Decimal,
    leverage: Decimal,
    market_type: str,
    fills: Sequence[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    """Reporte de margen siempre presente (aparte del capital inicial).

    - ``margin_per_trade`` / ``notional_per_trade``: sizing configurado.
    - ``peak_margin`` / ``peak_notional``: estimado desde fills.
    - ``capital_shortfall``: cuánto faltó de caja (modo fixed).
    - ``capital_required``: pico de margen (modo unconstrained = capital mínimo).
    """
    mode = str(capital_mode).strip().lower()
    if mode not in CAPITAL_MODES:
        raise ValidationError(f"capital_mode inválido: {capital_mode!r}")

    sizing = validate_trade_size(
        initial_capital if initial_capital is not None else _ONE,
        per_trade,
        leverage,
        market_type=market_type,
        capital_mode=mode,
    )
    peak = estimate_peak_margin_from_fills(
        fills,
        leverage=leverage,
        market_type=market_type,
        margin_per_trade=per_trade,
    )
    peak_margin = _dec(peak["peak_margin"], field="peak_margin")
    # Si no hubo fills, el mínimo teórico sigue siendo el margen por trade
    capital_required = peak_margin if peak_margin > _ZERO else per_trade

    shortfall = _ZERO
    enough = True
    if mode == "fixed":
        cap = initial_capital if initial_capital is not None else _ZERO
        if capital_required > cap:
            shortfall = capital_required - cap
            enough = False
    else:
        enough = True  # sin tope: el output es cuánto hizo falta

    return {
        "capital_mode": mode,
        "initial_capital": str(initial_capital) if initial_capital is not None else None,
        "margin_per_trade": sizing["margin"],
        "notional_per_trade": sizing["notional"],
        "peak_margin": str(peak_margin),
        "peak_notional": peak["peak_notional"],
        "peak_lots_vs_per_trade": peak["peak_lots_vs_per_trade"],
        "capital_required": str(capital_required),
        "capital_shortfall": str(shortfall),
        "capital_enough": enough,
        "needed_more_money": (not enough) if mode == "fixed" else False,
        "n_fills_used": peak["n_fills_used"],
        "ended_flat": peak["ended_flat"],
        "note": (
            "Margen pico estimado desde fills (posición neta × precio). "
            "En fixed: shortfall = cuánto capital faltó vs el pico. "
            "En unconstrained: capital_required = margen mínimo sugerido."
        ),
    }
