"""Hardening research-prod A1–A5: live gate, batch strict, integrity, metrics."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
import yaml

from quantlab.backtester.accounting import assert_accounting_balanced
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import (
    FeeType,
    LiquidityType,
    OrderSide,
    OrderStatus,
    OrderType,
    TimeInForce,
)
from quantlab.core.types.manifests import DatasetManifest, TimeRange
from quantlab.core.types.orders import Fee, Fill, Order
from quantlab.core.types.portfolio import Balance, PortfolioState, Position
from quantlab.core.types.results import EquityPoint, SimulationResult
from quantlab.data.catalog.catalog import DataCatalog, SqliteCatalogBackend
from quantlab.data.exchanges.a3.adapter import A3Adapter
from quantlab.data.exchanges.a3.config import A3Config, load_a3_config
from quantlab.data.exchanges.a3.constants import A3EnvironmentName
from quantlab.data.exchanges.a3.fake_backend import FakeA3Backend
from quantlab.execution import LIVE_BLOCKED, GatedBackendRouter, NullRouter
from quantlab.execution.live_gate import assert_live_routing_blocked
from quantlab.metrics.engine import MetricsEngine, win_rate_and_profit_factor
from quantlab.scale.batch import ParallelBatchRunner


def test_live_blocked_constant() -> None:
    assert LIVE_BLOCKED is True
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        assert_live_routing_blocked()


def test_null_router_fail_closed() -> None:
    router = NullRouter()
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        router.place_order(
            symbol="X",
            side="BUY",
            size="1",
            order_type="LIMIT",
            price="1",
            client_order_id="c1",
        )


def test_gated_backend_router_never_reaches_fake() -> None:
    router = GatedBackendRouter(FakeA3Backend())
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        router.place_order(
            symbol="DLR/DIC24",
            side="BUY",
            size="1",
            order_type="LIMIT",
            price="1000",
            client_order_id="c1",
        )


def test_a3_yaml_execution_disabled_by_default() -> None:
    raw = yaml.safe_load(
        (Path.cwd() / "config" / "exchanges" / "a3.yaml").read_text(encoding="utf-8")
    )
    assert raw["execution"]["enabled"] is False
    assert raw["execution"]["allow_live_orders"] is False


def test_adapter_default_null_router(tmp_path: Path) -> None:
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


def test_batch_strict_raises_exception_group() -> None:
    runner = ParallelBatchRunner(max_workers=2, chunk_size=2, strict=True)

    def boom(i: int) -> int:
        if i == 1:
            raise RuntimeError("worker-fail")
        return i

    with pytest.raises(ExceptionGroup) as ei:
        runner.map_indexed(3, boom)
    assert "ParallelBatchRunner" in str(ei.value)
    assert any(isinstance(e, RuntimeError) for e in ei.value.exceptions)


def test_batch_non_strict_reports_failed() -> None:
    runner = ParallelBatchRunner(max_workers=2, chunk_size=2, strict=False)

    def boom(i: int) -> int:
        if i == 0:
            raise ValueError("x")
        return i

    report = runner.map_indexed(2, boom)
    assert report.failed == 1
    assert report.completed == 1


def test_verify_dataset_hashes_storage(tmp_path: Path) -> None:
    payload = b"integrity-payload"
    path = tmp_path / "bars.bin"
    path.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    now = datetime.now(tz=UTC)
    manifest = DatasetManifest(
        dataset_id="ds-hash",
        version="v1",
        source="test",
        instruments=("X",),
        time_range=TimeRange(
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end=datetime(2024, 1, 2, tzinfo=UTC),
        ),
        granularity="1m",
        schema_version="1.0",
        checksum=digest,
        row_count=1,
        storage_path=str(path),
        created_at=now,
    )
    cat = DataCatalog(
        tmp_path / "cat.sqlite", backend=SqliteCatalogBackend(tmp_path / "cat.sqlite")
    )
    cat.register_dataset(manifest, kind="bars", provider="test")
    assert cat.verify_dataset("ds-hash") is True
    path.write_bytes(b"tampered")
    assert cat.verify_dataset("ds-hash") is False


def test_accounting_fails_on_orphan_fills() -> None:
    ts = datetime(2024, 1, 1, tzinfo=UTC)
    fee = Fee(
        fee_id="fee-1",
        fill_id="f-orphan",
        amount=Decimal("0"),
        currency="USD",
        fee_type=FeeType.TAKER,
    )
    fill = Fill(
        fill_id="f-orphan",
        order_id="missing-order",
        instrument_id="N6:X",
        price=Decimal("10"),
        quantity=Decimal("1"),
        fee=fee,
        timestamp=ts,
        liquidity=LiquidityType.TAKER,
    )
    snap = PortfolioState(
        timestamp=ts,
        positions=(),
        balances=(
            Balance(
                asset="USD",
                available=Decimal("100"),
                locked=Decimal("0"),
                total=Decimal("100"),
                updated_at=ts,
            ),
        ),
        total_equity=Decimal("100"),
        total_realized_pnl=Decimal("0"),
        total_unrealized_pnl=Decimal("0"),
    )
    result = SimulationResult(
        experiment_id="orphan",
        equity_curve=(EquityPoint(ts, Decimal("100")),),
        fills=(fill,),
        orders=(),
        portfolio_snapshots=(snap,),
        events_log=(),
    )
    with pytest.raises(ValidationError, match="orphan fills"):
        assert_accounting_balanced(result, initial_cash=Decimal("100"))


def test_profit_factor_undefined_without_losses() -> None:
    ts = datetime(2024, 1, 1, tzinfo=UTC)
    ts2 = datetime(2024, 1, 2, tzinfo=UTC)
    order = Order(
        order_id="o1",
        client_order_id="c1",
        instrument_id="x",
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
        currency="USDT",
        fee_type=FeeType.TAKER,
    )
    fill = Fill(
        fill_id="fl1",
        order_id="o1",
        instrument_id="x",
        price=Decimal("10"),
        quantity=Decimal("1"),
        fee=fee,
        timestamp=ts,
        liquidity=LiquidityType.TAKER,
    )
    snap = PortfolioState(
        timestamp=ts2,
        positions=(
            Position(
                instrument_id="x",
                quantity=Decimal("1"),
                avg_entry_price=Decimal("10"),
                unrealized_pnl=Decimal("5"),
                realized_pnl=Decimal("0"),
                updated_at=ts2,
            ),
        ),
        balances=(
            Balance(
                asset="USDT",
                available=Decimal("90"),
                locked=Decimal("0"),
                total=Decimal("90"),
                updated_at=ts2,
            ),
        ),
        total_equity=Decimal("105"),
        total_realized_pnl=Decimal("0"),
        total_unrealized_pnl=Decimal("5"),
    )
    result = SimulationResult(
        experiment_id="e-pf",
        equity_curve=(
            EquityPoint(ts, Decimal("100")),
            EquityPoint(ts2, Decimal("105")),
        ),
        fills=(fill,),
        orders=(order,),
        portfolio_snapshots=(snap,),
        events_log=(),
    )
    wr, pf = win_rate_and_profit_factor(result)
    assert wr == 1.0
    assert pf is None
    metrics = MetricsEngine().compute(result)
    assert metrics.metrics["profit_factor"] == "undefined"
