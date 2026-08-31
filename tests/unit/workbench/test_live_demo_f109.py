"""Tests LIVE demo cancel + LIMIT + journal mirror (F109)."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from quantlab import __version__
from quantlab.brokers.binance.demo_router import BinanceDemoRouter, reset_demo_router
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import IntentType, OrderSide, OrderType, TimeInForce
from quantlab.core.types.orders import OrderIntent
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.execution.live_unlock import reset_live_unlock_for_tests, unlock_live_session
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import (
    ApiError,
    WorkbenchState,
    handle_get_live_demo_open_orders,
    handle_post_live_demo_cancel,
    handle_post_live_demo_submit,
)
from quantlab.workbench.session import WorkbenchSession


@pytest.fixture(autouse=True)
def _clean() -> None:
    reset_live_unlock_for_tests()
    reset_demo_router()
    yield
    reset_live_unlock_for_tests()
    reset_demo_router()


@pytest.fixture(autouse=True)
def _isolate_demo_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "QUANTLAB_DEMO_USE_TESTNET",
        "BINANCE_DEMO_API_KEY",
        "BINANCE_DEMO_API_SECRET",
        "QUANTLAB_DEMO_USE_FUTURES_TESTNET",
        "BINANCE_FUTURES_DEMO_API_KEY",
        "BINANCE_FUTURES_DEMO_API_SECRET",
    ):
        monkeypatch.delenv(key, raising=False)


def test_version_f109() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "1.01.0"
    assert PHASES_SUMMARY == "F19–F111 INTERNAL"
    assert not Path("docs/audit/FASE_109_APPROVED.md").exists()


def test_limit_resting_local(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QUANTLAB_LIVE_USER", "op")
    monkeypatch.setenv("QUANTLAB_LIVE_PASSWORD", "sec")
    unlock_live_session(username="op", password="sec")
    router = BinanceDemoRouter()
    intent = OrderIntent(
        intent_id="lim-1",
        intent_type=IntentType.PLACE_ORDER,
        instrument_id="BTCUSDT",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
        price=Decimal("50000"),
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.GTC,
    )
    ack = router.submit(intent)
    assert ack.status == "NEW"
    assert len(router.open_orders()) == 1


def test_limit_marketable_fills_local(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("QUANTLAB_LIVE_USER", "op")
    monkeypatch.setenv("QUANTLAB_LIVE_PASSWORD", "sec")
    unlock_live_session(username="op", password="sec")
    router = BinanceDemoRouter()
    intent = OrderIntent(
        intent_id="lim-2",
        intent_type=IntentType.PLACE_ORDER,
        instrument_id="BTCUSDT",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
        price=Decimal("70000"),
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.GTC,
    )
    ack = router.submit(intent)
    assert ack.status == "FILLED"
    assert len(router.recent_fills()) == 1


def test_cancel_resting_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("QUANTLAB_LIVE_USER", "op")
    monkeypatch.setenv("QUANTLAB_LIVE_PASSWORD", "sec")
    unlock_live_session(username="op", password="sec")
    router = BinanceDemoRouter()
    intent = OrderIntent(
        intent_id="lim-3",
        intent_type=IntentType.PLACE_ORDER,
        instrument_id="BTCUSDT",
        side=OrderSide.SELL,
        quantity=Decimal("0.001"),
        price=Decimal("80000"),
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.GTC,
    )
    ack = router.submit(intent)
    assert ack.status == "NEW"
    cancel = router.cancel(ack.order_id)
    assert cancel.status == "CANCELED"
    assert router.open_orders() == []


def test_demo_cancel_api(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("QUANTLAB_LIVE_USER", "op")
    monkeypatch.setenv("QUANTLAB_LIVE_PASSWORD", "sec")
    unlock_live_session(username="op", password="sec")
    session = WorkbenchSession.create_or_load(tmp_path, "dc1")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    placed = handle_post_live_demo_submit(
        state,
        {
            "symbol": "BTCUSDT",
            "side": "SELL",
            "quantity": "0.001",
            "price": "80000",
        },
    )
    assert placed["status"] == "NEW"
    out = handle_post_live_demo_cancel(state, {"order_id": placed["order_id"]})
    assert out["status"] == "CANCELED"
    open_orders = handle_get_live_demo_open_orders(state)
    assert open_orders["count"] == 0


def test_mirror_to_paper_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("QUANTLAB_LIVE_USER", "op")
    monkeypatch.setenv("QUANTLAB_LIVE_PASSWORD", "sec")
    unlock_live_session(username="op", password="sec")
    session = WorkbenchSession.create_or_load(tmp_path, "mir1")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    out = handle_post_live_demo_submit(
        state,
        {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "quantity": "0.001",
            "mirror_to_paper": True,
        },
    )
    assert out["mirrored_to_paper"] is True
    assert out["paper_fill"] is not None
    journal = state.ensure_journal()
    fills = journal.list_fills()
    assert any(f.source == "binance_demo" for f in fills)


def test_cancel_unknown_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("QUANTLAB_LIVE_USER", "op")
    monkeypatch.setenv("QUANTLAB_LIVE_PASSWORD", "sec")
    unlock_live_session(username="op", password="sec")
    session = WorkbenchSession.create_or_load(tmp_path, "dc2")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    out = handle_post_live_demo_cancel(state, {"order_id": "BN-DEMO-missing"})
    assert out["status"] == "REJECTED"


def test_demo_blocked_without_unlock(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "dc3")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    with pytest.raises(ApiError) as exc:
        handle_post_live_demo_cancel(state, {"order_id": "x"})
    assert exc.value.status == 401
