"""Auditoría integral autónoma 2026-07-26 — gaps MEDIUM remediados."""

from __future__ import annotations

import zipfile
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from quantlab.backtester.micro import MicroBacktestConfig, MicroBacktester
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import FeeType, LiquidityType, OrderSide
from quantlab.core.types.market import Trade
from quantlab.core.types.orders import Fee, Fill, OrderIntent
from quantlab.core.types.results import EquityPoint, SimulationResult
from quantlab.data.exchanges.a3.fake_backend import FakeA3Backend
from quantlab.execution import LIVE_BLOCKED, NullRouter
from quantlab.execution import live_gate as live_gate_mod
from quantlab.execution.live_gate import assert_live_routing_blocked
from quantlab.scale.backup import restore_backup


def test_fake_backend_place_cancel_fail_closed() -> None:
    backend = FakeA3Backend()
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
    assert backend.placed == []


def test_live_gate_blocks_even_if_flag_false(monkeypatch: pytest.MonkeyPatch) -> None:
    assert LIVE_BLOCKED is True
    monkeypatch.setattr(live_gate_mod, "LIVE_BLOCKED", False)
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        assert_live_routing_blocked()
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        NullRouter().place_order(
            symbol="X",
            side="BUY",
            size="1",
            order_type="LIMIT",
            price="1",
            client_order_id="c",
        )


def test_restore_blocks_absolute_zip_member(tmp_path: Path) -> None:
    evil = tmp_path / "evil_abs.zip"
    with zipfile.ZipFile(evil, "w") as zf:
        zf.writestr("/tmp/escape_abs.txt", "pwned")
    dest = tmp_path / "out"
    with pytest.raises(ValidationError, match="zip-slip"):
        restore_backup(evil, dest)


def test_micro_fails_closed_fills_without_snapshots() -> None:
    """Si hay fills y no hay snapshots, no inventar accounting.ok=True."""
    ts = datetime(2024, 1, 1, tzinfo=UTC)
    fee = Fee(
        fee_id="f1",
        fill_id="fill1",
        amount=Decimal("0"),
        currency="USD",
        fee_type=FeeType.TAKER,
    )
    fill = Fill(
        fill_id="fill1",
        order_id="o1",
        instrument_id="X",
        price=Decimal("10"),
        quantity=Decimal("1"),
        fee=fee,
        timestamp=ts,
        liquidity=LiquidityType.TAKER,
    )
    sim = SimulationResult(
        experiment_id="micro-orphan-path",
        equity_curve=(EquityPoint(ts, Decimal("100")),),
        fills=(fill,),
        orders=(),
        portfolio_snapshots=(),
        events_log=(),
    )

    class _StubEngine:
        def run(self, strategy: object, replay: object) -> SimulationResult:
            _ = (strategy, replay)
            return sim

    bt = MicroBacktester(MicroBacktestConfig(experiment_id="micro-orphan-path"))
    bt._engine = _StubEngine()  # type: ignore[assignment]

    class _Noop:
        def on_event(self, event: object, context: object) -> tuple[OrderIntent, ...]:
            return ()

        def on_bar(self, bar: object, context: object) -> tuple[OrderIntent, ...]:
            return ()

        def get_parameters(self) -> dict[str, Any]:
            return {}

        def set_parameters(self, params: dict[str, Any]) -> None:
            return None

        def get_state(self) -> dict[str, Any]:
            return {}

        def reset(self) -> None:
            return None

    with pytest.raises(ValidationError, match="fills presentes sin portfolio_snapshots"):
        bt.run(
            _Noop(),
            trades=(
                Trade(
                    instrument_id="X",
                    price=Decimal("10"),
                    quantity=Decimal("1"),
                    side=OrderSide.BUY,
                    timestamp=ts,
                    trade_id="t1",
                ),
            ),
        )
