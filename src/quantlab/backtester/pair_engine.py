"""Backtest research de spread long-short (2 piernas)."""

from __future__ import annotations

from dataclasses import dataclass

from quantlab.research.alpha.pairwise.stats import (
    log_spread,
    ols_hedge_ratio,
    spread_zscore,
)


@dataclass(frozen=True, slots=True)
class SpreadBacktestResult:
    net_returns: tuple[float, ...]
    n_trades: int
    total_fee_drag: float


def run_spread_backtest(
    closes_a: tuple[float, ...],
    closes_b: tuple[float, ...],
    *,
    z_window: int = 48,
    entry_z: float = 2.0,
    exit_z: float = 0.5,
    fee_bps_per_leg: float = 10.0,
    hedge_ratio: float | None = None,
) -> SpreadBacktestResult:
    """Simula mean-reversion sobre spread log con fees round-trip conservadores.

    ``hedge_ratio`` fijo (p.ej. estimado en train) evita reestimar β en el tramo OOS.
    """
    if len(closes_a) < z_window + 5 or len(closes_b) < z_window + 5:
        return SpreadBacktestResult(net_returns=(), n_trades=0, total_fee_drag=0.0)

    beta = (
        float(hedge_ratio)
        if hedge_ratio is not None
        else ols_hedge_ratio(list(closes_a), list(closes_b))
    )
    spread = log_spread(list(closes_a), list(closes_b), beta)
    zs = spread_zscore(spread, z_window)
    if len(zs) < 3:
        return SpreadBacktestResult(net_returns=(), n_trades=0, total_fee_drag=0.0)

    fee = fee_bps_per_leg / 10000.0
    round_trip = fee * 4  # open/close 2 legs
    position = 0  # +1 long spread, -1 short spread
    returns: list[float] = []
    n_trades = 0
    fee_drag = 0.0
    offset = len(spread) - len(zs)

    for i in range(1, len(zs)):
        z_prev = zs[i - 1]
        spr_prev = spread[offset + i - 1]
        spr_cur = spread[offset + i]
        spread_ret = spr_cur - spr_prev

        if position == 0 and z_prev <= -entry_z:
            position = 1
            n_trades += 1
            fee_drag += round_trip
        elif position == 0 and z_prev >= entry_z:
            position = -1
            n_trades += 1
            fee_drag += round_trip
        elif position != 0 and abs(z_prev) <= exit_z:
            position = 0
            n_trades += 1
            fee_drag += round_trip

        if position != 0:
            bar_ret = position * spread_ret - (round_trip if n_trades and i == 1 else 0)
            returns.append(bar_ret)

    return SpreadBacktestResult(
        net_returns=tuple(returns),
        n_trades=n_trades,
        total_fee_drag=fee_drag,
    )
