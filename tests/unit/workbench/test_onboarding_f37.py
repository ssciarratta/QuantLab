"""Tests First-run Onboarding Wizard (F37) — meta.onboarding_done + API."""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import (
    WorkbenchState,
    handle_get_onboarding,
    handle_post_onboarding_complete,
)
from quantlab.workbench.onboarding import (
    ONBOARDING_STEPS,
    is_onboarding_done,
    mark_onboarding_complete,
    onboarding_status,
)
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


def _post(
    server: ThreadingHTTPServer, path: str, body: dict[str, Any] | None = None
) -> tuple[int, dict[str, Any]]:
    host, port = _addr(server)
    payload = json.dumps(body or {}).encode("utf-8")
    conn = http.client.HTTPConnection(host, port, timeout=30)
    conn.request(
        "POST",
        path,
        body=payload,
        headers={"Content-Type": "application/json", "Content-Length": str(len(payload))},
    )
    resp = conn.getresponse()
    raw = resp.read().decode("utf-8")
    conn.close()
    return resp.status, json.loads(raw)


def test_live_blocked_still_true() -> None:
    assert LIVE_BLOCKED is True


def test_is_onboarding_done_false_by_default() -> None:
    assert is_onboarding_done({}) is False
    assert is_onboarding_done(None) is False
    assert is_onboarding_done({"onboarding_done": False}) is False


def test_is_onboarding_done_truthy() -> None:
    assert is_onboarding_done({"onboarding_done": True}) is True
    assert is_onboarding_done({"onboarding_done": "true"}) is True


def test_onboarding_steps_count() -> None:
    assert len(ONBOARDING_STEPS) == 4
    ids = [s["id"] for s in ONBOARDING_STEPS]
    assert ids == ["modes", "venue_tester", "paper_or_backtest", "chat_safe"]


def test_status_show_wizard_before_complete(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "ob-new")
    status = onboarding_status(session)
    assert status["onboarding_done"] is False
    assert status["show_wizard"] is True
    assert status["live_blocked"] is True
    assert status["live_routing"] is False
    assert status["research_safe"] is True
    assert len(status["steps"]) == 4
    assert "live" in status["modes"]


def test_mark_complete_persists_meta(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "ob-done")
    status = mark_onboarding_complete(session)
    assert status["onboarding_done"] is True
    assert status["show_wizard"] is False
    assert status["completed_at"]
    meta = session.load_meta()
    assert meta["onboarding_done"] is True
    assert "onboarding_completed_at" in meta

    # Idempotente
    again = mark_onboarding_complete(session)
    assert again["onboarding_done"] is True
    assert again["completed_at"] == meta["onboarding_completed_at"]


def test_api_handlers_get_complete(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "ob-api")
    state = WorkbenchState(session=session)
    state.ensure_session()

    got = handle_get_onboarding(state)
    assert got["ok"] is True
    assert got["kind"] == "onboarding"
    assert got["onboarding_done"] is False
    assert got["show_wizard"] is True
    assert got["live_blocked"] is True

    done = handle_post_onboarding_complete(state, {})
    assert done["ok"] is True
    assert done["onboarding_done"] is True
    assert done["show_wizard"] is False

    got2 = handle_get_onboarding(state)
    assert got2["onboarding_done"] is True


def test_api_onboarding_http(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    status, body = _get(server, "/api/onboarding")
    assert status == 200
    assert isinstance(body, dict)
    assert body["ok"] is True
    assert body["kind"] == "onboarding"
    assert body["live_blocked"] is True
    assert body["show_wizard"] is True or body["onboarding_done"] is True

    st2, complete = _post(server, "/api/onboarding/complete", {})
    assert st2 == 200
    assert complete["onboarding_done"] is True
    assert complete["show_wizard"] is False
    assert complete["live_routing"] is False

    st3, again = _get(server, "/api/onboarding")
    assert st3 == 200
    assert isinstance(again, dict)
    assert again["onboarding_done"] is True


def test_onboarding_ui_served(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    status, html = _get(server, "/")
    assert status == 200
    assert isinstance(html, str)
    assert "onboarding.js" in html

    st2, js = _get(server, "/static/js/onboarding.js")
    assert st2 == 200
    assert isinstance(js, str)
    assert "QLOnboarding" in js
    assert "Completar" in js
    assert "LIVE_BLOCKED" in js
    assert "TESTER" in js

    st3, shell = _get(server, "/static/js/shell.js")
    assert st3 == 200
    assert isinstance(shell, str)
    assert "getOnboarding" in shell
    assert "QLOnboarding" in shell

    st4, css = _get(server, "/static/css/workbench.css")
    assert st4 == 200
    assert isinstance(css, str)
    assert "onboarding-wizard" in css

    st5, api = _get(server, "/static/js/api.js")
    assert st5 == 200
    assert isinstance(api, str)
    assert "getOnboarding" in api
    assert "completeOnboarding" in api
