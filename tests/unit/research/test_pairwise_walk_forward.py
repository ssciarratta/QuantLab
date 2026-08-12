"""Walk-forward con embargo para pairwise."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from quantlab.core.types.market import Bar
from quantlab.research.alpha.validation.walk_forward_eval import walk_forward_with_embargo


def _bars(n: int) -> tuple[Bar, ...]:
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    out: list[Bar] = []
    for i in range(n):
        ts_o = t0 + timedelta(hours=i)
        ts_c = t0 + timedelta(hours=i + 1)
        out.append(
            Bar(
                instrument_id="WB:X",
                open=Decimal("1"),
                high=Decimal("1"),
                low=Decimal("1"),
                close=Decimal("1"),
                volume=Decimal("1"),
                timestamp_open=ts_o,
                timestamp_close=ts_c,
                timeframe="1h",
            )
        )
    return tuple(out)


def test_walk_forward_embargo_no_overlap() -> None:
    bars = _bars(200)
    folds = walk_forward_with_embargo(
        bars,
        train_size=80,
        test_size=30,
        embargo_bars=5,
        step=30,
    )
    assert len(folds) >= 3
    for fold in folds:
        assert fold.train[-1].timestamp_close < fold.test[0].timestamp_open
