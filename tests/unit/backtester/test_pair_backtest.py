"""Tests pair spread backtest engine."""

from __future__ import annotations

import random

from quantlab.backtester.pair_engine import run_spread_backtest


def test_spread_backtest_produces_returns() -> None:
    random.seed(1)
    n = 200
    spread = [0.0]
    for _ in range(n - 1):
        spread.append(spread[-1] * 0.92 + random.gauss(0, 0.03))
    a = [100.0 * (2.718**s) for s in spread]
    b = [100.0] * n
    bt = run_spread_backtest(tuple(a), tuple(b), entry_z=1.2, exit_z=0.4)
    assert len(bt.net_returns) > 0
    assert bt.n_trades >= 1
