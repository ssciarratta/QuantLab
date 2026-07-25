"""F17 + residuos F10/F12/F14 + DuckDB/Parquet + LIVE gate."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.manifests import DatasetManifest, TimeRange
from quantlab.data.catalog import DataCatalog, DuckDBCatalogBackend
from quantlab.data.storage import ParquetProcessedStore
from quantlab.execution import LiveOrderRouter, assert_live_routing_blocked
from quantlab.optimizer import ParetoPoint, TrialResult, pareto_from_trials, pareto_front
from quantlab.research.strategies import (
    AvellanedaStoikovStrategy,
    optimal_half_spread,
    reservation_price,
)
from quantlab.scale import (
    ParallelBatchRunner,
    ProgressMonitor,
    backup_directory,
    restore_backup,
    run_trivial_capacity_probe,
)
from quantlab.validation import benjamini_hochberg, bonferroni, holm_bonferroni


def test_parallel_batch_map_and_monitor() -> None:
    runner = ParallelBatchRunner(max_workers=4, chunk_size=10)
    report = runner.map_indexed(50, lambda i: i * 2, store_results=True)
    assert report.completed == 50
    assert report.failed == 0
    assert report.results is not None
    assert report.results[0] == 0
    assert report.results[49] == 98
    assert report.throughput_per_sec > 0


def test_capacity_probe_100k() -> None:
    report = run_trivial_capacity_probe(100_000, max_workers=8, chunk_size=5000)
    assert report.n_jobs == 100_000
    assert report.completed == 100_000
    assert report.failed == 0
    assert report.results is None


def test_backup_and_restore(tmp_path: Path) -> None:
    src = tmp_path / "artifacts"
    src.mkdir()
    (src / "a.txt").write_text("hello", encoding="utf-8")
    (src / "sub").mkdir()
    (src / "sub" / "b.txt").write_text("world", encoding="utf-8")
    dest = tmp_path / "backups"
    result = backup_directory(src, dest, label="exp")
    assert Path(result.archive_path).is_file()
    assert result.files_count == 2
    out = tmp_path / "restored"
    restore_backup(Path(result.archive_path), out)
    assert (out / "a.txt").read_text(encoding="utf-8") == "hello"


def test_progress_monitor_pct() -> None:
    mon = ProgressMonitor(10)
    mon.tick(n=4)
    mon.tick(ok=False, n=1)
    snap = mon.snapshot()
    assert snap.completed == 4
    assert snap.failed == 1
    assert snap.pct == 50.0


def test_bonferroni_and_holm() -> None:
    ps = [0.01, 0.04, 0.03, 0.20]
    b = bonferroni(ps, alpha=0.05)
    assert b.adjusted[0] == pytest.approx(0.04)
    assert b.rejected[0] is True
    h = holm_bonferroni(ps, alpha=0.05)
    assert h.method == "holm"
    assert len(h.adjusted) == 4
    fdr = benjamini_hochberg(ps, alpha=0.05)
    assert fdr.method == "benjamini_hochberg"
    assert all(0.0 <= a <= 1.0 for a in fdr.adjusted)


def test_pareto_front_two_objectives() -> None:
    points = [
        ParetoPoint(0, {"a": 1}, (1.0, 0.5)),  # high sharpe, mid mdd
        ParetoPoint(1, {"a": 2}, (0.5, 0.1)),  # low sharpe, low mdd
        ParetoPoint(2, {"a": 3}, (0.2, 0.8)),  # dominated
        ParetoPoint(3, {"a": 4}, (0.9, 0.2)),  # on front
    ]
    # maximize sharpe, minimize mdd
    front = pareto_front(points, maximize=(True, False))
    ids = {p.trial_id for p in front.front}
    assert 2 not in ids
    assert len(front.front) >= 2


def test_pareto_from_trials() -> None:
    trials = [
        TrialResult(params={"x": 1}, score=1.0, trial_id=0),
        TrialResult(params={"x": 2}, score=0.5, trial_id=1),
    ]
    res = pareto_from_trials(trials, second_objective=[0.3, 0.1], maximize=(True, False))
    assert res.n_objectives == 2
    assert len(res.front) >= 1


def test_avellaneda_formulas_and_quotes() -> None:
    from quantlab.core.contracts.strategy import StrategyContext
    from quantlab.core.types.enums import ClockMode, ClockSpeed, EventType
    from quantlab.core.types.market import MarketEvent
    from quantlab.core.types.portfolio import SimulationClock

    r = reservation_price(mid=100.0, inventory=2.0, gamma=0.1, sigma=0.02, tau=0.5)
    assert r < 100.0
    d = optimal_half_spread(gamma=0.1, sigma=0.02, kappa=1.5, tau=0.5)
    assert d > 0

    strat = AvellanedaStoikovStrategy({"quantity": "1", "gamma": 0.1, "sigma": 0.02})
    ctx = StrategyContext(
        clock=SimulationClock(
            current_time=datetime.now(tz=UTC),
            mode=ClockMode.EVENT_DRIVEN,
            speed=ClockSpeed.ACCELERATED,
        ),
        portfolio_state=None,
        parameters={"best_bid": "99", "best_ask": "101", "inventory": "0"},
    )
    evt = MarketEvent(
        event_id="e1",
        event_type=EventType.ORDER_BOOK_SNAPSHOT,
        timestamp=datetime.now(tz=UTC),
        instrument_id="AS:X",
        payload={},
    )
    intents = strat.on_event(evt, ctx)
    assert any(i.intent_type.value == "place_order" for i in intents)


def test_parquet_roundtrip(tmp_path: Path) -> None:
    store = ParquetProcessedStore(tmp_path / "processed")
    rows = [
        {"ts": "2024-01-01T00:00:00+00:00", "close": "100.0", "symbol": "X"},
        {"ts": "2024-01-01T00:01:00+00:00", "close": "101.0", "symbol": "X"},
    ]
    written = store.write_rows(
        dataset_id="ds-pq",
        schema_version="1.0",
        symbol="X",
        timeframe="1m",
        rows=rows,
        meta={"source": "test"},
    )
    assert Path(written.path).is_file()
    assert written.rows == 2
    loaded = store.read_rows(Path(written.path))
    assert len(loaded) == 2
    assert loaded[0]["close"] == "100.0"


def test_duckdb_catalog_backend(tmp_path: Path) -> None:
    backend = DuckDBCatalogBackend(tmp_path / "cat.duckdb")
    now = datetime.now(tz=UTC)
    manifest = DatasetManifest(
        dataset_id="ds-duck",
        version="v1",
        source="test",
        instruments=("INST1",),
        time_range=TimeRange(
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end=datetime(2024, 1, 2, tzinfo=UTC),
        ),
        granularity="1m",
        schema_version="1.0",
        checksum="ab" * 32,
        row_count=2,
        storage_path=str(tmp_path / "data"),
        created_at=now,
    )
    cat = DataCatalog(tmp_path / "unused.sqlite", backend=backend)
    cat.register_dataset(manifest, kind="bars", provider="generic_csv")
    got = cat.get_dataset("ds-duck")
    assert got is not None
    assert got.provider == "generic_csv"
    assert cat.verify_dataset("ds-duck")


def test_live_routing_blocked() -> None:
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        assert_live_routing_blocked()
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        LiveOrderRouter()
