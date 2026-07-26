"""Tests Ops Metrics API + workbench exposure (F42)."""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED, assert_live_routing_blocked
from quantlab.infra.ops_metrics import get_ops_metrics
from quantlab.workbench.api import (
    WorkbenchState,
    handle_get_ops_metrics,
    handle_get_ops_prometheus,
)
from quantlab.workbench.commands import list_commands
from quantlab.workbench.server import make_handler
from quantlab.workbench.session import WorkbenchSession


def test_live_blocked_still_true() -> None:
    assert LIVE_BLOCKED is True


def test_ops_metrics_handler_snapshot(tmp_path: Path) -> None:
    metrics = get_ops_metrics()
    metrics.reset()
    metrics.inc("health.runs", 2)
    metrics.inc("live_gate.blocked", 1)

    session = WorkbenchSession.create_or_load(tmp_path, "ops42")
    state = WorkbenchState(session=session)
    state.ensure_session()

    payload = handle_get_ops_metrics(state)
    assert payload["ok"] is True
    assert payload["kind"] == "ops_metrics"
    assert payload["live_blocked"] is True
    assert payload["live_routing"] is False
    assert payload["research_safe"] is True
    assert payload["session_id"] == "ops42"
    assert payload["counters"]["health.runs"] == 2
    assert payload["live_gate_blocked"] == 1
    assert payload["highlight_live_gate_blocked"] is True
    names = [r["name"] for r in payload["rows"]]
    assert "health.runs" in names
    assert "live_gate.blocked" in names
    metrics.reset()


def test_ops_metrics_highlight_when_zero(tmp_path: Path) -> None:
    metrics = get_ops_metrics()
    metrics.reset()
    metrics.inc("batch.failed_jobs", 1)

    session = WorkbenchSession.create_or_load(tmp_path, "ops42z")
    state = WorkbenchState(session=session)
    payload = handle_get_ops_metrics(state)
    assert payload["live_gate_blocked"] == 0
    assert payload["highlight_live_gate_blocked"] is False
    metrics.reset()


def test_ops_prometheus_handler(tmp_path: Path) -> None:
    metrics = get_ops_metrics()
    metrics.reset()
    metrics.inc("live_gate.blocked", 3)

    session = WorkbenchSession.create_or_load(tmp_path, "prom42")
    state = WorkbenchState(session=session)
    text = handle_get_ops_prometheus(state)
    assert "# TYPE live_gate_blocked counter" in text
    assert "live_gate_blocked 3" in text
    metrics.reset()


def test_live_gate_increments_visible_in_api(tmp_path: Path) -> None:
    metrics = get_ops_metrics()
    metrics.reset()
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        assert_live_routing_blocked()

    session = WorkbenchSession.create_or_load(tmp_path, "gate42")
    state = WorkbenchState(session=session)
    payload = handle_get_ops_metrics(state)
    assert payload["counters"].get("live_gate.blocked", 0) >= 1
    assert payload["highlight_live_gate_blocked"] is True
    metrics.reset()


def test_command_open_ops_metrics() -> None:
    payload = list_commands()
    ids = {c["id"] for c in payload["commands"]}
    assert "open.ops_metrics" in ids
    cmd = next(c for c in payload["commands"] if c["id"] == "open.ops_metrics")
    assert cmd["pane_id"] == "ops_metrics"
    assert cmd["safe"] is True
    assert cmd["live"] is False


def test_http_get_ops_metrics_and_prometheus(tmp_path: Path) -> None:
    metrics = get_ops_metrics()
    metrics.reset()
    metrics.inc("health.runs", 4)

    session = WorkbenchSession.create_or_load(tmp_path, "http42")
    state = WorkbenchState(session=session)
    state.ensure_session()

    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(state))
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    try:
        import threading

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        conn = http.client.HTTPConnection(host, port, timeout=30)
        conn.request("GET", "/api/ops/metrics")
        resp = conn.getresponse()
        raw = resp.read().decode("utf-8")
        ctype = resp.getheader("Content-Type") or ""
        conn.close()
        assert resp.status == 200
        assert "json" in ctype
        body: dict[str, Any] = json.loads(raw)
        assert body["ok"] is True
        assert body["kind"] == "ops_metrics"
        assert body["counters"]["health.runs"] == 4
        assert body["live_blocked"] is True

        conn2 = http.client.HTTPConnection(host, port, timeout=30)
        conn2.request("GET", "/api/ops/prometheus")
        resp2 = conn2.getresponse()
        text = resp2.read().decode("utf-8")
        ctype2 = resp2.getheader("Content-Type") or ""
        conn2.close()
        assert resp2.status == 200
        assert "text/plain" in ctype2
        assert "health_runs 4" in text
    finally:
        server.shutdown()
        metrics.reset()
