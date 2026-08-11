"""Validación 5A de timeframe con close_time de exchange (−1ms)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from quantlab.backtester.bar_based import BarBacktestConfig, BarBacktester
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar


def _bar(*, open_ts: datetime, close_ts: datetime, timeframe: str = "1m") -> Bar:
    return Bar(
        instrument_id="BN:BTCUSDT",
        open=Decimal("1"),
        high=Decimal("1"),
        low=Decimal("1"),
        close=Decimal("1"),
        volume=Decimal("1"),
        timestamp_open=open_ts,
        timestamp_close=close_ts,
        timeframe=timeframe,
    )


def test_5a_accepts_binance_style_1m_close_minus_1ms() -> None:
    """close = open + 60s − 1ms (convención klines) no debe fallar el mínimo 1m."""
    t0 = datetime(2026, 7, 28, 12, 0, 0, tzinfo=UTC)
    t1 = t0 + timedelta(milliseconds=59_999)
    bt = BarBacktester(BarBacktestConfig(experiment_id="t-1m-tol"))
    # No corremos estrategia: solo validación
    bt._validate_bars_5a([_bar(open_ts=t0, close_ts=t1)])  # noqa: SLF001


def test_5a_rejects_true_sub_minute_bars() -> None:
    t0 = datetime(2026, 7, 28, 12, 0, 0, tzinfo=UTC)
    t1 = t0 + timedelta(seconds=30)
    bt = BarBacktester(BarBacktestConfig(experiment_id="t-sub-1m"))
    with pytest.raises(ValidationError, match="timeframe de barra"):
        bt._validate_bars_5a([_bar(open_ts=t0, close_ts=t1, timeframe="30s")])  # noqa: SLF001
