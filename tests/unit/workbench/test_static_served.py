"""Static assets servidos desde workbench/static."""

from __future__ import annotations

import http.client
from http.server import ThreadingHTTPServer

from quantlab.workbench.api import WorkbenchState


def test_index_and_static_css(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    conn = http.client.HTTPConnection(host, port, timeout=5)

    conn.request("GET", "/")
    resp = conn.getresponse()
    html = resp.read().decode("utf-8")
    assert resp.status == 200
    assert "QuantLab" in html
    assert "text/html" in (resp.getheader("Content-Type") or "")

    conn.request("GET", "/static/css/workbench.css")
    resp = conn.getresponse()
    css = resp.read().decode("utf-8")
    assert resp.status == 200
    assert "--amber" in css or "amber" in css

    conn.request("GET", "/api/static/js/wm.js")
    resp = conn.getresponse()
    js = resp.read().decode("utf-8")
    conn.close()
    assert resp.status == 200
    assert "WindowManager" in js


def test_static_path_traversal_rejected(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    conn = http.client.HTTPConnection(host, port, timeout=5)
    conn.request("GET", "/static/../../../../etc/passwd")
    resp = conn.getresponse()
    _ = resp.read()
    conn.close()
    assert resp.status == 404
