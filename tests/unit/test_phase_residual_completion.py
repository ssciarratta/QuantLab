"""Suite de control — residuos F10 / F12 / F14 / F17 (API de auditoría)."""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from quantlab.backtester import ParallelBacktester, SimJob
from quantlab.core.types.results import MetricsResult
from quantlab.execution import LIVE_BLOCKED, LiveOrderRouter
from quantlab.optimizer import compute_pareto_frontier
from quantlab.research.strategies import quote_prices
from quantlab.validation import adjust_pvalues, filter_significant


def test_adjust_pvalues_bonferroni_holm_fdr() -> None:
    ps = [0.01, 0.04, 0.03, 0.20]
    b = adjust_pvalues(ps, method="bonferroni")
    assert b[0] == pytest.approx(0.04)
    assert b[3] == pytest.approx(0.80)
    h = adjust_pvalues(ps, method="holm")
    assert len(h) == 4
    assert all(0.0 <= x <= 1.0 for x in h)
    fdr = adjust_pvalues(ps, method="fdr_bh")
    assert len(fdr) == 4
    # FDR BH no debe ser más estricto que Bonferroni en el menor p
    assert fdr[0] <= b[0] + 1e-12


def test_filter_significant_after_correction() -> None:
    labels = ("A", "B", "C", "D")
    ps = [0.001, 0.02, 0.04, 0.50]
    kept = filter_significant(labels, ps, method="bonferroni", alpha=0.05)
    assert "A" in kept
    assert "D" not in kept


def test_compute_pareto_frontier_sharpe_vs_mdd() -> None:
    now = datetime.now(tz=UTC)

    def mr(eid: str, sharpe: float, mdd: float) -> MetricsResult:
        return MetricsResult(
            experiment_id=eid,
            metrics={"sharpe": sharpe, "max_drawdown": mdd},
            computed_at=now,
            metrics_version="1.0",
        )

    results = (
        mr("r1", 1.0, 0.20),
        mr("r2", 0.5, 0.05),
        mr("r3", 0.2, 0.40),  # dominado
        mr("r4", 0.9, 0.08),
    )
    front = compute_pareto_frontier(
        results,
        objectives=(("sharpe", "max"), ("max_drawdown", "min")),
    )
    ids = {r.experiment_id for r in front}
    assert "r3" not in ids
    assert len(front) >= 2


def test_avellaneda_inventory_shifts_quotes() -> None:
    mid = 100.0
    _, bid0, ask0 = quote_prices(mid=mid, inventory=0.0, tau=1.0)
    _, bid_long, ask_long = quote_prices(mid=mid, inventory=5.0, tau=1.0)
    # Inventario largo → reservation baja → bid/ask más bajos
    assert bid_long < bid0
    assert ask_long < ask0
    assert isinstance(bid0, Decimal)
    assert ask0 > bid0


def test_live_blocked_invariant() -> None:
    assert LIVE_BLOCKED is True
    with pytest.raises(Exception, match="BLOQUEADO"):
        LiveOrderRouter()


def test_parallel_backtester_faster_or_competitive(tmp_path: Path) -> None:
    jobs = tuple(
        SimJob(job_id=i, params={"seed": i, "work": 80_000}) for i in range(12)
    )
    bt = ParallelBacktester(max_workers=min(4, os.cpu_count() or 2))
    seq = bt.run_sequential(jobs)
    par = bt.run(jobs, export_parquet_dir=tmp_path / "pq")
    assert seq.n_jobs == par.n_jobs == 12
    assert len(par.results) == 12
    assert par.results[0]["job_id"] == 0
    assert par.results[0]["live_blocked"] is True
    # Misma semántica que secuencial
    assert [r["score"] for r in par.results] == [r["score"] for r in seq.results]
    assert par.parquet_path is not None
    assert Path(par.parquet_path).is_file()
    assert par.elapsed_seconds > 0
    assert seq.elapsed_seconds > 0
    # Windows usa spawn: overhead de procesos domina jobs cortos.
    # En fork (Linux/mac) + multi-core exigimos competitive vs secuencial.
    if sys.platform != "win32" and (os.cpu_count() or 1) >= 2:
        assert par.elapsed_seconds <= seq.elapsed_seconds * 1.5
    else:
        assert par.workers >= 1
