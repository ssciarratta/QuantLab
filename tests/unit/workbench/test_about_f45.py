"""GET /api/about + About UI (F45) — version badge + dialog."""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer
from typing import Any

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import (
    BIND_POLICY_ALLOW_NON_LOOPBACK,
    BIND_POLICY_LOOPBACK,
    PHASES_SUMMARY,
    bind_policy_dict,
    build_about_payload,
)
from quantlab.workbench.api import WorkbenchState, handle_get_about
from quantlab.workbench.server import STATIC_ROOT, create_server


def _addr(server: ThreadingHTTPServer) -> tuple[str, int]:
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    return host, port


def _get(server: ThreadingHTTPServer, path: str) -> tuple[int, dict[str, Any] | str]:
    host, port = _addr(server)
    conn = http.client.HTTPConnection(host, port, timeout=30)
    conn.request("GET", path)
    resp = conn.getresponse()
    raw = resp.read().decode("utf-8")
    conn.close()
    ctype = resp.getheader("Content-Type") or ""
    if "json" in ctype or raw.startswith("{"):
        return resp.status, json.loads(raw)
    return resp.status, raw


def test_live_blocked_still_true() -> None:
    assert LIVE_BLOCKED is True


def test_phases_summary_constant() -> None:
    assert PHASES_SUMMARY == "F19–F102 INTERNAL"


def test_bind_policy_loopback_default() -> None:
    bp = bind_policy_dict(bind_host="127.0.0.1", allow_non_loopback=False)
    assert bp["policy"] == BIND_POLICY_LOOPBACK
    assert bp["loopback"] is True
    assert bp["allow_non_loopback"] is False
    assert bp["loopback_enforced"] is True


def test_bind_policy_allow_non_loopback() -> None:
    bp = bind_policy_dict(bind_host="0.0.0.0", allow_non_loopback=True)
    assert bp["policy"] == BIND_POLICY_ALLOW_NON_LOOPBACK
    assert bp["loopback"] is False
    assert bp["allow_non_loopback"] is True


def test_build_about_payload_shape() -> None:
    import platform

    payload = build_about_payload()
    assert payload["ok"] is True
    assert payload["kind"] == "about"
    assert payload["version"] == __version__ == "0.94.0"
    assert payload["live_blocked"] is True
    assert payload["live_routing"] is False
    assert payload["research_safe"] is True
    assert payload["phases_summary"] == PHASES_SUMMARY
    assert payload["python_version"] == platform.python_version()
    assert "bind_policy" in payload
    assert payload["bind_policy"]["policy"] == BIND_POLICY_LOOPBACK


def test_handle_get_about_uses_state_bind(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    _server, state = workbench_server
    assert state.bind_host == "127.0.0.1"
    assert state.allow_non_loopback is False
    payload = handle_get_about(state)
    assert payload["ok"] is True
    assert payload["version"] == "0.94.0"
    assert payload["bind_policy"]["bind_host"] == "127.0.0.1"


def test_api_about_http(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    status, body = _get(server, "/api/about")
    assert status == 200
    assert isinstance(body, dict)
    assert body["ok"] is True
    assert body["kind"] == "about"
    assert body["version"] == "0.94.0"
    assert body["live_blocked"] is True
    assert body["phases_summary"] == "F19–F102 INTERNAL"
    assert "python_version" in body
    assert body["bind_policy"]["policy"] == BIND_POLICY_LOOPBACK


def test_create_server_records_non_loopback_bind() -> None:
    server = create_server(host="0.0.0.0", port=0, allow_non_loopback=True)
    try:
        state = server.workbench_state  # type: ignore[attr-defined]
        assert isinstance(state, WorkbenchState)
        assert state.allow_non_loopback is True
        assert state.bind_host == "0.0.0.0"
        about = handle_get_about(state)
        assert about["bind_policy"]["policy"] == BIND_POLICY_ALLOW_NON_LOOPBACK
    finally:
        server.server_close()


def test_about_ui_served(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    status, html = _get(server, "/")
    assert status == 200
    assert isinstance(html, str)
    assert "about.js" in html
    assert 'data-open="about"' in html
    assert "Acerca de" in html
    assert "sb-version" in html

    st2, about_js = _get(server, "/static/js/about.js")
    assert st2 == 200
    assert isinstance(about_js, str)
    assert "QLAbout" in about_js
    assert "QLApi.about" in about_js

    st3, shell = _get(server, "/static/js/shell.js")
    assert st3 == 200
    assert isinstance(shell, str)
    assert "openAbout" in shell
    assert "refreshVersionBadge" in shell
    assert "sb-version" in shell

    st4, api = _get(server, "/static/js/api.js")
    assert st4 == 200
    assert isinstance(api, str)
    assert "about:" in api or "about: function" in api

    st5, css = _get(server, "/static/css/workbench.css")
    assert st5 == 200
    assert isinstance(css, str)
    assert "about-dialog" in css
    assert "sb-version" in css

    assert (STATIC_ROOT / "js" / "about.js").is_file()


def test_commands_include_about() -> None:
    from quantlab.workbench.commands import list_commands

    payload = list_commands()
    ids = {c["id"] for c in payload["commands"]}
    assert "open.about" in ids
    about = next(c for c in payload["commands"] if c["id"] == "open.about")
    assert about["pane_id"] == "about"
