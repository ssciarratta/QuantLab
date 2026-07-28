"""Overlay post-backtest: PnL × leverage, liquidación y funding (toggles)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Sequence

from quantlab.core.exceptions import ValidationError

_ZERO = Decimal("0")
_ONE = Decimal("1")
_HUNDRED = Decimal("100")


@dataclass(frozen=True, slots=True)
class LeverageOverlayConfig:
    leverage: Decimal = _ONE
    simulate_liquidation: bool = True
    apply_funding: bool = True
    # Mantenimiento simplificado: liquidar si equity <= initial * maint_rate
    maintenance_rate: Decimal = Decimal("0.005")


def _dec(raw: str | Decimal | float | int) -> Decimal:
    try:
        return Decimal(str(raw))
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError(f"decimal inválido: {raw!r}") from exc


def _parse_equity_curve(backtest: dict[str, Any]) -> list[tuple[str, Decimal]]:
    """Extrae curva de equity del payload lab (equity_curve_tail o similar)."""
    points: list[tuple[str, Decimal]] = []
    tail = backtest.get("equity_curve_tail")
    if isinstance(tail, list):
        for item in tail:
            if isinstance(item, dict) and item.get("ts") is not None:
                points.append((str(item["ts"]), _dec(item["equity"])))
    if points:
        return points
    # Fallback: solo ini/fin
    ini = backtest.get("initial_equity")
    fin = backtest.get("final_equity")
    if ini is not None and fin is not None:
        return [("start", _dec(ini)), ("end", _dec(fin))]
    return []


def _apply_funding_series(
    *,
    equity_points: list[Decimal],
    funding_rates: Sequence[Decimal],
    notional_per_bar: Decimal,
) -> Decimal:
    """Resta funding sobre notional abierto (simplificado: 1 rate por barra)."""
    total = _ZERO
    n = min(len(equity_points), len(funding_rates))
    for i in range(n):
        rate = funding_rates[i]
        payment = notional_per_bar * rate
        equity_points[i] = equity_points[i] - payment
        total += payment
    return total


def apply_leverage_overlay(
    backtest: dict[str, Any],
    *,
    config: LeverageOverlayConfig | None = None,
    funding_rates: Sequence[Decimal] | None = None,
) -> dict[str, Any]:
    """Aplica modelo PnL×L sobre resultado 1x del lab.

    - ``simulate_liquidation=False`` → solo escala PnL, sin cortar.
    - ``apply_funding=False`` → ignora ``funding_rates``.
    """
    cfg = config or LeverageOverlayConfig()
    lev = cfg.leverage
    if lev < _ONE or lev > Decimal("125"):
        raise ValidationError("leverage debe estar entre 1 y 125")

    initial = _dec(backtest.get("initial_equity", "0"))
    final_1x = _dec(backtest.get("final_equity", "0"))
    curve = _parse_equity_curve(backtest)

    if not curve:
        pnl_1x = final_1x - initial
        final_lev = initial + pnl_1x * lev
        return {
            "initial_equity": str(initial),
            "final_equity": str(final_lev),
            "pnl": str(final_lev - initial),
            "pnl_pct": str((final_lev - initial) / initial * _HUNDRED) if initial else "0",
            "leverage": str(lev),
            "liquidated": False,
            "liquidation_bar_index": None,
            "total_funding": "0",
            "funding_applied": False,
            "liquidation_simulated": cfg.simulate_liquidation,
            "equity_curve": [],
        }

    equities_1x = [e for _, e in curve]
    pnl_series = [e - initial for e in equities_1x]
    equities_lev = [initial + p * lev for p in pnl_series]

    total_funding = _ZERO
    funding_applied = False
    if cfg.apply_funding and funding_rates:
        # Notional aproximado: equity × leverage al inicio (modelo simple)
        notional = initial * lev
        total_funding = _apply_funding_series(
            equity_points=equities_lev,
            funding_rates=funding_rates,
            notional_per_bar=notional,
        )
        funding_applied = True

    liquidated = False
    liq_idx: int | None = None
    maint_floor = initial * cfg.maintenance_rate

    if cfg.simulate_liquidation:
        for i, eq in enumerate(equities_lev):
            # Liquidación: equity agotada o bajo piso de mantenimiento
            if eq <= maint_floor:
                liquidated = True
                liq_idx = i
                for j in range(i, len(equities_lev)):
                    equities_lev[j] = maint_floor
                break

    final_lev = equities_lev[-1]
    pnl_lev = final_lev - initial
    pnl_pct = (pnl_lev / initial * _HUNDRED) if initial > _ZERO else _ZERO

    out_curve = [
        {"ts": curve[i][0], "equity": str(equities_lev[i])}
        for i in range(len(equities_lev))
    ]

    return {
        "initial_equity": str(initial),
        "final_equity": str(final_lev),
        "pnl": str(pnl_lev),
        "pnl_pct": str(pnl_pct),
        "leverage": str(lev),
        "liquidated": liquidated,
        "liquidation_bar_index": liq_idx,
        "total_funding": str(total_funding),
        "funding_applied": funding_applied,
        "liquidation_simulated": cfg.simulate_liquidation,
        "equity_curve": out_curve,
    }
