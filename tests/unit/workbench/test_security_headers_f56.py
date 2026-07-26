"""F56 — Security headers + CORS fail-closed (no ACAO *)."""

from __future__ import annotations

import http.client
from http.server import ThreadingHTTPServer

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.security_headers import (
    ACCESS_CONTROL_ALLOW_ORIGIN,
    SECURITY_HEADERS,
    assert_no_wildcard_acao,
    cors_allow_origin,
    is_loopback_origin,
    origin_host,
    security_header_items,
    wants_api_no_store,
)


def test_live_blocked_and_version_f56() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.76.0"
    assert PHASES_SUMMARY == "F19–F84 INTERNAL"


def test_security_headers_constants() -> None:
    assert SECURITY_HEADERS["X-Content-Type-Options"] == "nosniff"
    assert SECURITY_HEADERS["X-Frame-Options"] == "DENY"
    assert SECURITY_HEADERS["Referrer-Policy"] == "no-referrer"
    assert wants_api_no_store("/api/health") is True
    assert wants_api_no_store("/api/mode") is True
    assert wants_api_no_store("/") is False
    assert wants_api_no_store("/static/js/app.js") is False


def test_cors_never_wildcard_and_non_loopback_not_reflected() -> None:
    assert cors_allow_origin(None) is None
    assert cors_allow_origin("*") is None
    assert cors_allow_origin("null") is None
    assert cors_allow_origin("https://evil.example") is None
    assert cors_allow_origin("http://192.168.1.10:8765") is None
    assert cors_allow_origin("http://example.com") is None
    # Loopback Origins may be reflected (exact value).
    assert cors_allow_origin("http://127.0.0.1:8765") == "http://127.0.0.1:8765"
    assert cors_allow_origin("http://localhost:8765") == "http://localhost:8765"
    assert cors_allow_origin("http://[::1]:8765") == "http://[::1]:8765"
    assert is_loopback_origin("http://127.0.0.1:9") is True
    assert is_loopback_origin("https://not-loopback.test") is False
    assert origin_host("http://127.0.0.1:8765") == "127.0.0.1"
    assert_no_wildcard_acao({"Access-Control-Allow-Origin": "http://127.0.0.1"})
    try:
        assert_no_wildcard_acao({"Access-Control-Allow-Origin": "*"})
        raised = False
    except AssertionError:
        raised = True
    assert raised is True


def test_security_header_items_include_cache_for_api() -> None:
    items = dict(security_header_items(path="/api/health", origin=None))
    assert items["X-Content-Type-Options"] == "nosniff"
    assert items["X-Frame-Options"] == "DENY"
    assert items["Referrer-Policy"] == "no-referrer"
    assert items["Cache-Control"] == "no-store"
    assert ACCESS_CONTROL_ALLOW_ORIGIN not in items

    items_evil = dict(
        security_header_items(path="/api/health", origin="https://evil.example")
    )
    assert ACCESS_CONTROL_ALLOW_ORIGIN not in items_evil

    items_lb = dict(
        security_header_items(path="/api/health", origin="http://127.0.0.1:8765")
    )
    assert items_lb[ACCESS_CONTROL_ALLOW_ORIGIN] == "http://127.0.0.1:8765"


def _header_map(resp: http.client.HTTPResponse) -> dict[str, str]:
    return {k.lower(): v for k, v in resp.getheaders()}


def test_http_api_security_headers_present(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    conn = http.client.HTTPConnection(host, port, timeout=5.0)
    try:
        conn.request("GET", "/api/health")
        resp = conn.getresponse()
        body = resp.read()
        assert resp.status == 200, body
        headers = _header_map(resp)
        assert headers.get("x-content-type-options") == "nosniff"
        assert headers.get("x-frame-options") == "DENY"
        assert headers.get("referrer-policy") == "no-referrer"
        assert headers.get("cache-control") == "no-store"
        assert headers.get("access-control-allow-origin") != "*"
        # Sin Origin → no ACAO.
        assert "access-control-allow-origin" not in headers
        assert_no_wildcard_acao(headers)
    finally:
        conn.close()


def test_http_cors_non_loopback_origin_not_reflected(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    conn = http.client.HTTPConnection(host, port, timeout=5.0)
    try:
        conn.request(
            "GET",
            "/api/about",
            headers={"Origin": "https://evil.example"},
        )
        resp = conn.getresponse()
        raw = resp.read()
        assert resp.status == 200, raw
        headers = _header_map(resp)
        assert headers.get("x-content-type-options") == "nosniff"
        assert headers.get("x-frame-options") == "DENY"
        assert headers.get("referrer-policy") == "no-referrer"
        assert headers.get("cache-control") == "no-store"
        # No reflejar Origin non-loopback; nunca *.
        assert "access-control-allow-origin" not in headers
        assert_no_wildcard_acao(headers)
    finally:
        conn.close()


def test_http_cors_loopback_origin_may_reflect(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    origin = f"http://127.0.0.1:{port}"
    conn = http.client.HTTPConnection(host, port, timeout=5.0)
    try:
        conn.request("GET", "/api/livez", headers={"Origin": origin})
        resp = conn.getresponse()
        raw = resp.read()
        assert resp.status == 200, raw
        headers = _header_map(resp)
        assert headers.get("access-control-allow-origin") == origin
        assert headers.get("access-control-allow-origin") != "*"
        assert headers.get("cache-control") == "no-store"
    finally:
        conn.close()


def test_http_static_has_security_headers_without_forcing_api_cache(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    conn = http.client.HTTPConnection(host, port, timeout=5.0)
    try:
        conn.request("GET", "/")
        resp = conn.getresponse()
        raw = resp.read()
        assert resp.status == 200, raw
        headers = _header_map(resp)
        assert headers.get("x-content-type-options") == "nosniff"
        assert headers.get("x-frame-options") == "DENY"
        assert headers.get("referrer-policy") == "no-referrer"
        # Cache-Control no-store es obligatorio en /api/*; static no lo exige.
        assert headers.get("access-control-allow-origin") != "*"
    finally:
        conn.close()
