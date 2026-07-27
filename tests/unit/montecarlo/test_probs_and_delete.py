"""Tests métricas de probabilidad y DELETE Monte Carlo (UX pendientes)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.core.types.results import EquityPoint, SimulationResult
from quantlab.montecarlo.models import MonteCarloConfig
from quantlab.montecarlo.simulator import MonteCarloSimulator
from quantlab.montecarlo.traceability import normalize_montecarlo_payload
from quantlab.workbench import lab_services
from quantlab.workbench.api import (
    ApiError,
    WorkbenchState,
    handle_delete_lab_montecarlo_run,
    handle_get_lab_montecarlo_history,
    handle_get_lab_montecarlo_run,
    handle_post_lab_montecarlo,
)
from quantlab.workbench.montecarlo_runs import delete_montecarlo_run
from quantlab.workbench.session import WorkbenchSession


def _bar(i: int) -> Bar:
    t0 = datetime(2024, 6, 1, tzinfo=UTC)
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


def test_outcome_probs_from_finals() -> None:
    """prob_profit / prob_loss / prob_above_initial desde equities + initial."""
    finals_cycle = [900.0, 1000.0, 1100.0, 1200.0]  # loss, flat, profit, profit

    def runner(bars: list[Bar]) -> SimulationResult:
        idx = runner.i  # type: ignore[attr-defined]
        runner.i = idx + 1  # type: ignore[attr-defined]
        eq = finals_cycle[idx % len(finals_cycle)]
        t = bars[-1].timestamp_close if bars else datetime(2024, 6, 1, tzinfo=UTC)
        return SimulationResult(
            experiment_id="t",
            equity_curve=(EquityPoint(timestamp=t, equity=Decimal(str(eq))),),
            fills=(),
            orders=(),
            portfolio_snapshots=(),
            events_log=(),
        )

    runner.i = 0  # type: ignore[attr-defined]
    bars = [_bar(i) for i in range(4)]
    cfg = MonteCarloConfig(n_scenarios=4, n_bars=4, seed=1, noise_bps=0.0)
    result = MonteCarloSimulator(seed=1).run(
        bars, runner, config=cfg, initial_equity=1000.0
    )
    assert result.metrics is not None
    assert result.final_equities == (900.0, 1000.0, 1100.0, 1200.0)
    assert result.metrics.prob_profit == pytest.approx(0.5)  # 2/4 >
    assert result.metrics.prob_loss == pytest.approx(0.25)  # 1/4 <
    assert result.metrics.prob_above_initial == pytest.approx(0.75)  # 3/4 >=


def test_probs_none_without_initial_equity() -> None:
    bars = [_bar(i) for i in range(4)]

    def runner(bars_: list[Bar]) -> SimulationResult:
        t = bars_[-1].timestamp_close
        return SimulationResult(
            experiment_id="t",
            equity_curve=(EquityPoint(timestamp=t, equity=Decimal("1000")),),
            fills=(),
            orders=(),
            portfolio_snapshots=(),
            events_log=(),
        )

    cfg = MonteCarloConfig(n_scenarios=2, n_bars=4, seed=3, noise_bps=0.0)
    result = MonteCarloSimulator().run(bars, runner, config=cfg, initial_equity=None)
    assert result.metrics is not None
    assert result.metrics.prob_profit is None
    assert result.metrics.prob_loss is None
    assert result.metrics.prob_above_initial is None


def test_normalize_fills_probs_for_legacy_with_initial() -> None:
    legacy = {
        "schema_version": 1,
        "final_equities": [90.0, 100.0, 110.0],
        "initial_equity": 100.0,
        "mean_equity": 100.0,
        "n_bars": 8,
        "n_scenarios": 3,
        "seed": 1,
        "ok": True,
        "run_id": "mc-legacy-probs",
    }
    norm = normalize_montecarlo_payload(legacy)
    m = norm["metrics"]
    assert m["prob_profit"] == pytest.approx(1 / 3)
    assert m["prob_loss"] == pytest.approx(1 / 3)
    assert m["prob_above_initial"] == pytest.approx(2 / 3)
    assert norm["schema_version"] == 1


def test_normalize_v1_without_initial_keeps_null_probs() -> None:
    legacy = {
        "schema_version": 1,
        "final_equities": [50013.5, 50014.0],
        "mean_equity": 50013.75,
        "n_bars": 16,
        "n_scenarios": 2,
        "seed": 42,
        "ok": True,
        "run_id": "mc-legacy",
    }
    norm = normalize_montecarlo_payload(legacy)
    assert norm["schema_version"] == 1
    assert norm["metrics"].get("prob_profit") is None


def test_lab_payload_includes_probs() -> None:
    out = lab_services.run_lab_montecarlo(
        n_scenarios=3, n_bars=10, seed=11, persist=False
    )
    m = out["metrics"]
    assert m["prob_profit"] is not None
    assert m["prob_loss"] is not None
    assert m["prob_above_initial"] is not None
    assert 0.0 <= m["prob_profit"] <= 1.0
    assert 0.0 <= m["prob_loss"] <= 1.0
    assert 0.0 <= m["prob_above_initial"] <= 1.0
    # flat = above - profit; profit + loss + flat == 1
    assert m["prob_profit"] + m["prob_loss"] <= 1.0 + 1e-9
    assert m["prob_above_initial"] + m["prob_loss"] == pytest.approx(1.0)


def test_delete_api_handler(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "mc-del")
    state = WorkbenchState(session=session)
    run = handle_post_lab_montecarlo(state, {"n_scenarios": 2, "n_bars": 8, "seed": 5})
    rid = run["run_id"]
    assert rid
    loaded = handle_get_lab_montecarlo_run(state, rid)
    assert loaded["run_id"] == rid
    deleted = handle_delete_lab_montecarlo_run(state, rid)
    assert deleted["ok"] is True
    assert deleted["kind"] == "montecarlo_deleted"
    hist = handle_get_lab_montecarlo_history(state)
    assert hist["count"] == 0
    with pytest.raises(ApiError) as exc:
        handle_get_lab_montecarlo_run(state, rid)
    assert exc.value.status == 404


def test_delete_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="no encontrado"):
        delete_montecarlo_run(tmp_path, "mc-no-existe-xyz")
