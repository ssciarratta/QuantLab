"""Tests TD-03 — federación / merge de paper ledger shards."""

from __future__ import annotations

from datetime import UTC, datetime
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
from quantlab.core.types.orders import Fee, Fill, Order
from quantlab.core.types.results import EquityPoint, SimulationResult
from quantlab.ledger import LocalPaperLedger, reconcile_indexes


def _result(exp_id: str, *, qty: str = "1") -> SimulationResult:
    ts = datetime(2024, 1, 1, tzinfo=UTC)
    order = Order(
        order_id="o1",
        client_order_id="c1",
        instrument_id="a3:TEST",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal(qty),
        filled_quantity=Decimal(qty),
        price=Decimal("100"),
        status=OrderStatus.FILLED,
        created_at=ts,
        updated_at=ts,
        time_in_force=TimeInForce.GTC,
    )
    fee = Fee(
        fee_id="fee1",
        fill_id="f1",
        amount=Decimal("0.1"),
        currency="USD",
        fee_type=FeeType.TAKER,
    )
    fill = Fill(
        fill_id="f1",
        order_id="o1",
        instrument_id="a3:TEST",
        price=Decimal("100"),
        quantity=Decimal(qty),
        fee=fee,
        timestamp=ts,
        liquidity=LiquidityType.TAKER,
    )
    return SimulationResult(
        experiment_id=exp_id,
        equity_curve=(EquityPoint(timestamp=ts, equity=Decimal("100000")),),
        fills=(fill,),
        orders=(order,),
        portfolio_snapshots=(),
        events_log=(),
    )


def test_reconcile_indexes_conflict_and_sides() -> None:
    report = reconcile_indexes(
        {"a": "1", "b": "2", "c": "3"},
        {"a": "1", "b": "9", "d": "4"},
    )
    assert report.matched == ("a",)
    assert report.only_local == ("c",)
    assert report.only_remote == ("d",)
    assert len(report.conflicts) == 1
    assert report.conflicts[0].experiment_id == "b"
    assert not report.ok


def test_merge_imports_remote_only(tmp_path: Path) -> None:
    local = LocalPaperLedger(tmp_path / "a.sqlite", node_id="node-a")
    remote = LocalPaperLedger(tmp_path / "b.sqlite", node_id="node-b")
    assert local.append_simulation(_result("exp-local")) > 0
    assert remote.append_simulation(_result("exp-remote")) > 0
    assert remote.append_simulation(_result("exp-shared")) > 0
    assert local.append_simulation(_result("exp-shared")) > 0

    report = local.reconcile_with(remote)
    assert set(report.only_remote) == {"exp-remote"}
    assert set(report.matched) == {"exp-shared"}
    assert set(report.only_local) == {"exp-local"}
    assert report.ok

    merged = local.merge_from(remote)
    assert merged.imported_experiments == 1
    assert merged.imported_entries > 0
    assert "exp-remote" in local.experiment_index()
    again = local.merge_from(remote)
    assert again.imported_experiments == 0
    assert again.skipped_identical >= 1


def test_merge_conflict_raises(tmp_path: Path) -> None:
    local = LocalPaperLedger(tmp_path / "a.sqlite", node_id="a")
    remote = LocalPaperLedger(tmp_path / "b.sqlite", node_id="b")
    local.append_simulation(_result("same", qty="1"))
    remote.append_simulation(_result("same", qty="2"))
    with pytest.raises(ValidationError, match="conflict"):
        local.merge_from(remote)
