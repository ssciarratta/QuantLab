"""Tests GET /api/broker/heartbeat + status bar poll hooks (F75)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import (
    HEARTBEAT_POLL_SECONDS,
    WorkbenchState,
    handle_get_broker_heartbeat,
    handle_post_broker_connect,
)
from quantlab.workbench.session import WorkbenchSession


def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.67.0"
    assert PHASES_SUMMARY == "F19–F75 INTERNAL"
    assert HEARTBEAT_POLL_SECONDS == 5
    assert not Path("docs/audit/FASE_75_APPROVED.md").exists()


def test_heartbeat_disconnected(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "hb-disc")
    state = WorkbenchState(session=session)
    state.ensure_session()
    body = handle_get_broker_heartbeat(state)
    assert body["ok"] is False
    assert body["status"] == "disconnected"
    assert body["heartbeat"] == "fail"
    assert body["connected"] is False
    assert body["health"] is None
    assert body["poll_seconds"] == 5
    assert body["live_blocked"] is True
    assert body["kind"] == "broker_heartbeat"


def test_heartbeat_ok_after_connect(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "hb-ok")
    state = WorkbenchState(session=session)
    state.ensure_session()
    conn = handle_post_broker_connect(
        state, {"venue": "binance", "mode": "tester"}
    )
    assert conn["ok"] is True
    body = handle_get_broker_heartbeat(state)
    assert body["connected"] is True
    assert body["status"] == "ok"
    assert body["heartbeat"] == "ok"
    assert body["ok"] is True
    assert isinstance(body["health"], dict)
    assert body["venue"] == "binance"
    assert body["live_blocked"] is True
    assert body["poll_seconds"] == HEARTBEAT_POLL_SECONDS


def test_heartbeat_fail_when_health_ok_false(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "hb-fail")
    state = WorkbenchState(session=session)
    state.ensure_session()
    broker = MagicMock()
    broker.health.return_value = {"ok": False, "venue": "mock"}
    state.broker = broker
    state.venue = "mock"
    body = handle_get_broker_heartbeat(state)
    assert body["connected"] is True
    assert body["ok"] is False
    assert body["status"] == "fail"
    assert body["heartbeat"] == "fail"
    assert body["health"] == {"ok": False, "venue": "mock"}


def test_heartbeat_fail_when_health_raises(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "hb-exc")
    state = WorkbenchState(session=session)
    state.ensure_session()
    broker = MagicMock()
    broker.health.side_effect = RuntimeError("md down")
    state.broker = broker
    body = handle_get_broker_heartbeat(state)
    assert body["ok"] is False
    assert body["status"] == "fail"
    assert body["heartbeat"] == "fail"
    assert body["connected"] is True
    assert body["health"] is None
    assert "md down" in str(body.get("error", ""))


def test_static_heartbeat_hooks_present() -> None:
    root = Path(__file__).resolve().parents[3]
    static = root / "src" / "quantlab" / "workbench" / "static"
    html = (static / "index.html").read_text(encoding="utf-8")
    assert "sb-heartbeat" in html
    assert "status.heartbeat" in html
    shell = (static / "js" / "shell.js").read_text(encoding="utf-8")
    assert "brokerHeartbeat" in shell
    assert "pollBrokerHeartbeat" in shell
    assert "heartbeatPollSeconds" in shell
    assert "updateHeartbeatStatus" in shell
    api = (static / "js" / "api.js").read_text(encoding="utf-8")
    assert "/api/broker/heartbeat" in api
    assert "brokerHeartbeat" in api


@pytest.mark.parametrize(
    "status_expected",
    ["disconnected", "ok"],
)
def test_heartbeat_status_values(
    tmp_path: Path, status_expected: str
) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, f"hb-{status_expected}")
    state = WorkbenchState(session=session)
    state.ensure_session()
    if status_expected == "ok":
        handle_post_broker_connect(state, {"venue": "binance", "mode": "tester"})
    body: dict[str, Any] = handle_get_broker_heartbeat(state)
    assert body["status"] == status_expected
