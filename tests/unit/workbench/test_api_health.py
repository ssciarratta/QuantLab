"""GET /api/health."""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer

from quantlab.workbench.api import WorkbenchState


def test_api_health_ok(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    conn = http.client.HTTPConnection(host, port, timeout=5)
    conn.request("GET", "/api/health")
    resp = conn.getresponse()
    body = json.loads(resp.read().decode("utf-8"))
    conn.close()

    assert resp.status == 200
    assert body["ok"] is True
    assert body["live_blocked"] is True
    assert "checks" in body
    assert "version" in body
