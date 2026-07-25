"""Autoevaluación MVP Fases 7–16."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from quantlab.backtester import BarBacktestConfig, BarBacktester
from quantlab.core.types.enums import ExperimentStatus, OrderSide
from quantlab.core.types.manifests import (
    ExecutionModelVersions,
    ExperimentManifest,
)
from quantlab.core.types.market import Bar
from quantlab.data.exchanges.generic_csv import GenericCsvProvider
from quantlab.execution_export import HummingbotExporter
from quantlab.experiments import ExperimentRegistry
from quantlab.montecarlo import MonteCarloSimulator
from quantlab.optimizer import GridSearchOptimizer
from quantlab.reporting import ReportGenerator
from quantlab.research.alpha import AlphaScanner
from quantlab.research.alpha.explain import explain_scores
from quantlab.research.sizing import fixed_fractional
from quantlab.research.strategies.buy_once import BuyOnceStrategy
from quantlab.validation import check_temporal_leakage, train_val_oos_split
from quantlab.validation.splits import walk_forward


def _bars(n: int = 40) -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 9, 1, tzinfo=UTC)
    for i in range(n):
        c = Decimal(50 + i)
        t0 = base + timedelta(minutes=i)
        out.append(
            Bar(
                instrument_id="N:X",
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
    return out


def test_f8_report_html(tmp_path: Path) -> None:
    bt = BarBacktester(BarBacktestConfig(experiment_id="rep1", initial_cash=Decimal("10000")))
    run = bt.run(BuyOnceStrategy({"quantity": "1"}), _bars(10))
    gen = ReportGenerator(tmp_path / "reports")
    result = gen.generate(metrics=run.metrics, simulation=run.simulation)
    assert Path(result.path).exists()
    assert "QuantLab" in Path(result.path).read_text(encoding="utf-8")


def test_f9_registry_crud(tmp_path: Path) -> None:
    reg = ExperimentRegistry(tmp_path / "exp.sqlite")
    rec = reg.create(
        experiment_id="e1", dataset_id="ds", strategy_version="0.1.0", metadata={"a": 1}
    )
    assert rec.status is ExperimentStatus.DRAFT
    reg.link_artifact("e1", "/tmp/art.json")
    reg.set_status("e1", ExperimentStatus.COMPLETED)
    got = reg.get("e1")
    assert got is not None
    assert got.status is ExperimentStatus.COMPLETED
    assert got.artifact_paths == ("/tmp/art.json",)


def test_f10_splits_and_leakage() -> None:
    bars = _bars(50)
    split = train_val_oos_split(bars)
    assert len(split.train) + len(split.validation) + len(split.oos) == 50
    report = check_temporal_leakage(split.train, split.oos)
    assert report.ok
    folds = walk_forward(bars, train_size=20, test_size=5, step=5)
    assert len(folds) >= 1


def test_f11_montecarlo() -> None:
    from quantlab.core.types.results import SimulationResult

    bars = _bars(12)

    def runner(b: Sequence[Bar]) -> SimulationResult:
        return (
            BarBacktester(BarBacktestConfig(experiment_id="mc", initial_cash=Decimal("10000")))
            .run(BuyOnceStrategy({"quantity": "1"}), b)
            .simulation
        )

    mc = MonteCarloSimulator(seed=7).run(bars, runner, n_scenarios=8, noise_bps=5.0)
    assert mc.n_scenarios == 8
    assert mc.ci_high >= mc.ci_low


def test_f12_grid_optimizer() -> None:
    opt = GridSearchOptimizer(seed=1)
    result = opt.grid(
        {"x": [1, 2, 3], "y": [0.1, 0.2]},
        objective=lambda p: float(p["x"]) * float(p["y"]),
    )
    assert result.best.params["x"] == 3
    assert len(result.history) == 6


def _bars_id(instrument_id: str, n: int = 8) -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 9, 1, tzinfo=UTC)
    for i in range(n):
        c = Decimal(50 + i)
        t0 = base + timedelta(minutes=i)
        out.append(
            Bar(
                instrument_id=instrument_id,
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
    return out


def test_f13_explain_and_f14_sizing() -> None:
    data = {"A": _bars_id("A"), "B": _bars_id("B")}
    scan = AlphaScanner().scan(data, top_n=2)
    expl = explain_scores(scan, top=2)
    assert expl
    qty = fixed_fractional(
        Decimal("10000"), risk_fraction=Decimal("0.01"), stop_distance=Decimal("2")
    )
    assert qty == Decimal("50.00000000")


def test_f15_csv_provider(tmp_path: Path) -> None:
    csv_path = tmp_path / "t.csv"
    ts = datetime(2024, 1, 1, tzinfo=UTC).isoformat()
    csv_path.write_text(
        f"ts,price,qty,side,trade_id\n{ts},10,1,buy,t1\n",
        encoding="utf-8",
    )
    trades = GenericCsvProvider().load_trades(csv_path, instrument_id="G:X")
    assert len(trades) == 1
    assert trades[0].side is OrderSide.BUY


def test_f16_hummingbot_export_blocked(tmp_path: Path) -> None:
    now = datetime.now(tz=UTC)
    manifest = ExperimentManifest(
        experiment_id="exp-hb",
        dataset_id="ds",
        dataset_version="v1",
        resolved_config={"x": 1},
        seed=1,
        git_commit="abc",
        python_version="3.12",
        dependency_versions_or_hash="deps",
        platform="test",
        strategy_version="0.1.0",
        execution_model_versions=ExecutionModelVersions(
            fee_model="f", slippage_model="s", latency_model="l", fill_model="m"
        ),
        artifacts_produced=(),
        created_at=now,
        checksum="a" * 64,
    )
    exporter = HummingbotExporter()
    assert exporter.LIVE_BLOCKED is True
    pkg = exporter.build_execution_package(manifest)
    assert pkg.payload["live_routing"] is False
    out = exporter.export_configuration(pkg, tmp_path / "hb.json")
    assert Path(out.path).exists()
