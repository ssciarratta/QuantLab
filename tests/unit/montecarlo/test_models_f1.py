"""Tests contratos Monte Carlo (FASE 1)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.core.types.results import EquityPoint, SimulationResult
from quantlab.montecarlo import (
    IMPLEMENTED_METHODS,
    METHOD_DISCLAIMER,
    MonteCarloConfig,
    MonteCarloExperimentContext,
    MonteCarloMethod,
    MonteCarloSimulator,
    unavailable_label,
)


def _bar(i: int) -> Bar:
    t0 = datetime(2024, 6, 1, tzinfo=UTC)
    from datetime import timedelta

    c = Decimal(100 + i)
    ts = t0 + timedelta(minutes=i)
    return Bar(
        instrument_id="WB:SYN",
        open=c,
        high=c + 1,
        low=c - 1,
        close=c,
        volume=Decimal(10),
        timestamp_open=ts,
        timestamp_close=ts + timedelta(minutes=1),
        timeframe="1m",
    )


def _runner(bars: list[Bar]) -> SimulationResult:
    # equity final ≈ 1000 + close[-1] (determinista, sensible a shock)
    last = float(bars[-1].close) if bars else 0.0
    eq = 1000.0 + last
    t = bars[-1].timestamp_close if bars else datetime(2024, 6, 1, tzinfo=UTC)
    return SimulationResult(
        experiment_id="t",
        equity_curve=(EquityPoint(timestamp=t, equity=Decimal(str(eq))),),
        fills=(),
        orders=(),
        portfolio_snapshots=(),
        events_log=(),
    )


def test_only_implemented_method_exposed() -> None:
    assert MonteCarloMethod.PRICE_SHOCK_RERUN in IMPLEMENTED_METHODS
    assert list(IMPLEMENTED_METHODS) == [MonteCarloMethod.PRICE_SHOCK_RERUN]


def test_context_null_not_zero_sentinel() -> None:
    ctx = MonteCarloExperimentContext()
    d = ctx.to_dict()
    assert d["initial_equity"] is None
    assert d["scan_id"] is None
    assert d["strategy_id"] is None
    assert unavailable_label() == "No disponible"
    roundtrip = MonteCarloExperimentContext.from_dict(d)
    assert roundtrip.initial_equity is None
    assert roundtrip.symbols is None


def test_config_rejects_unimplemented_bootstrap() -> None:
    with pytest.raises(ValidationError, match="bootstrap"):
        MonteCarloConfig(bootstrap_block_size=5)


def test_config_bar_horizon_label() -> None:
    cfg = MonteCarloConfig(n_bars=16, n_scenarios=5)
    label = cfg.bar_horizon_label("1m")
    assert "16 velas" in label
    assert "1m" in label
    assert "16 min" in label
    assert METHOD_DISCLAIMER in cfg.disclaimer


def test_simulator_accepts_config_and_metrics() -> None:
    bars = [_bar(i) for i in range(8)]
    cfg = MonteCarloConfig(n_scenarios=4, n_bars=8, seed=7, noise_bps=5.0)
    mc = MonteCarloSimulator(seed=0)
    result = mc.run(bars, _runner, config=cfg, initial_equity=1000.0)
    assert result.seed == 7
    assert result.n_scenarios == 4
    assert result.method == MonteCarloMethod.PRICE_SHOCK_RERUN
    assert result.metrics is not None
    assert result.metrics.ci_kind == "wald_mean"
    assert result.metrics.finals_only is True
    assert result.metrics.max_drawdown_mean is None
    assert result.metrics.mean_return_pct is not None
    assert result.ci_high >= result.ci_low


def test_as_of_time_blocks_lookahead() -> None:
    bars = [_bar(i) for i in range(4)]
    as_of = bars[1].timestamp_close
    cfg = MonteCarloConfig(n_scenarios=2, n_bars=4, as_of_time=as_of)
    with pytest.raises(ValidationError, match="look-ahead"):
        MonteCarloSimulator(seed=1).run(bars, _runner, config=cfg)


def test_seed_reproducible_with_config() -> None:
    bars = [_bar(i) for i in range(6)]
    cfg = MonteCarloConfig(n_scenarios=3, n_bars=6, seed=99, noise_bps=8.0)
    a = MonteCarloSimulator().run(bars, _runner, config=cfg)
    b = MonteCarloSimulator().run(bars, _runner, config=cfg)
    assert a.final_equities == b.final_equities
