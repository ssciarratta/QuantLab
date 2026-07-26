"""Workbench: md_provider / md_source / plugins en connect + health + session."""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer

from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import WorkbenchState


def _get(server: ThreadingHTTPServer, path: str) -> tuple[int, dict[str, object]]:
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    conn = http.client.HTTPConnection(host, port, timeout=5)
    conn.request("GET", path)
    resp = conn.getresponse()
    body = json.loads(resp.read().decode("utf-8"))
    conn.close()
    assert isinstance(body, dict)
    return resp.status, body


def _post(
    server: ThreadingHTTPServer, path: str, payload: dict[str, object]
) -> tuple[int, dict[str, object]]:
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    raw = json.dumps(payload).encode("utf-8")
    conn = http.client.HTTPConnection(host, port, timeout=5)
    conn.request(
        "POST",
        path,
        body=raw,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    resp = conn.getresponse()
    body = json.loads(resp.read().decode("utf-8"))
    conn.close()
    assert isinstance(body, dict)
    return resp.status, body


def test_health_includes_venues_and_md_fields(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    status, body = _get(server, "/api/health")
    assert status == 200
    assert body["ok"] is True
    assert body["live_blocked"] is True
    assert LIVE_BLOCKED is True
    assert "venues" in body
    assert "a3" in body["venues"]  # type: ignore[operator]
    assert "generic_csv" in body["venues"]  # type: ignore[operator]
    assert "plugin_venues" in body
    assert body.get("md_provider") is None


def test_connect_accepts_md_source_and_reports_provider(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, state = workbench_server
    status, body = _post(
        server,
        "/api/broker/connect",
        {"venue": "a3", "mode": "tester", "md_source": "fake"},
    )
    assert status == 200
    assert body["ok"] is True
    assert body["md_provider"] == "a3-fake"
    assert body["md_source"] == "fake"
    assert state.md_provider == "a3-fake"

    status_h, health = _get(server, "/api/health")
    assert status_h == 200
    assert health["md_provider"] == "a3-fake"
    assert health["connected_venue"] == "a3"

    status_s, session = _get(server, "/api/session")
    assert status_s == 200
    assert session["md_provider"] == "a3-fake"
    assert "plugin_venues" in session


def test_connect_generic_rest_reports_provider(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    status, body = _post(
        server,
        "/api/broker/connect",
        {"venue": "generic_rest", "mode": "tester"},
    )
    assert status == 200
    assert body["md_provider"] == "generic-rest-fake"


def test_connect_env_md_source_falls_back_without_flag(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    status, body = _post(
        server,
        "/api/broker/connect",
        {"venue": "a3", "mode": "paper", "md_source": "env"},
    )
    assert status == 200
    assert body["md_provider"] == "a3-fake"
    assert body["md_source"] == "fake"
