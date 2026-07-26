"""F55 — OpenAPI / API Catalog (/api/openapi.json)."""

from __future__ import annotations

import contextlib
import http.client
import json
import threading
from pathlib import Path

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import WorkbenchState, handle_get_openapi
from quantlab.workbench.api_catalog import (
    API_ROUTES,
    OPENAPI_PATH,
    OPENAPI_VERSION,
    ApiRoute,
    assert_no_live_trading_routes,
    build_openapi_schema,
    catalog_routes,
)
from quantlab.workbench.server import create_server
from quantlab.workbench.session import WorkbenchSession


def test_live_blocked_and_version_f55() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.69.0"
    assert PHASES_SUMMARY == "F19–F77 INTERNAL"


def test_catalog_has_health_and_livez() -> None:
    paths = {(r.method, r.path) for r in catalog_routes()}
    assert ("GET", "/api/health") in paths
    assert ("GET", "/api/livez") in paths
    assert ("GET", OPENAPI_PATH) in paths
    assert ("GET", "/api/readyz") in paths


def test_schema_has_health_livez_no_live_trading() -> None:
    schema = build_openapi_schema()
    assert schema["openapi"] == OPENAPI_VERSION
    assert schema["info"]["version"] == "0.69.0"
    paths = schema["paths"]
    assert "/api/health" in paths
    assert "get" in paths["/api/health"]
    assert "/api/livez" in paths
    assert "get" in paths["/api/livez"]
    assert OPENAPI_PATH in paths

    # No LIVE trading routes
    for path in paths:
        assert path != "/api/live"
        assert not path.startswith("/api/live/")
        assert "place_order" not in path.lower()
        assert "set_live" not in path.lower()

    assert_no_live_trading_routes()
    assert schema["x-quantlab"]["live_blocked"] is True
    assert schema["x-quantlab"]["live_routing"] is False
    assert schema["x-quantlab"]["research_safe"] is True
    assert schema["x-quantlab"]["phases_summary"] == PHASES_SUMMARY


def test_assert_rejects_live_trading_route() -> None:
    bad = (
        ApiRoute("/api/live/orders", "POST", "Place live order", ("live",)),
    )
    try:
        assert_no_live_trading_routes(bad)
        raised = False
    except AssertionError:
        raised = True
    assert raised is True


def test_handle_get_openapi(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "openapi")
    state = WorkbenchState(session=session)
    payload = handle_get_openapi(state)
    assert payload["openapi"] == OPENAPI_VERSION
    assert "/api/health" in payload["paths"]
    assert "/api/livez" in payload["paths"]
    assert payload["info"]["version"] == __version__


def test_http_openapi_json(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "http-oa")
    state = WorkbenchState(session=session)
    state.ensure_session()
    server = create_server(host="127.0.0.1", port=0, state=state)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    try:
        conn = http.client.HTTPConnection(host, port, timeout=5.0)
        try:
            conn.request("GET", "/api/openapi.json")
            resp = conn.getresponse()
            raw = resp.read()
            assert resp.status == 200, raw
            body = json.loads(raw.decode("utf-8"))
            assert body["openapi"].startswith("3.")
            assert "/api/health" in body["paths"]
            assert "/api/livez" in body["paths"]
            for path in body["paths"]:
                assert not (path == "/api/live" or path.startswith("/api/live/"))
        finally:
            conn.close()
    finally:
        with contextlib.suppress(Exception):
            server.shutdown()
        server.server_close()


def test_about_js_mentions_openapi_link() -> None:
    about_js = (
        Path(__file__).resolve().parents[3]
        / "src"
        / "quantlab"
        / "workbench"
        / "static"
        / "js"
        / "about.js"
    )
    text = about_js.read_text(encoding="utf-8")
    assert "/api/openapi.json" in text


def test_route_count_matches_catalog() -> None:
    assert len(API_ROUTES) == len(catalog_routes())
    schema = build_openapi_schema()
    assert schema["x-quantlab"]["route_count"] == len(API_ROUTES)
