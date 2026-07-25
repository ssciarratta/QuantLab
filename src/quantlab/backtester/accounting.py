"""Contabilidad cuadrada — invariantes de Portfolio/Ledger (Fase 6 / 5A)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import OrderSide
from quantlab.core.types.results import SimulationResult

# Convención TD-17 (explícita): realized_pnl de posiciones es BRUTO (sin fees).
# Los fees impactan cash/equity vía fill.fee, no se restan del realized_pnl reportado.
REALIZED_PNL_CONVENTION = "gross_excluding_fees"


@dataclass(frozen=True, slots=True)
class AccountingReport:
    """Resultado de la verificación de contabilidad."""

    ok: bool
    issues: tuple[str, ...]
    reconstructed_cash: Decimal
    reported_cash: Decimal
    reported_equity: Decimal
    total_fees: Decimal
    realized_pnl_convention: str = REALIZED_PNL_CONVENTION


def _order_sides(result: SimulationResult) -> dict[str, OrderSide]:
    return {o.order_id: o.side for o in result.orders}


def reconstruct_cash(
    result: SimulationResult, *, initial_cash: Decimal
) -> tuple[Decimal, Decimal, tuple[str, ...]]:
    """Reconstruye cash y fees a partir de fills (long-only baseline 5A).

    Retorna también IDs de fills huérfanos (order_id desconocido).
    """
    cash = initial_cash
    fees = Decimal("0")
    sides = _order_sides(result)
    orphans: list[str] = []
    for fill in result.fills:
        side = sides.get(fill.order_id)
        if side is None:
            orphans.append(fill.fill_id)
            continue
        fee = fill.fee.amount
        fees += fee
        notional = fill.price * fill.quantity
        if side is OrderSide.BUY:
            cash -= notional + fee
        else:
            cash += notional - fee
    return cash, fees, tuple(orphans)


def assert_accounting_balanced(
    result: SimulationResult,
    *,
    initial_cash: Decimal,
    tolerance: Decimal = Decimal("0.00000001"),
) -> AccountingReport:
    """Valida que cash/equity/fees cuadren al cierre del backtest.

    Invariantes:
    1. Hay al menos un snapshot de portfolio.
    2. Cash reconstruido desde fills ≈ cash reportado (última balance).
    3. total_equity ≈ cash + Σ(qty * mark) de posiciones.
    4. Σ fees de fills == total_fees reportado en reconstrucción.
    5. Valores finitos (sin NaN/Infinity).
    """
    issues: list[str] = []
    if not result.portfolio_snapshots:
        raise ValidationError("accounting: sin portfolio_snapshots")
    if not result.equity_curve:
        raise ValidationError("accounting: sin equity_curve")

    snap = result.portfolio_snapshots[-1]
    if not snap.balances:
        raise ValidationError("accounting: snapshot sin balances")

    reported_cash = snap.balances[0].total
    reported_equity = snap.total_equity
    reconstructed_cash, total_fees, orphans = reconstruct_cash(
        result, initial_cash=initial_cash
    )
    if orphans:
        issues.append(f"orphan fills (order_id desconocido): {', '.join(orphans)}")

    for label, value in (
        ("reported_cash", reported_cash),
        ("reported_equity", reported_equity),
        ("reconstructed_cash", reconstructed_cash),
        ("total_fees", total_fees),
    ):
        if value.is_nan() or value.is_infinite():
            issues.append(f"{label} no finito")

    if abs(reconstructed_cash - reported_cash) > tolerance:
        issues.append(f"cash mismatch: reconstructed={reconstructed_cash} reported={reported_cash}")

    # equity = cash + mark-to-market de posiciones
    marks_value = Decimal("0")
    for pos in snap.positions:
        # mark implícito desde unrealized: mark = avg + u/qty
        if pos.quantity == 0:
            continue
        mark = pos.avg_entry_price + (pos.unrealized_pnl / pos.quantity)
        marks_value += mark * pos.quantity
    expected_equity = reported_cash + marks_value
    if abs(expected_equity - reported_equity) > tolerance:
        issues.append(f"equity mismatch: cash+marks={expected_equity} reported={reported_equity}")

    curve_end = result.equity_curve[-1].equity
    if abs(curve_end - reported_equity) > tolerance:
        issues.append(f"equity_curve[-1]={curve_end} != snapshot.total_equity={reported_equity}")

    fill_fee_sum = sum((f.fee.amount for f in result.fills), Decimal("0"))
    if abs(fill_fee_sum - total_fees) > tolerance:
        issues.append(f"fee sum mismatch: fills={fill_fee_sum} reconstructed={total_fees}")

    ok = not issues
    report = AccountingReport(
        ok=ok,
        issues=tuple(issues),
        reconstructed_cash=reconstructed_cash,
        reported_cash=reported_cash,
        reported_equity=reported_equity,
        total_fees=total_fees,
    )
    if not ok:
        raise ValidationError("accounting no cuadra: " + "; ".join(issues))
    return report
