"""F57 — Content-Security-Policy (restrictiva SPA local; sin unsafe-eval)."""

from __future__ import annotations

import http.client
import re
from http.server import ThreadingHTTPServer
from pathlib import Path

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.security_headers import (
    CONTENT_SECURITY_POLICY,
    SECURITY_HEADERS,
    security_header_items,
)

_STATIC_INDEX = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "quantlab"
    / "workbench"
    / "static"
    / "index.html"
)


def test_live_blocked_and_version_f57() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.55.0"
    assert PHASES_SUMMARY == "F19–F63 INTERNAL"


def test_csp_policy_constants() -> None:
    csp = CONTENT_SECURITY_POLICY
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "style-src 'self' 'unsafe-inline'" in csp
    assert "connect-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "unsafe-eval" not in csp
    assert SECURITY_HEADERS["Content-Security-Policy"] == CONTENT_SECURITY_POLICY


def test_csp_in_security_header_items() -> None:
    items = dict(security_header_items(path="/api/health", origin=None))
    assert items["Content-Security-Policy"] == CONTENT_SECURITY_POLICY
    assert items["X-Content-Type-Options"] == "nosniff"
    assert items["Cache-Control"] == "no-store"


def test_index_html_has_no_inline_scripts() -> None:
    """Scripts del SPA deben ser archivos externos (script-src 'self')."""
    html = _STATIC_INDEX.read_text(encoding="utf-8")
    # Bloques <script>...</script> sin src (inline) no permitidos.
    inline = re.findall(
        r"<script(?![^>]*\bsrc=)[^>]*>\s*[^<\s]",
        html,
        flags=re.IGNORECASE,
    )
    assert inline == [], f"inline <script> found in index.html: {inline!r}"
    # Debe haber al menos un script externo.
    assert re.search(r'<script\s+src="/static/js/', html) is not None


def _header_map(resp: http.client.HTTPResponse) -> dict[str, str]:
    return {k.lower(): v for k, v in resp.getheaders()}


def test_http_api_sends_csp_header(
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
        csp = headers.get("content-security-policy")
        assert csp is not None
        assert csp == CONTENT_SECURITY_POLICY
        assert "unsafe-eval" not in csp
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp
        # F56 headers siguen presentes.
        assert headers.get("x-content-type-options") == "nosniff"
        assert headers.get("x-frame-options") == "DENY"
        assert headers.get("cache-control") == "no-store"
    finally:
        conn.close()


def test_http_static_index_sends_csp(
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
        assert headers.get("content-security-policy") == CONTENT_SECURITY_POLICY
        # HTML sin scripts inline (compat script-src 'self').
        html = raw.decode("utf-8")
        assert 'src="/static/js/shell.js"' in html
        assert re.search(
            r"<script(?![^>]*\bsrc=)[^>]*>\s*[^<\s]",
            html,
            flags=re.IGNORECASE,
        ) is None
    finally:
        conn.close()
