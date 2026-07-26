"""Tests activity log + GET /api/activity (F41)."""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.activity import (
    ACTIVITY_EVENT_TYPES,
    ActivityLog,
    clamp_limit,
    list_activity,
    validate_event_type,
)
from quantlab.workbench.api import (
    ApiError,
    WorkbenchState,
    handle_get_activity,
    handle_post_broker_connect,
    handle_post_lab_backtest,
)
from quantlab.workbench.server import make_handler
from quantlab.workbench.session import WorkbenchSession


def test_live_blocked_still_true() -> None:
    assert LIVE_BLOCKED is True


def test_event_types_allowlist() -> None:
    assert {
        "connect",
        "submit",
        "backtest",
        "optimize",
        "export",
        "error",
        "rehydrate",
    } == ACTIVITY_EVENT_TYPES
    assert validate_event_type("CONNECT") == "connect"
    with pytest.raises(ValidationError, match="desconocido"):
        validate_event_type("live_order")


def test_clamp_limit() -> None:
    assert clamp_limit(None) == 100
    assert clamp_limit(50) == 50
    assert clamp_limit(9999) == 500
    with pytest.raises(ValidationError):
        clamp_limit(0)


def test_activity_log_append_only(tmp_path: Path) -> None:
    path = tmp_path / "activity.jsonl"
    log = ActivityLog(path)
    log.append("connect", ok=True, message="ok", detail={"venue": "fake"})
    log.append("error", ok=False, message="boom", op="connect")
    rows = log.read_tail(10)
    assert len(rows) == 2
    assert rows[0]["event"] == "connect"
    assert rows[0]["ok"] is True
    assert rows[0]["live_blocked"] is True
    assert rows[1]["event"] == "error"
    assert rows[1]["op"] == "connect"
    # Append-only: file grows, no rewrite of prior lines.
    text = path.read_text(encoding="utf-8")
    assert text.count("\n") == 2
    log.append("export", ok=True, message="zip")
    assert path.read_text(encoding="utf-8").count("\n") == 3


def test_list_activity_tail(tmp_path: Path) -> None:
    path = tmp_path / "activity.jsonl"
    log = ActivityLog(path)
    for i in range(5):
        log.append("submit", message=f"n={i}")
    payload = list_activity(path, limit=2)
    assert payload["ok"] is True
    assert payload["count"] == 2
    assert payload["events"][0]["message"] == "n=3"
    assert payload["events"][1]["message"] == "n=4"
    assert payload["live_routing"] is False
    assert payload["research_safe"] is True


def test_session_activity_path(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "act41")
    session.ensure_layout()
    assert session.activity_path.name == "activity.jsonl"
    assert session.activity_path.is_file()
    assert "activity" in session.to_dict()


def test_api_handlers_record_and_list(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "api41")
    state = WorkbenchState(session=session)
    state.ensure_session()

    empty = handle_get_activity(state, "limit=100")
    assert empty["ok"] is True
    assert empty["count"] == 0
    assert empty["session_id"] == "api41"

    connected = handle_post_broker_connect(
        state, {"venue": "binance", "mode": "tester", "md_source": "fake"}
    )
    assert connected["ok"] is True

    listed = handle_get_activity(state, "limit=10")
    assert listed["count"] >= 1
    events = {e["event"] for e in listed["events"]}
    assert "connect" in events

    # Error path records event=error
    with pytest.raises(ApiError):
        handle_post_broker_connect(state, {"venue": "", "mode": "tester"})
    listed2 = handle_get_activity(state, "")
    assert any(e["event"] == "error" and e.get("op") == "connect" for e in listed2["events"])


def test_backtest_records_activity(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "bt41")
    state = WorkbenchState(session=session)
    state.ensure_session()
    result = handle_post_lab_backtest(
        state,
        {
            "strategy_id": "momentum",
            "n_bars": 16,
            "experiment_id": "wb-act-bt",
        },
    )
    assert result.get("ok") is True or "metrics" in result or "kind" in result
    listed = handle_get_activity(state, "limit=5")
    assert any(e["event"] == "backtest" and e["ok"] is True for e in listed["events"])


def test_http_get_activity(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "http41")
    state = WorkbenchState(session=session)
    state.ensure_session()
    ActivityLog(session.activity_path).append("export", message="seed")

    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(state))
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    try:
        import threading

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        conn = http.client.HTTPConnection(host, port, timeout=30)
        conn.request("GET", "/api/activity?limit=50")
        resp = conn.getresponse()
        raw = resp.read().decode("utf-8")
        conn.close()
        assert resp.status == 200
        body: dict[str, Any] = json.loads(raw)
        assert body["ok"] is True
        assert body["kind"] == "activity"
        assert body["count"] >= 1
        assert body["live_blocked"] is True
    finally:
        server.shutdown()
