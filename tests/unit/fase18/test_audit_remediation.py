"""Wrapper de verificación — agenda remediación auditoría F18 / research-prod.

Cubre los criterios explícitos del review package:
1. A3Adapter place_order fail-closed (mensaje BLOQUEADO)
2. verify_dataset False si storage alterado byte a byte
3. assert_accounting_balanced falla con fill huérfano

Implementación canónica también en ``tests/unit/ops/test_research_prod_hardening.py``.
LIVE sigue BLOQUEADO.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from quantlab.backtester.accounting import assert_accounting_balanced
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import (
    FeeType,
    IntentType,
    LiquidityType,
    OrderSide,
    OrderType,
    TimeInForce,
)
from quantlab.core.types.manifests import DatasetManifest, TimeRange
from quantlab.core.types.orders import Fee, Fill, OrderIntent
from quantlab.core.types.portfolio import Balance, PortfolioState
from quantlab.core.types.results import EquityPoint, SimulationResult
from quantlab.data.catalog.catalog import DataCatalog, SqliteCatalogBackend
from quantlab.data.exchanges.a3.adapter import A3Adapter
from quantlab.data.exchanges.a3.config import A3Config, load_a3_config
from quantlab.data.exchanges.a3.constants import A3EnvironmentName
from quantlab.data.exchanges.a3.exceptions import A3LiveTradingDisabledError
from quantlab.data.exchanges.a3.fake_backend import FakeA3Backend
from quantlab.execution import LIVE_BLOCKED, NullRouter
from quantlab.execution.live_gate import assert_live_routing_blocked


def _a3_adapter(tmp_path: Path) -> A3Adapter:
    cfg = load_a3_config(Path.cwd() / "config" / "exchanges" / "a3.yaml")
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
    return A3Adapter(cfg2, FakeA3Backend(), account="SIM-001")


def test_audit_live_gate_blocked_message() -> None:
    assert LIVE_BLOCKED is True
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        assert_live_routing_blocked()


def test_audit_a3_adapter_place_order_fail_closed(tmp_path: Path) -> None:
    adapter = _a3_adapter(tmp_path)
    assert isinstance(adapter._order_router, NullRouter)
    intent = OrderIntent(
        intent_id="audit-place",
        intent_type=IntentType.PLACE_ORDER,
        instrument_id="GGAL",
        side=OrderSide.BUY,
        quantity=Decimal("1"),
        price=Decimal("100"),
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.GTC,
    )
    # Adapter envuelve ValidationError → A3LiveTradingDisabledError (fail-closed).
    with pytest.raises(A3LiveTradingDisabledError, match="BLOQUEADO") as ei:
        adapter.place_order(intent)
    assert isinstance(ei.value.__cause__, ValidationError)


def test_audit_verify_dataset_false_when_storage_tampered(tmp_path: Path) -> None:
    payload = b"audit-remediation-payload"
    path = tmp_path / "bars.bin"
    path.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    now = datetime.now(tz=UTC)
    manifest = DatasetManifest(
        dataset_id="ds-audit",
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
    cat = DataCatalog(tmp_path / "cat.sqlite", backend=SqliteCatalogBackend(tmp_path / "cat.sqlite"))
    cat.register_dataset(manifest, kind="bars", provider="test")
    assert cat.verify_dataset("ds-audit") is True
    path.write_bytes(b"tampered-byte-by-byte")
    assert cat.verify_dataset("ds-audit") is False


def test_audit_accounting_fails_on_orphan_fill() -> None:
    ts = datetime(2024, 1, 1, tzinfo=UTC)
    fill = Fill(
        fill_id="f-orphan",
        order_id="missing-order",
        instrument_id="N6:X",
        price=Decimal("10"),
        quantity=Decimal("1"),
        fee=Fee(
            fee_id="fee-1",
            fill_id="f-orphan",
            amount=Decimal("0"),
            currency="USD",
            fee_type=FeeType.TAKER,
        ),
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
        experiment_id="audit-orphan",
        equity_curve=(EquityPoint(ts, Decimal("100")),),
        fills=(fill,),
        orders=(),
        portfolio_snapshots=(snap,),
        events_log=(),
    )
    with pytest.raises(ValidationError, match="orphan fills"):
        assert_accounting_balanced(result, initial_cash=Decimal("100"))
