"""POST /api/mode rechaza LIVE."""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer

from quantlab.brokers.mode import OperatingMode
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import WorkbenchState


def test_api_mode_rejects_live(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    assert LIVE_BLOCKED is True
    server, state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    conn = http.client.HTTPConnection(host, port, timeout=5)
    payload = json.dumps({"mode": "live"}).encode("utf-8")
    conn.request(
        "POST",
        "/api/mode",
        body=payload,
        headers={"Content-Type": "application/json"},
    )
    resp = conn.getresponse()
    body = json.loads(resp.read().decode("utf-8"))
    conn.close()

    assert resp.status == 400
    assert body["ok"] is False
    assert "LIVE" in body["error"] or "live" in body["error"].lower()
    assert state.mode is not OperatingMode.LIVE


def test_api_mode_accepts_real_as_paper(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    conn = http.client.HTTPConnection(host, port, timeout=5)
    payload = json.dumps({"mode": "real"}).encode("utf-8")
    conn.request(
        "POST",
        "/api/mode",
        body=payload,
        headers={"Content-Type": "application/json"},
    )
    resp = conn.getresponse()
    body = json.loads(resp.read().decode("utf-8"))
    conn.close()

    assert resp.status == 200
    assert body["mode"] == "paper"
    assert body["live_blocked"] is True
    assert body["real_alias"] == "paper"
    assert state.mode is OperatingMode.PAPER


def test_api_get_mode(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    conn = http.client.HTTPConnection(host, port, timeout=5)
    conn.request("GET", "/api/mode")
    resp = conn.getresponse()
    body = json.loads(resp.read().decode("utf-8"))
    conn.close()
    assert resp.status == 200
    assert body["mode"] == "tester"
    assert body["live_blocked"] is True
