"""Tests Binance demo routing post-unlock (F101)."""

from __future__ import annotations

from pathlib import Path

import pytest

from quantlab import __version__
from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import (
    LIVE_BLOCKED,
    LiveOrderRouter,
    assert_live_routing_blocked,
)
from quantlab.execution.live_unlock import reset_live_unlock_for_tests, unlock_live_session
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import (
    ApiError,
    WorkbenchState,
    handle_get_live_demo_fills,
    handle_post_live_demo_submit,
)
from quantlab.workbench.session import WorkbenchSession


@pytest.fixture(autouse=True)
def _clean_unlock() -> None:
    reset_live_unlock_for_tests()
    yield
    reset_live_unlock_for_tests()


def test_version_and_no_external_cert() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.96.0"
    assert PHASES_SUMMARY == "F19–F104 INTERNAL"
    assert not Path("docs/audit/FASE_101_APPROVED.md").exists()


def test_demo_submit_blocked_without_unlock(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "d1")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    with pytest.raises(ApiError) as exc:
        handle_post_live_demo_submit(
            state, {"symbol": "BTCUSDT", "side": "BUY", "quantity": "0.001"}
        )
    assert exc.value.status == 401


def test_demo_submit_after_unlock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QUANTLAB_LIVE_USER", "demo_op")
    monkeypatch.setenv("QUANTLAB_LIVE_PASSWORD", "demo_secret")
    unlock_live_session(username="demo_op", password="demo_secret")
    assert_live_routing_blocked()

    router = LiveOrderRouter()
    status = router.status()
    assert status["transport"] == "local_demo_sim"
    assert status["remote_testnet"] is False

    session = WorkbenchSession.create_or_load(tmp_path, "d2")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    out = handle_post_live_demo_submit(
        state, {"symbol": "BTCUSDT", "side": "BUY", "quantity": "0.001"}
    )
    assert out["ok"] is True
    assert out["status"] == "FILLED"
    assert out["venue"] == "binance_demo"
    assert out["transport"] == "local_demo_sim"
    assert out["live_routing"] is False
    assert out["order_id"].startswith("BN-DEMO-")

    fills = handle_get_live_demo_fills(state)
    assert fills["count"] >= 1
    assert fills["fills"][-1]["symbol"] == "BTCUSDT"


def test_demo_rejects_unknown_symbol(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("QUANTLAB_LIVE_USER", "demo_op")
    monkeypatch.setenv("QUANTLAB_LIVE_PASSWORD", "demo_secret")
    unlock_live_session(username="demo_op", password="demo_secret")
    session = WorkbenchSession.create_or_load(tmp_path, "d3")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    with pytest.raises(ApiError) as exc:
        handle_post_live_demo_submit(
            state, {"symbol": "DOGEUSDT", "side": "BUY", "quantity": "1"}
        )
    assert exc.value.status == 400


def test_guided_lab_has_demo_submit_ui() -> None:
    root = Path(__file__).resolve().parents[3] / "src" / "quantlab" / "workbench" / "static"
    js = (root / "js" / "panes" / "guided_lab.js").read_text(encoding="utf-8")
    assert "gl-demo-submit" in js
    assert "liveDemoSubmit" in (root / "js" / "api.js").read_text(encoding="utf-8")
