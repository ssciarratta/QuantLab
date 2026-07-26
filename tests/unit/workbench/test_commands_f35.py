"""Tests Command Palette + /api/commands (F35)."""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import WorkbenchState, handle_get_commands
from quantlab.workbench.commands import PANE_SHORTCUT_ORDER, list_commands
from quantlab.workbench.session import WorkbenchSession


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


def test_list_commands_registry() -> None:
    payload = list_commands()
    assert payload["ok"] is True
    assert payload["kind"] == "commands"
    assert payload["live_blocked"] is True
    assert payload["live_routing"] is False
    assert payload["research_safe"] is True
    assert payload["count"] >= 20
    assert payload["pane_shortcut_order"] == list(PANE_SHORTCUT_ORDER)
    assert "Ctrl+K" in payload["palette_shortcuts"]
    assert "Ctrl+Shift+P" in payload["palette_shortcuts"]

    ids = {c["id"] for c in payload["commands"]}
    assert "open.health" in ids
    assert "open.validation" in ids
    assert "action.health_refresh" in ids
    assert "action.close_focused" in ids
    assert "action.minimize_all" in ids
    assert "action.restore_all" in ids
    assert "action.cascade_windows" in ids
    assert "action.tile_windows" in ids
    assert "action.bring_to_front" in ids
    assert "action.send_to_back" in ids
    assert "action.maximize_window" in ids
    assert "action.restore_from_maximize" in ids

    for cmd in payload["commands"]:
        assert cmd["safe"] is True
        assert cmd["live"] is False
        assert cmd["kind"] in ("pane", "action")
        # No live / venue mutation commands
        blob = json.dumps(cmd).lower()
        assert "flip_live" not in blob
        assert "place_order" not in blob
        assert "set_live" not in blob

    health = next(c for c in payload["commands"] if c["id"] == "open.health")
    assert health["shortcut"] == "Ctrl+1"
    assert health["pane_id"] == "health"


def test_handle_get_commands(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "f35-cmds")
    state = WorkbenchState(session=session)
    body = handle_get_commands(state)
    assert body["ok"] is True
    assert body["count"] == len(body["commands"])


def test_api_commands_http(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    status, body = _get(server, "/api/commands")
    assert status == 200
    assert isinstance(body, dict)
    assert body["ok"] is True
    assert body["kind"] == "commands"
    assert body["live_blocked"] is True
    assert any(c["id"] == "open.market" for c in body["commands"])
    assert any(c.get("action") == "health_refresh" for c in body["commands"])


def test_command_palette_js_served(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    status, html = _get(server, "/")
    assert status == 200
    assert isinstance(html, str)
    assert "command_palette.js" in html

    st2, js = _get(server, "/static/js/command_palette.js")
    assert st2 == 200
    assert isinstance(js, str)
    assert "QLCommandPalette" in js
    assert "Ctrl+K" in js or "command-palette" in js

    st3, shell = _get(server, "/static/js/shell.js")
    assert st3 == 200
    assert isinstance(shell, str)
    assert "QLCommandPalette" in shell
    assert "closeFocused" in shell
    assert "PANE_SHORTCUT_ORDER" in shell

    st4, wm = _get(server, "/static/js/wm.js")
    assert st4 == 200
    assert isinstance(wm, str)
    assert "closeFocused" in wm
    assert "focusedId" in wm
