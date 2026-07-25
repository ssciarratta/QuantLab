"""Remediación autauditoría 2026-07-25 — H1/H2 + gaps LIVE/sizing/batch."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import (
    FeeType,
    LiquidityType,
    OrderSide,
    OrderStatus,
    OrderType,
    TimeInForce,
)
from quantlab.core.types.market import Bar
from quantlab.core.types.orders import Fee, Fill, Order
from quantlab.core.types.results import EquityPoint, SimulationResult
from quantlab.data.catalog.catalog import DataCatalog
from quantlab.data.catalog.duckdb_backend import DuckDBCatalogBackend
from quantlab.data.exchanges.a3.client import PyRofexBackend
from quantlab.execution import GatedBackendRouter, NullRouter
from quantlab.features import ClosePriceTransformer, build_pipeline
from quantlab.features.store import FeatureStore
from quantlab.ledger import LocalPaperLedger
from quantlab.research.sizing import fixed_fractional, volatility_target
from quantlab.scale.backup import copy_tree_backup
from quantlab.scale.batch import ParallelBatchRunner, assert_capacity_claim


def _bars(n: int = 3) -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 9, 1, tzinfo=UTC)
    for i in range(n):
        c = Decimal(100 + i)
        t0 = base + timedelta(minutes=i)
        out.append(
            Bar(
                instrument_id="AUD:X",
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


def test_feature_store_rejects_overwrite_different_content(tmp_path: Path) -> None:
    store = FeatureStore(tmp_path / "fs")
    f1 = build_pipeline(ClosePriceTransformer(), name="p").run(_bars(3))
    f2 = build_pipeline(ClosePriceTransformer(), name="p").run(_bars(4))
    store.put(f1, version="v1")
    with pytest.raises(ValidationError, match="ya existe"):
        store.put(f2, version="v1")
    # mismo contenido: idempotente
    ref = store.put(f1, version="v1")
    assert ref.version == "v1"


def test_null_and_gated_cancel_blocked() -> None:
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        NullRouter().cancel_order("x")
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        GatedBackendRouter(__import__(
            "quantlab.data.exchanges.a3.fake_backend", fromlist=["FakeA3Backend"]
        ).FakeA3Backend()).cancel_order("x")


def test_pyrofex_backend_place_blocked() -> None:
    from quantlab.data.exchanges.a3.config import A3Credentials
    from quantlab.data.exchanges.a3.constants import A3EnvironmentName

    backend = PyRofexBackend(
        A3Credentials(user="u", password="p", account="a", token="t"),
        A3EnvironmentName.SIMULATION,
    )
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        backend.place_order(
            symbol="X",
            side="BUY",
            size="1",
            order_type="LIMIT",
            price="1",
            client_order_id="c",
        )
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        backend.cancel_order("oid")


def test_sizing_volatility_and_rejects() -> None:
    qty = volatility_target(
        Decimal("10000"),
        target_vol=Decimal("0.10"),
        realized_vol=Decimal("0.20"),
        base_qty=Decimal("2"),
    )
    assert qty == Decimal("1.00000000")
    with pytest.raises(ValidationError):
        fixed_fractional(Decimal("1000"), risk_fraction=Decimal("1"), stop_distance=Decimal("1"))
    ff = fixed_fractional(
        Decimal("1000"), risk_fraction=Decimal("0.01"), stop_distance=Decimal("2")
    )
    assert ff == Decimal("5.00000000")


def test_batch_reduce_and_capacity() -> None:
    runner = ParallelBatchRunner(max_workers=2, chunk_size=10, strict=True)
    total, report = runner.reduce_indexed(5, lambda i: float(i))
    assert total == float(sum(range(5)))
    assert report.completed == 5
    assert_capacity_claim(100_000, minimum=100_000)
    with pytest.raises(ValidationError):
        assert_capacity_claim(10, minimum=100)
    with pytest.raises(ValidationError):
        ParallelBatchRunner(max_workers=0)


def test_copy_tree_backup(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_text("x", encoding="utf-8")
    dest = tmp_path / "dest"
    copy_tree_backup(src, dest)
    assert (dest / "a.txt").read_text(encoding="utf-8") == "x"
    with pytest.raises(ValidationError):
        copy_tree_backup(src, dest)


def test_paper_ledger_idempotent_conflict(tmp_path: Path) -> None:
    ts = datetime(2024, 1, 1, tzinfo=UTC)
    order = Order(
        order_id="o1",
        client_order_id="c1",
        instrument_id="AUD:X",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("1"),
        filled_quantity=Decimal("1"),
        price=Decimal("10"),
        status=OrderStatus.FILLED,
        created_at=ts,
        updated_at=ts,
        time_in_force=TimeInForce.GTC,
    )
    fee = Fee(
        fee_id="f1",
        fill_id="fl1",
        amount=Decimal("0"),
        currency="USD",
        fee_type=FeeType.TAKER,
    )
    fill = Fill(
        fill_id="fl1",
        order_id="o1",
        instrument_id="AUD:X",
        price=Decimal("10"),
        quantity=Decimal("1"),
        fee=fee,
        timestamp=ts,
        liquidity=LiquidityType.TAKER,
    )
    base = SimulationResult(
        experiment_id="idem-1",
        equity_curve=(EquityPoint(ts, Decimal("100")),),
        fills=(fill,),
        orders=(order,),
        portfolio_snapshots=(),
        events_log=(),
    )
    ledger = LocalPaperLedger(tmp_path / "p.sqlite")
    assert ledger.append_simulation(base) > 0
    other = SimulationResult(
        experiment_id="idem-1",
        equity_curve=(EquityPoint(ts, Decimal("200")),),
        fills=(),
        orders=(),
        portfolio_snapshots=(),
        events_log=(),
    )
    with pytest.raises(ValidationError, match="otro payload"):
        ledger.append_simulation(other)


def test_duckdb_list_and_verify_tamper(tmp_path: Path) -> None:
    import hashlib

    from quantlab.core.types.manifests import DatasetManifest, TimeRange

    backend = DuckDBCatalogBackend(tmp_path / "c.duckdb")
    data = tmp_path / "d.bin"
    data.write_bytes(b"abc")
    checksum = hashlib.sha256(b"abc").hexdigest()
    now = datetime.now(tz=UTC)
    manifest = DatasetManifest(
        dataset_id="ds1",
        version="v1",
        source="t",
        instruments=("X",),
        time_range=TimeRange(
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end=datetime(2024, 1, 2, tzinfo=UTC),
        ),
        granularity="1m",
        schema_version="1.0",
        checksum=checksum,
        row_count=1,
        storage_path=str(data),
        created_at=now,
    )
    cat = DataCatalog(tmp_path / "unused.sqlite", backend=backend)
    cat.register_dataset(manifest, kind="bars", provider="p")
    assert len(cat.list_datasets(provider="p")) == 1
    assert cat.verify_dataset("ds1") is True
    data.write_bytes(b"zzz")
    assert cat.verify_dataset("ds1") is False
