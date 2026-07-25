"""Bloque 3 — downsampling equity, métricas masivas, create_batch registry."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.results import EquityPoint, MetricsResult, SimulationResult
from quantlab.experiments import ExperimentRegistry
from quantlab.reporting import ReportGenerator, downsample_equities


def test_downsample_10000_points_keeps_ends() -> None:
    eqs = [float(i) for i in range(10_000)]
    sampled = downsample_equities(eqs, max_points=100)
    assert len(sampled) == 100
    assert sampled[0] == 0.0
    assert sampled[-1] == 9999.0
    # Distribución uniforme: índices crecientes
    assert sampled == sorted(sampled)


def test_downsample_short_series_unchanged() -> None:
    eqs = [1.0, 2.0, 3.0]
    assert downsample_equities(eqs, max_points=100) == eqs


def test_downsample_rejects_max_points_lt_2() -> None:
    with pytest.raises(ValidationError):
        downsample_equities([1.0, 2.0], max_points=1)


def test_report_uses_downsampled_equity_bars(tmp_path: Path) -> None:
    n = 500
    base = datetime(2024, 1, 1, tzinfo=UTC)
    curve = tuple(
        EquityPoint(timestamp=base + timedelta(minutes=i), equity=Decimal(1000 + i))
        for i in range(n)
    )
    sim = SimulationResult(
        experiment_id="b3-eq",
        equity_curve=curve,
        fills=(),
        orders=(),
        portfolio_snapshots=(),
        events_log=(),
        metadata={},
    )
    metrics = MetricsResult(
        experiment_id="b3-eq",
        metrics={"sharpe": 1.2, "max_drawdown": 0.1},
        computed_at=datetime.now(tz=UTC),
        metrics_version="1.0",
    )
    gen = ReportGenerator(tmp_path / "reports")
    result = gen.generate(metrics=metrics, simulation=sim, max_equity_points=80)
    html = Path(result.path).read_text(encoding="utf-8")
    bar_count = html.count('class="bar"')
    assert bar_count == 80
    assert "500 puntos → 80 mostrados" in html


def test_report_metrics_scroll_and_max_rows(tmp_path: Path) -> None:
    metrics_map = {f"metric_{i:04d}": float(i) for i in range(200)}
    metrics_map["sharpe"] = 1.5
    metrics = MetricsResult(
        experiment_id="b3-met",
        metrics=metrics_map,
        computed_at=datetime.now(tz=UTC),
        metrics_version="1.0",
    )
    gen = ReportGenerator(tmp_path / "reports")
    result = gen.generate(
        metrics=metrics,
        max_table_rows=20,
        primary_metrics=("sharpe",),
    )
    html = Path(result.path).read_text(encoding="utf-8")
    assert "overflow-y: auto" in html
    assert "Métricas principales" in html
    assert "sharpe" in html
    assert "métricas adicionales omitidas" in html


def test_create_batch_single_transaction(tmp_path: Path) -> None:
    reg = ExperimentRegistry(tmp_path / "exp.sqlite")
    payload = [
        {
            "experiment_id": f"grid-{i:03d}",
            "dataset_id": "ds-1",
            "strategy_version": "v1",
            "metadata": {"i": i},
        }
        for i in range(25)
    ]
    created = reg.create_batch(payload)
    assert len(created) == 25
    assert len(reg.list()) == 25
    assert reg.get("grid-000") is not None
    assert reg.get("grid-024") is not None
    sidecar = tmp_path / "exp_records" / "grid-010.json"
    assert sidecar.is_file()


def test_create_batch_rejects_existing(tmp_path: Path) -> None:
    reg = ExperimentRegistry(tmp_path / "exp.sqlite")
    reg.create(experiment_id="dup", dataset_id="d", strategy_version="v1")
    with pytest.raises(ValidationError, match="ya existe"):
        reg.create_batch(
            [
                {
                    "experiment_id": "dup",
                    "dataset_id": "d",
                    "strategy_version": "v1",
                }
            ]
        )


def test_create_individual_still_works(tmp_path: Path) -> None:
    reg = ExperimentRegistry(tmp_path / "exp.sqlite")
    rec = reg.create(experiment_id="one", dataset_id="d", strategy_version="v1")
    assert rec.experiment_id == "one"
    assert reg.get("one") is not None
