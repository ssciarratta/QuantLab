"""Tests HTTP access log + GET /api/access-log (F61)."""

from __future__ import annotations

import http.client
import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from quantlab import __version__
from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.access_log import (
    AccessLog,
    clamp_limit,
    list_access_log,
    sanitize_method,
    sanitize_path,
)
from quantlab.workbench.api import (
    WorkbenchState,
    handle_get_access_log,
    handle_put_settings,
    record_http_access,
)
from quantlab.workbench.server import make_handler
from quantlab.workbench.session import WorkbenchSession
from quantlab.workbench.settings import default_settings, load_settings, save_settings


def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.68.0"
    assert PHASES_SUMMARY == "F19–F76 INTERNAL"
    assert not Path("docs/audit/FASE_61_APPROVED.md").exists()


def test_sanitize_strips_query_and_secrets_shape() -> None:
    assert sanitize_path("/api/health?token=abc") == "/api/health"
    assert sanitize_path("/api/about#frag") == "/api/about"
    assert sanitize_method("get") == "GET"
    assert sanitize_method("!!!") == "GET"


def test_clamp_limit() -> None:
    assert clamp_limit(None) == 100
    assert clamp_limit(50) == 50
    assert clamp_limit(9999) == 500
    with pytest.raises(ValidationError):
        clamp_limit(0)


def test_access_log_append_only_no_bodies(tmp_path: Path) -> None:
    path = tmp_path / "access.jsonl"
    log = AccessLog(path)
    row = log.append(method="GET", path="/api/health", status=200, ms=1.25)
    assert row["method"] == "GET"
    assert row["path"] == "/api/health"
    assert row["status"] == 200
    assert row["ms"] == 1.25
    assert row["live_blocked"] is True
    assert "body" not in row
    assert "headers" not in row
    assert "authorization" not in row
    log.append(method="POST", path="/api/mode", status=200, ms=2.0)
    text = path.read_text(encoding="utf-8")
    assert text.count("\n") == 2
    assert "password" not in text.lower()
    assert "secret" not in text.lower()
    rows = log.read_tail(10)
    assert len(rows) == 2
    assert rows[1]["method"] == "POST"


def test_list_access_log_tail(tmp_path: Path) -> None:
    path = tmp_path / "access.jsonl"
    log = AccessLog(path)
    for i in range(5):
        log.append(method="GET", path=f"/api/x{i}", status=200, ms=float(i))
    payload = list_access_log(path, limit=2)
    assert payload["ok"] is True
    assert payload["kind"] == "access_log"
    assert payload["count"] == 2
    assert payload["events"][0]["path"] == "/api/x3"
    assert payload["events"][1]["path"] == "/api/x4"
    assert payload["live_routing"] is False
    assert payload["research_safe"] is True


def test_settings_access_log_default_true(tmp_path: Path) -> None:
    s = default_settings()
    assert s["access_log"] is True
    path = tmp_path / "settings.json"
    save_settings(path, {**s, "access_log": False})
    loaded = load_settings(path)
    assert loaded["access_log"] is False


def test_session_access_path(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "acc61")
    session.ensure_layout()
    assert session.access_path.name == "access.jsonl"
    assert session.access_path.is_file()
    assert "access" in session.to_dict()


def test_record_respects_toggle(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "tog61")
    state = WorkbenchState(session=session)
    state.ensure_session()
    handle_put_settings(state, {"access_log": False})
    before = session.access_path.read_text(encoding="utf-8")
    record_http_access(state, method="GET", path="/api/about", status=200, ms=1.0)
    assert session.access_path.read_text(encoding="utf-8") == before
    handle_put_settings(state, {"access_log": True})
    record_http_access(state, method="GET", path="/api/about", status=200, ms=1.5)
    rows = AccessLog(session.access_path).read_tail(10)
    assert any(r["path"] == "/api/about" for r in rows)


def test_api_handler_list(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "api61")
    state = WorkbenchState(session=session)
    state.ensure_session()
    AccessLog(session.access_path).append(
        method="GET", path="/api/health", status=200, ms=0.5
    )
    payload = handle_get_access_log(state, "limit=50")
    assert payload["ok"] is True
    assert payload["kind"] == "access_log"
    assert payload["count"] >= 1
    assert payload["access_log_enabled"] is True
    assert payload["session_id"] == "api61"
    assert payload["live_blocked"] is True


def test_http_access_log_middleware(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "http61")
    state = WorkbenchState(session=session)
    state.ensure_session()

    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(state))
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    try:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        conn = http.client.HTTPConnection(host, port, timeout=30)
        conn.request("GET", "/api/about")
        resp = conn.getresponse()
        _ = resp.read()
        assert resp.status == 200
        conn.request("GET", "/api/access-log?limit=100")
        resp2 = conn.getresponse()
        raw = resp2.read().decode("utf-8")
        conn.close()
        assert resp2.status == 200
        body: dict[str, Any] = json.loads(raw)
        assert body["ok"] is True
        assert body["kind"] == "access_log"
        paths = {e["path"] for e in body["events"]}
        assert "/api/about" in paths
        for event in body["events"]:
            assert set(event.keys()) >= {"ts", "method", "path", "status", "ms"}
            assert "body" not in event
            assert "headers" not in event
    finally:
        server.shutdown()
