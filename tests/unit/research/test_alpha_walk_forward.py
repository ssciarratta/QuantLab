"""Walk-forward split rank ≠ backtest."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from quantlab.core.types.market import Bar
from quantlab.research.alpha.walk_forward import split_bars_walk_forward


def _bars(sym: str, n: int) -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 1, 1, tzinfo=UTC)
    for i in range(n):
        c = Decimal(100 + i)
        t0 = base + timedelta(hours=i)
        out.append(
            Bar(
                instrument_id=f"BN:{sym}",
                open=c,
                high=c + Decimal("1"),
                low=c - Decimal("0.5"),
                close=c,
                volume=Decimal("1000"),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(hours=1),
                timeframe="1h",
            )
        )
    return out


def test_split_no_overlap() -> None:
    bars = {"BN:A": _bars("A", 100), "BN:B": _bars("B", 100)}
    split = split_bars_walk_forward(bars, rank_fraction=0.7)
    assert split.n_rank == 70
    assert split.n_backtest == 30
    for iid in bars:
        rank_ts = {b.timestamp_close for b in split.rank_bars[iid]}
        bt_ts = {b.timestamp_close for b in split.backtest_bars[iid]}
        assert rank_ts.isdisjoint(bt_ts)
        assert max(rank_ts) < min(bt_ts)


def test_split_rejects_short_series() -> None:
    bars = {"BN:A": _bars("A", 10)}
    with pytest.raises(ValueError, match="insuficiente"):
        split_bars_walk_forward(bars, min_rank_bars=8, min_backtest_bars=8)
