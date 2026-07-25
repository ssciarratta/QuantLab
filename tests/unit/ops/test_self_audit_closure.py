"""Cierre residual self-audit: C2/C3 red-team + cobertura batch/AS/DuckDB/grid."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import duckdb
import pytest

from quantlab.core.contracts.strategy import StrategyContext
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import (
    ClockMode,
    ClockSpeed,
    EventType,
    IntentType,
    OrderSide,
    OrderType,
    TimeInForce,
)
from quantlab.core.types.manifests import DatasetManifest, TimeRange
from quantlab.core.types.market import Bar, MarketEvent
from quantlab.core.types.orders import OrderIntent
from quantlab.core.types.portfolio import SimulationClock
from quantlab.data.catalog import DataCatalog, DuckDBCatalogBackend
from quantlab.data.exchanges.a3.adapter import A3Adapter
from quantlab.data.exchanges.a3.config import A3Config, load_a3_config
from quantlab.data.exchanges.a3.constants import A3EnvironmentName
from quantlab.data.exchanges.a3.exceptions import A3LiveTradingDisabledError
from quantlab.data.exchanges.a3.fake_backend import FakeA3Backend
from quantlab.execution.live_gate import LIVE_BLOCKED, assert_live_routing_blocked
from quantlab.execution.order_router import NullRouter
from quantlab.optimizer.grid import GridSearchOptimizer
from quantlab.research.strategies.avellaneda_stoikov import AvellanedaStoikovStrategy
from quantlab.scale.batch import ParallelBatchRunner


def test_c1_live_blocked_invariant() -> None:
    assert LIVE_BLOCKED is True
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        assert_live_routing_blocked()


def test_c2_c3_null_router_and_a3_default(tmp_path: Path) -> None:
    router = NullRouter()
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        router.place_order(
            symbol="GGAL",
            side="BUY",
            size="1",
            order_type="LIMIT",
            price="100",
            client_order_id="c1",
        )
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        router.cancel_order("oid")

    root = Path.cwd()
    cfg = load_a3_config(root / "config" / "exchanges" / "a3.yaml")
    storage = cfg.storage.__class__(
        raw_root=tmp_path / "raw",
        processed_root=tmp_path / "processed",
        catalog_path=tmp_path / "catalog.sqlite",
        kill_switch_path=tmp_path / "kill.json",
    )
    cfg2 = A3Config(
        enabled=True,
        environment=A3EnvironmentName.SIMULATION,
        market_data=cfg.market_data,
        execution=cfg.execution,
        storage=storage,
        risk=cfg.risk,
    )
    adapter = A3Adapter(cfg2, FakeA3Backend(), account="SIM-001")
    assert isinstance(adapter._order_router, NullRouter)
    intent = OrderIntent(
        intent_id="c2",
        intent_type=IntentType.PLACE_ORDER,
        instrument_id="GGAL",
        side=OrderSide.BUY,
        quantity=Decimal("1"),
        price=Decimal("100"),
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.GTC,
    )
    with pytest.raises(A3LiveTradingDisabledError, match="BLOQUEADO"):
        adapter.place_order(intent)


def test_batch_n_jobs_zero_and_store_results_false() -> None:
    runner = ParallelBatchRunner(max_workers=2, chunk_size=2, strict=True)
    empty = runner.map_indexed(0, lambda i: i)
    assert empty.n_jobs == 0
    assert empty.results == ()

    report = runner.map_indexed(5, lambda i: i * 3, store_results=False)
    assert report.results is None
    assert report.completed == 5
    assert report.failed == 0


def test_batch_invalid_chunk_and_n_jobs() -> None:
    with pytest.raises(ValidationError, match="chunk_size"):
        ParallelBatchRunner(chunk_size=0)
    runner = ParallelBatchRunner(max_workers=2, chunk_size=2)
    with pytest.raises(ValidationError, match="n_jobs"):
        runner.map_indexed(-1, lambda i: i)
    with pytest.raises(ValidationError, match="n_jobs"):
        runner.stream_sum(-1, lambda i: 1.0)


def test_stream_sum_strict_raises_exception_group() -> None:
    runner = ParallelBatchRunner(max_workers=2, chunk_size=2, strict=True)

    def boom(i: int) -> float:
        if i == 1:
            raise RuntimeError("fail-one")
        return float(i)

    with pytest.raises(ExceptionGroup) as ei:
        runner.stream_sum(4, boom)
    assert "stream_sum" in str(ei.value)


def test_stream_sum_non_strict_partial() -> None:
    runner = ParallelBatchRunner(max_workers=2, chunk_size=2, strict=False)

    def boom(i: int) -> float:
        if i % 2 == 0:
            raise ValueError("even")
        return 1.0

    total, report = runner.stream_sum(4, boom)
    assert report.failed == 2
    assert report.completed == 2
    assert total == 2.0
    assert report.results is None


def _as_ctx(**params: Any) -> StrategyContext:
    return StrategyContext(
        clock=SimulationClock(
            current_time=datetime(2024, 6, 1, tzinfo=UTC),
            mode=ClockMode.EVENT_DRIVEN,
            speed=ClockSpeed.ACCELERATED,
        ),
        parameters=params,
    )


def _as_event() -> MarketEvent:
    return MarketEvent(
        event_id="e1",
        event_type=EventType.ORDER_BOOK_SNAPSHOT,
        timestamp=datetime(2024, 6, 1, tzinfo=UTC),
        instrument_id="AS:TEST",
    )


def test_avellaneda_max_pos_ask_only_and_lifecycle() -> None:
    strat = AvellanedaStoikovStrategy({"quantity": "1", "max_pos": "2"})
    intents = strat.on_event(
        _as_event(),
        _as_ctx(best_bid="99", best_ask="101", inventory="2"),
    )
    places = [i for i in intents if i.intent_type is IntentType.PLACE_ORDER]
    assert len(places) == 1
    assert places[0].side is OrderSide.SELL

    ts = datetime(2024, 6, 1, tzinfo=UTC)
    assert (
        strat.on_bar(
            Bar(
                instrument_id="AS:TEST",
                open=Decimal("100"),
                high=Decimal("101"),
                low=Decimal("99"),
                close=Decimal("100"),
                volume=Decimal("1"),
                timestamp_open=ts,
                timestamp_close=ts,
                timeframe="1m",
            ),
            _as_ctx(),
        )
        == ()
    )

    strat.set_parameters({"quantity": "2", "max_pos": "5"})
    assert strat.get_parameters()["quantity"] == "2"
    strat.reset()
    assert strat.get_state()["n"] == 0
    assert strat.get_state()["quotes"] == []


def test_avellaneda_noop_px_and_noop_inv() -> None:
    # Mid ~0 → bid negativo → noop-px
    strat = AvellanedaStoikovStrategy({"quantity": "1", "gamma": 0.1, "sigma": 0.5, "kappa": 1.5})
    intents = strat.on_event(
        _as_event(),
        _as_ctx(best_bid="0.0001", best_ask="0.0002", inventory="0"),
    )
    assert intents[0].intent_id == "as-noop-px"

    # inventory >= max_pos y q<=0 → sin quotes
    strat2 = AvellanedaStoikovStrategy({"quantity": "1", "max_pos": "0"})
    intents2 = strat2.on_event(
        _as_event(),
        _as_ctx(best_bid="99", best_ask="101", inventory="0"),
    )
    assert intents2[0].intent_id == "as-noop-inv"


def test_random_search_minimize() -> None:
    opt = GridSearchOptimizer(seed=11)
    result = opt.random_search(
        {"x": [1, 2, 3, 4], "y": [10, 20, 30]},
        objective=lambda p: float(p["x"]) + float(p["y"]),
        n_trials=8,
        maximize=False,
    )
    assert result.method == "random"
    assert result.best.score == min(t.score for t in result.history)


def test_duckdb_verify_empty_storage_path(tmp_path: Path) -> None:
    db_path = tmp_path / "cat.duckdb"
    backend = DuckDBCatalogBackend(db_path)
    cat = DataCatalog(tmp_path / "unused.sqlite", backend=backend)
    data = tmp_path / "payload.bin"
    payload = b"self-audit"
    data.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    created = datetime(2024, 1, 1, tzinfo=UTC)

    cat.register_dataset(
        DatasetManifest(
            dataset_id="ds-ok",
            version="v1",
            source="test",
            instruments=("X",),
            time_range=TimeRange(start=created - timedelta(hours=1), end=created),
            granularity="1m",
            schema_version="1.0",
            checksum=digest,
            row_count=1,
            storage_path=str(data),
            created_at=created,
        ),
        kind="bars",
        provider="p",
    )
    assert cat.verify_dataset("ds-ok") is True

    entry = cat.get_dataset("ds-ok")
    assert entry is not None
    corrupted = dict(entry.manifest)
    corrupted["storage_path"] = ""
    con = duckdb.connect(database=str(db_path))
    try:
        con.execute(
            "UPDATE datasets SET manifest_json = ? WHERE dataset_id = ?",
            [json.dumps(corrupted, ensure_ascii=False, sort_keys=True), "ds-ok"],
        )
    finally:
        con.close()
    assert cat.verify_dataset("ds-ok") is False
