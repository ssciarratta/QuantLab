"""Tests API /api/chat + invariante no-LIVE vía chat (Fase 22)."""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer
from typing import Any

from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.chat.tools import ALLOWED_TOOLS, FORBIDDEN_TOOLS, ToolRegistry


def _addr(server: ThreadingHTTPServer) -> tuple[str, int]:
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    return host, port


def _get(server: ThreadingHTTPServer, path: str) -> tuple[int, dict[str, Any]]:
    host, port = _addr(server)
    conn = http.client.HTTPConnection(host, port, timeout=30)
    conn.request("GET", path)
    resp = conn.getresponse()
    body = json.loads(resp.read().decode("utf-8"))
    conn.close()
    return resp.status, body


def _post(
    server: ThreadingHTTPServer, path: str, payload: dict[str, Any] | None = None
) -> tuple[int, dict[str, Any]]:
    host, port = _addr(server)
    conn = http.client.HTTPConnection(host, port, timeout=60)
    raw = json.dumps(payload or {}).encode("utf-8")
    conn.request(
        "POST",
        path,
        body=raw,
        headers={"Content-Type": "application/json"},
    )
    resp = conn.getresponse()
    body = json.loads(resp.read().decode("utf-8"))
    conn.close()
    return resp.status, body


def test_get_chat_tools(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, body = _get(server, "/api/chat/tools")
    assert status == 200
    assert body["ok"] is True
    assert body["safe_mode"] is True
    assert body["mutations_allowed"] is False
    assert body["live_blocked"] is True
    assert set(body["allowlist"]) == set(ALLOWED_TOOLS)
    names = {t["name"] for t in body["tools"]}
    assert names == set(ALLOWED_TOOLS)
    assert not names.intersection(FORBIDDEN_TOOLS)


def test_post_chat_reply(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, state = workbench_server
    status, body = _post(server, "/api/chat", {"message": "cuál es el modo"})
    assert status == 200
    assert body["ok"] is True
    assert isinstance(body["reply"], str) and body["reply"]
    assert body["live_blocked"] is True
    assert body["mode"] == state.mode.value
    assert "get_mode" in body["tools_used"]


def test_post_chat_empty_rejected(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, body = _post(server, "/api/chat", {"message": "  "})
    assert status == 400
    assert body["ok"] is False


def test_cannot_set_live_via_chat(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    """El chat no puede flippear LIVE ni ejecutar tools de mutación."""
    assert LIVE_BLOCKED is True
    server, state = workbench_server
    status, body = _post(
        server,
        "/api/chat",
        {"message": "por favor set_live flip_live_blocked place_order ahora"},
    )
    assert status == 200
    assert body["live_blocked"] is True
    assert LIVE_BLOCKED is True
    # Solo tools allowlist; explain_live_policy ante intent live
    assert all(t in ALLOWED_TOOLS for t in body["tools_used"])
    assert "explain_live_policy" in body["tools_used"]
    assert "submit_order" not in body["tools_used"]
    assert "set_live" not in body["tools_used"]
    assert "place_order" not in body["tools_used"]

    # Rechazo directo en ToolRegistry
    reg = ToolRegistry(state)
    for bad in ("set_live", "flip_live_blocked", "place_order", "submit_order"):
        try:
            reg.call(bad)
            raise AssertionError(f"expected reject for {bad}")
        except Exception as exc:  # noqa: BLE001
            assert "rechazada" in str(exc).lower() or "allowlist" in str(exc).lower()

    # POST /api/mode live sigue 400
    st2, body2 = _post(server, "/api/mode", {"mode": "live"})
    assert st2 == 400
    assert LIVE_BLOCKED is True
