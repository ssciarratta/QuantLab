"""Tests corrección Monte Carlo: límites, batching, dataset, anti-huérfano."""

from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.montecarlo.cancel import CancellationToken
from quantlab.montecarlo.dataset import DatasetReference
from quantlab.montecarlo.limits import (
    MAX_SCENARIOS,
    MIN_SCENARIOS,
    estimate_cost,
    storage_mode_for,
    validate_n_scenarios,
)
from quantlab.montecarlo.simulator import MonteCarloSimulator
from quantlab.workbench import lab_services
from quantlab.workbench.lab_services import make_synthetic_bars
from quantlab.backtester import BarBacktestConfig, BarBacktester
from quantlab.research.strategies.buy_once import BuyOnceStrategy
from decimal import Decimal


def _runner_factory(initial: Decimal = Decimal("50000")):
    def runner(noisy):  # type: ignore[no-untyped-def]
        bt = BarBacktester(BarBacktestConfig(experiment_id="t", initial_cash=initial))
        return bt.run(BuyOnceStrategy({"quantity": "1"}), noisy).simulation

    return runner


@pytest.mark.parametrize("n", [2, 20, 100, 1000])
def test_n_scenarios_accepted(n: int) -> None:
    validate_n_scenarios(n)


def test_n_scenarios_rejects_zero_negative_over_max() -> None:
    with pytest.raises(ValidationError):
        validate_n_scenarios(0)
    with pytest.raises(ValidationError):
        validate_n_scenarios(-1)
    with pytest.raises(ValidationError):
        validate_n_scenarios(MAX_SCENARIOS + 1)


def test_n_scenarios_rejects_bool() -> None:
    with pytest.raises(ValidationError):
        validate_n_scenarios(True)  # type: ignore[arg-type]


def test_storage_mode_threshold() -> None:
    assert storage_mode_for(10_000) == "full_equities"
    assert storage_mode_for(10_001) == "summary_and_sample"


def test_batching_reproducible_and_complete() -> None:
    bars = make_synthetic_bars(12)
    r1 = MonteCarloSimulator(seed=7).run(
        bars, _runner_factory(), n_scenarios=50, batch_size=10, initial_equity=50000.0
    )
    r2 = MonteCarloSimulator(seed=7).run(
        bars, _runner_factory(), n_scenarios=50, batch_size=25, initial_equity=50000.0
    )
    assert r1.n_scenarios_completed == 50
    assert r1.mean_equity == pytest.approx(r2.mean_equity)
    assert r1.final_equities == r2.final_equities


def test_trajectories_cap_independent_of_n() -> None:
    bars = make_synthetic_bars(10)
    r = MonteCarloSimulator(seed=1).run(
        bars,
        _runner_factory(),
        n_scenarios=40,
        store_paths=True,
        max_paths_stored=16,
        initial_equity=50000.0,
    )
    assert r.n_scenarios == 40
    assert r.equity_paths is not None
    assert len(r.equity_paths) <= 16


def test_cancel_marks_partial() -> None:
    bars = make_synthetic_bars(10)
    token = CancellationToken()
    # cancel immediately after start via progress
    def on_progress(p: dict) -> None:  # type: ignore[type-arg]
        if p.get("completed", 0) >= 5:
            token.cancel()

    r = MonteCarloSimulator(seed=3).run(
        bars,
        _runner_factory(),
        n_scenarios=40,
        batch_size=5,
        cancellation=token,
        on_progress=on_progress,
        progress_interval=1,
        initial_equity=50000.0,
    )
    assert r.partial is True
    assert r.status == "cancelled"
    assert (r.n_scenarios_completed or 0) < 40


def test_dataset_reference_synthetic() -> None:
    bars = make_synthetic_bars(16)
    ref = DatasetReference.from_synthetic_bars(bars, dataset_hash="abc", seed=42)
    d = ref.to_dict()
    assert d["synthetic"] is True
    assert d["symbol"] == "WB:SYN"
    assert d["bars"] == 16
    assert d["timeframe"] == "1m"
    assert d["duration_label"]


def test_lab_technical_has_full_context(tmp_path: Path) -> None:
    out = lab_services.run_lab_montecarlo(
        n_scenarios=5,
        n_bars=12,
        seed=2,
        persist=False,
        montecarlo_root=tmp_path,
        mode="technical_lab",
    )
    assert out["initial_equity"] == 50000.0
    assert out["equity_currency"] == "LAB"
    assert out["dataset"]["dataset_id"] == "wb-synthetic"
    ctx = out["context"]
    assert ctx["strategy_id"]
    assert ctx["symbols"]
    assert ctx["venue"] == "lab"
    assert ctx["timeframe"] == "1m"
    assert ctx["initial_equity"] == 50000.0
    assert out["bars_meta"]["label_es"] == "Velas utilizadas por escenario"


def test_lab_normal_rejects_orphan() -> None:
    with pytest.raises(ValidationError, match="backtest_id"):
        lab_services.run_lab_montecarlo(
            n_scenarios=5,
            n_bars=12,
            persist=False,
            mode="normal",
        )


def test_lab_large_requires_confirm() -> None:
    with pytest.raises(ValidationError, match="confirm_large"):
        lab_services.run_lab_montecarlo(
            n_scenarios=100_000,
            n_bars=12,
            persist=False,
            mode="technical_lab",
            confirm_large=False,
        )


def test_estimate_cost_shape() -> None:
    est = estimate_cost(n_scenarios=10_000, n_bars=60, store_paths=True)
    assert est["approx_bar_operations"] == 600_000
    assert est["approximation"] is True


def test_lab_2k_runs_and_reports_storage(tmp_path: Path) -> None:
    out = lab_services.run_lab_montecarlo(
        n_scenarios=2_000,
        n_bars=8,
        seed=1,
        persist=False,
        montecarlo_root=tmp_path,
        confirm_large=False,
        batch_size=500,
    )
    assert out["n_scenarios_completed"] == 2_000
    assert out["storage_mode"] == "full_equities"
    assert out["mean_equity"] is not None
