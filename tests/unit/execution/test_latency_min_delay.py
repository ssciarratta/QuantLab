"""Tests TD-05 — min_delay wall-clock en FixedLatencyModel."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.execution import FixedLatencyModel
from quantlab.research.strategies.buy_once import BuyOnceStrategy
from quantlab.simulation import BarSimulationEngine, SimulationConfig


def _bar(i: int, close: str = "100") -> Bar:
    t0 = datetime(2024, 1, 1, tzinfo=UTC) + timedelta(minutes=i)
    c = Decimal(close)
    return Bar(
        instrument_id="a3:TEST",
        open=c,
        high=c + Decimal("1"),
        low=c - Decimal("1"),
        close=c,
        volume=Decimal("100"),
        timestamp_open=t0,
        timestamp_close=t0 + timedelta(minutes=1),
        timeframe="1m",
    )


def test_min_delay_requires_bar_times() -> None:
    model = FixedLatencyModel(bars_delay=0, min_delay=timedelta(seconds=90))
    with pytest.raises(ValidationError, match="bar_times"):
        model.resolve(
            submit_index=0,
            submit_time=datetime(2024, 1, 1, tzinfo=UTC),
            series_length=5,
        )


def test_min_delay_advances_until_wall_clock() -> None:
    # Barras cada 60s de close relativo al submit (close de barra i = T0 + (i+1)m)
    times = [datetime(2024, 1, 1, 0, i + 1, tzinfo=UTC) for i in range(5)]
    submit = times[0]
    model = FixedLatencyModel(bars_delay=0, min_delay=timedelta(seconds=90))
    d = model.resolve(
        submit_index=0,
        submit_time=submit,
        series_length=5,
        bar_times=times,
    )
    assert d.executable
    assert d.effective_index == 2  # +120s >= 90s
    assert d.reason == "min_delay_90s_at_2"


def test_min_delay_respects_bars_delay_floor() -> None:
    times = [datetime(2024, 1, 1, 0, i + 1, tzinfo=UTC) for i in range(6)]
    model = FixedLatencyModel(bars_delay=3, min_delay=timedelta(seconds=30))
    d = model.resolve(
        submit_index=0,
        submit_time=times[0],
        series_length=6,
        bar_times=times,
    )
    assert d.executable
    assert d.effective_index == 3


def test_min_delay_beyond_series() -> None:
    times = [datetime(2024, 1, 1, 0, i + 1, tzinfo=UTC) for i in range(3)]
    model = FixedLatencyModel(bars_delay=0, min_delay=timedelta(hours=1))
    d = model.resolve(
        submit_index=0,
        submit_time=times[0],
        series_length=3,
        bar_times=times,
    )
    assert not d.executable
    assert d.reason == "min_delay_beyond_series"


def test_engine_min_delay_defers_fill() -> None:
    bars = [_bar(i) for i in range(5)]
    engine = BarSimulationEngine(
        SimulationConfig(experiment_id="e-min-delay"),
        latency_model=FixedLatencyModel(bars_delay=0, min_delay=timedelta(seconds=90)),
    )
    result = engine.run(BuyOnceStrategy({"quantity": "1"}), bars)
    assert len(result.fills) == 1
    # submit bar0 close = T0+1m; need +90s → bar2 close = T0+3m
    assert result.fills[0].timestamp == bars[2].timestamp_close
