"""Motor de métricas de rendimiento (Fase 4)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from math import sqrt

from quantlab.core.types.enums import OrderSide
from quantlab.core.types.results import EquityPoint, MetricsResult, SimulationResult

METRICS_VERSION = "1.1.0"


def equity_returns(curve: tuple[EquityPoint, ...]) -> tuple[float, ...]:
    if len(curve) < 2:
        return ()
    out: list[float] = []
    for i in range(1, len(curve)):
        prev = float(curve[i - 1].equity)
        cur = float(curve[i].equity)
        if prev == 0:
            continue
        out.append((cur - prev) / prev)
    return tuple(out)


def max_drawdown(curve: tuple[EquityPoint, ...]) -> float:
    if not curve:
        return 0.0
    peak = float(curve[0].equity)
    max_dd = 0.0
    for point in curve:
        eq = float(point.equity)
        if eq > peak:
            peak = eq
        if peak > 0:
            dd = (peak - eq) / peak
            if dd > max_dd:
                max_dd = dd
    return max_dd


def sharpe_ratio(returns: tuple[float, ...], *, periods_per_year: float = 252.0) -> float:
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    std = sqrt(var) if var > 0 else 0.0
    if std == 0.0:
        return 0.0
    return (mean / std) * sqrt(periods_per_year)


def sortino_ratio(
    returns: tuple[float, ...],
    *,
    periods_per_year: float = 252.0,
    target: float = 0.0,
) -> float:
    """Sortino: retorno medio anualizado / downside deviation."""
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    downside_sq = [(min(0.0, r - target)) ** 2 for r in returns]
    downside_var = sum(downside_sq) / len(returns)
    downside_dev = sqrt(downside_var) if downside_var > 0 else 0.0
    if downside_dev == 0.0:
        return 0.0
    return ((mean - target) / downside_dev) * sqrt(periods_per_year)


def calmar_ratio(
    curve: tuple[EquityPoint, ...],
    *,
    periods_per_year: float = 252.0,
) -> float:
    """Calmar: retorno anualizado / max drawdown."""
    if len(curve) < 2:
        return 0.0
    start_eq = float(curve[0].equity)
    end_eq = float(curve[-1].equity)
    if start_eq <= 0:
        return 0.0
    total_return = (end_eq - start_eq) / start_eq
    n_periods = len(curve) - 1
    ann = total_return * (periods_per_year / n_periods) if n_periods > 0 else 0.0
    mdd = max_drawdown(curve)
    if mdd <= 0:
        return 0.0
    return ann / mdd


def _mark_prices(result: SimulationResult) -> dict[str, Decimal]:
    """Último precio conocido por instrumento (fills → snapshots)."""
    marks: dict[str, Decimal] = {}
    for fill in result.fills:
        marks[fill.instrument_id] = fill.price
    if result.portfolio_snapshots:
        snap = result.portfolio_snapshots[-1]
        for pos in snap.positions:
            # mark implícito desde unrealized: mark = avg + u/qty
            if pos.quantity != 0:
                marks[pos.instrument_id] = pos.avg_entry_price + (pos.unrealized_pnl / pos.quantity)
    return marks


def win_rate_and_profit_factor(result: SimulationResult) -> tuple[float, float]:
    """Win rate y profit factor vía FIFO + MTM de posiciones abiertas al cierre."""
    inventory: dict[str, list[tuple[Decimal, Decimal]]] = {}
    wins = 0
    losses = 0
    gross_profit = 0.0
    gross_loss = 0.0

    order_side = {o.order_id: o.side for o in result.orders}
    for fill in result.fills:
        side = order_side.get(fill.order_id)
        if side is None:
            continue
        lots = inventory.setdefault(fill.instrument_id, [])
        if side is OrderSide.BUY:
            lots.append((fill.quantity, fill.price))
            continue
        remaining = fill.quantity
        while remaining > 0 and lots:
            lot_qty, lot_px = lots[0]
            take = min(remaining, lot_qty)
            pnl = float((fill.price - lot_px) * take)
            if pnl >= 0:
                wins += 1
                gross_profit += pnl
            else:
                losses += 1
                gross_loss += abs(pnl)
            lot_qty -= take
            remaining -= take
            if lot_qty == 0:
                lots.pop(0)
            else:
                lots[0] = (lot_qty, lot_px)

    # Posiciones abiertas: mark-to-market al cierre del experimento
    marks = _mark_prices(result)
    for instrument_id, lots in inventory.items():
        mark = marks.get(instrument_id)
        if mark is None:
            continue
        for lot_qty, lot_px in lots:
            if lot_qty <= 0:
                continue
            pnl = float((mark - lot_px) * lot_qty)
            if pnl >= 0:
                wins += 1
                gross_profit += pnl
            else:
                losses += 1
                gross_loss += abs(pnl)

    closed = wins + losses
    wr = (wins / closed) if closed else 0.0
    if gross_loss > 0:
        pf = gross_profit / gross_loss
    elif gross_profit > 0:
        pf = 999.0
    else:
        pf = 0.0
    return wr, pf


class MetricsEngine:
    """Calcula MetricsResult inmutable desde SimulationResult."""

    def __init__(self, *, periods_per_year: float = 252.0) -> None:
        self._periods = periods_per_year

    def compute(self, result: SimulationResult) -> MetricsResult:
        rets = equity_returns(result.equity_curve)
        wr, pf = win_rate_and_profit_factor(result)
        start_eq = float(result.equity_curve[0].equity) if result.equity_curve else 0.0
        end_eq = float(result.equity_curve[-1].equity) if result.equity_curve else 0.0
        total_return = ((end_eq - start_eq) / start_eq) if start_eq else 0.0
        metrics: dict[str, float | int | str] = {
            "sharpe": round(sharpe_ratio(rets, periods_per_year=self._periods), 6),
            "sortino": round(sortino_ratio(rets, periods_per_year=self._periods), 6),
            "calmar": round(calmar_ratio(result.equity_curve, periods_per_year=self._periods), 6),
            "max_drawdown": round(max_drawdown(result.equity_curve), 6),
            "win_rate": round(wr, 6),
            "profit_factor": round(pf, 6),
            "total_return": round(total_return, 6),
            "n_bars": len(result.equity_curve),
            "n_fills": len(result.fills),
            "final_equity": str(result.equity_curve[-1].equity) if result.equity_curve else "0",
        }
        return MetricsResult(
            experiment_id=result.experiment_id,
            metrics=metrics,
            computed_at=datetime.now(tz=UTC),
            metrics_version=METRICS_VERSION,
            benchmarks=None,
        )
