"""Autoevaluación F6 — contabilidad, golden, facade 5A."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from quantlab.backtester import (
    BarBacktestConfig,
    BarBacktester,
    assert_accounting_balanced,
)
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.research.strategies.buy_once import BuyOnceStrategy
from quantlab.research.strategies.simple_momentum import SimpleMomentumStrategy


def _bars(n: int = 8) -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 7, 1, tzinfo=UTC)
    for i in range(n):
        c = Decimal(200 + i)
        t0 = base + timedelta(minutes=i)
        out.append(
            Bar(
                instrument_id="N6:X",
                open=c,
                high=c + Decimal("2"),
                low=c - Decimal("2"),
                close=c,
                volume=Decimal("50"),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(minutes=1),
                timeframe="1m",
            )
        )
    return out


def test_accounting_rejects_empty_snapshots() -> None:
    from quantlab.core.types.results import EquityPoint, SimulationResult

    ts = datetime(2024, 1, 1, tzinfo=UTC)
    empty = SimulationResult(
        experiment_id="e",
        equity_curve=(EquityPoint(ts, Decimal("1")),),
        fills=(),
        orders=(),
        portfolio_snapshots=(),
        events_log=(),
    )
    with pytest.raises(ValidationError):
        assert_accounting_balanced(empty, initial_cash=Decimal("1"))


def test_momentum_roundtrip_accounting() -> None:
    # Up then down to force buy+sell
    base = datetime(2024, 7, 1, tzinfo=UTC)
    closes = [10, 11, 12, 13, 12, 11, 10, 9]
    bars: list[Bar] = []
    for i, c0 in enumerate(closes):
        c = Decimal(c0)
        t0 = base + timedelta(minutes=i)
        bars.append(
            Bar(
                instrument_id="N6:M",
                open=c,
                high=c + Decimal("1"),
                low=c - Decimal("1"),
                close=c,
                volume=Decimal("10"),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(minutes=1),
                timeframe="1m",
            )
        )
    bt = BarBacktester(BarBacktestConfig(experiment_id="n6-mom", initial_cash=Decimal("100000")))
    result = bt.run(SimpleMomentumStrategy({"lookback": 2, "quantity": "1"}), bars)
    assert result.accounting.ok
    assert result.simulation.metadata.get("fill_model") == "fill.immediate_bar.v1"


def test_dual_run_identical_fingerprint() -> None:
    from quantlab.backtester.golden import build_golden, fingerprint_hash, simulation_fingerprint

    bt = BarBacktester(BarBacktestConfig(experiment_id="n6-dup", initial_cash=Decimal("10000")))
    a = bt.run(BuyOnceStrategy({"quantity": "1"}), _bars())
    b = bt.run(BuyOnceStrategy({"quantity": "1"}), _bars())
    ha = fingerprint_hash(simulation_fingerprint(a.simulation))
    hb = fingerprint_hash(simulation_fingerprint(b.simulation))
    assert ha == hb
    ga = build_golden(name="x", simulation=a.simulation, metrics=a.metrics)
    gb = build_golden(name="x", simulation=b.simulation, metrics=b.metrics)
    assert ga.simulation_hash == gb.simulation_hash
    assert ga.metrics_hash == gb.metrics_hash
