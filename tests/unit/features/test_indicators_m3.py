"""Tests indicadores técnicos — Fase 5 Oficial M3."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.features import Indicator, build_pipeline
from quantlab.features.indicators import (
    ATRIndicator,
    EMACloseIndicator,
    RSIWilderIndicator,
    SMACloseIndicator,
)


def _bars(closes: list[str]) -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 7, 1, tzinfo=UTC)
    for i, c_str in enumerate(closes):
        c = Decimal(c_str)
        t0 = base + timedelta(minutes=i)
        out.append(
            Bar(
                instrument_id="FEAT:IND",
                open=c,
                high=c + Decimal("2"),
                low=c - Decimal("2"),
                close=c,
                volume=Decimal("100"),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(minutes=1),
                timeframe="1m",
            )
        )
    return out


def test_sma_close_and_pipeline() -> None:
    ind = SMACloseIndicator(window=3)
    assert isinstance(ind, Indicator)
    bars = _bars(["10", "20", "30", "40"])
    series = ind.transform(bars)
    assert series.points[0].value == Decimal("20")  # (10+20+30)/3
    frame = build_pipeline(ind, name="ind_pipe").run(bars)
    assert "sma_close_3" in frame.series


def test_ema_close_monotonic_on_uptrend() -> None:
    series = EMACloseIndicator(window=3).transform(_bars(["10", "20", "30", "40"]))
    values = [p.value for p in series.points]
    assert values[0] == Decimal("10")
    assert values[-1] > values[0]


def test_rsi_bounds() -> None:
    # tendencia alcista fuerte
    closes = [str(100 + i) for i in range(20)]
    series = RSIWilderIndicator(period=5).transform(_bars(closes))
    assert series.points
    for p in series.points:
        assert Decimal("0") <= p.value <= Decimal("100")


def test_atr_positive() -> None:
    series = ATRIndicator(period=3).transform(_bars(["10", "12", "11", "13", "14"]))
    assert series.points
    assert all(p.value > 0 for p in series.points)


def test_rsi_rejects_small_period() -> None:
    with pytest.raises(ValidationError):
        RSIWilderIndicator(period=1)


def test_indicators_no_lookahead_prefix() -> None:
    bars = _bars([str(100 + i) for i in range(10)])
    ind = SMACloseIndicator(window=3)
    s_short = ind.transform(bars[:5])
    s_long = ind.transform(bars)
    assert s_short.points == s_long.points[: len(s_short.points)]
