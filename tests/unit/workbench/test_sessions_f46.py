"""Multi-session switcher APIs (F46) — list / switch / new."""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import (
    ApiError,
    WorkbenchState,
    handle_get_sessions,
    handle_post_sessions_new,
    handle_post_sessions_switch,
)
from quantlab.workbench.commands import list_commands
from quantlab.workbench.server import STATIC_ROOT
from quantlab.workbench.session import WorkbenchSession, list_sessions, validate_session_id


def _addr(server: ThreadingHTTPServer) -> tuple[str, int]:
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    return host, port


def _request(
    server: ThreadingHTTPServer,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any] | str]:
    host, port = _addr(server)
    conn = http.client.HTTPConnection(host, port, timeout=30)
    payload = None
    headers: dict[str, str] = {}
    if body is not None:
        payload = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
        headers["Content-Length"] = str(len(payload))
    conn.request(method, path, body=payload, headers=headers)
    resp = conn.getresponse()
    raw = resp.read().decode("utf-8")
    conn.close()
    ctype = resp.getheader("Content-Type") or ""
    if "json" in ctype or raw.startswith("{"):
        return resp.status, json.loads(raw)
    return resp.status, raw


def test_live_blocked_still_true() -> None:
    assert LIVE_BLOCKED is True


def test_phases_summary_tip() -> None:
    assert PHASES_SUMMARY == "F19–F48 INTERNAL"


def test_list_sessions_filters_invalid(tmp_path: Path) -> None:
    parent = tmp_path / "sessions"
    WorkbenchSession.create_or_load(parent, "alpha")
    WorkbenchSession.create_or_load(parent, "beta")
    (parent / "not a session").mkdir(exist_ok=True)
    (parent / "ok-file").write_text("x", encoding="utf-8")
    items = list_sessions(parent)
    ids = {i["session_id"] for i in items}
    assert ids == {"alpha", "beta"}
    assert all("root" in i for i in items)


def test_switch_and_new_handlers(tmp_path: Path) -> None:
    parent = tmp_path / "sessions"
    s1 = WorkbenchSession.create_or_load(parent, "s1")
    WorkbenchSession.create_or_load(parent, "s2")
    state = WorkbenchState(session=s1, session_parent=parent)
    state.ensure_session()
    assert state.session is not None
    assert state.session.session_id == "s1"

    listed = handle_get_sessions(state)
    assert listed["ok"] is True
    assert listed["kind"] == "sessions"
    assert listed["count"] == 2
    assert listed["session_id"] == "s1"
    assert listed["live_blocked"] is True
    currents = [x for x in listed["sessions"] if x["current"]]
    assert len(currents) == 1
    assert currents[0]["session_id"] == "s1"

    switched = handle_post_sessions_switch(state, {"session_id": "s2"})
    assert switched["ok"] is True
    assert switched["kind"] == "session_switch"
    assert switched["session_id"] == "s2"
    assert state.session is not None
    assert state.session.session_id == "s2"
    assert state.book is not None
    assert state.journal is not None

    created = handle_post_sessions_new(state, {"session_id": "s3"})
    assert created["ok"] is True
    assert created["kind"] == "session_new"
    assert created["session_id"] == "s3"
    assert created["created"] is True
    assert (parent / "s3" / "meta.json").is_file()

    auto = handle_post_sessions_new(state, {})
    assert auto["ok"] is True
    assert auto["session_id"]
    assert auto["session_id"] != "s3"


def test_switch_fail_closed_invalid_and_missing(tmp_path: Path) -> None:
    parent = tmp_path / "sessions"
    session = WorkbenchSession.create_or_load(parent, "keep")
    state = WorkbenchState(session=session, session_parent=parent)
    state.ensure_session()

    with pytest.raises(ApiError) as missing:
        handle_post_sessions_switch(state, {"session_id": "ghost"})
    assert missing.value.status == 404

    with pytest.raises(ApiError) as bad:
        handle_post_sessions_switch(state, {"session_id": "../evil"})
    assert bad.value.status == 400

    with pytest.raises(ApiError) as empty:
        handle_post_sessions_switch(state, {})
    assert empty.value.status == 400

    with pytest.raises(ApiError) as exists:
        handle_post_sessions_new(state, {"session_id": "keep"})
    assert exists.value.status == 400

    with pytest.raises(ValidationError):
        validate_session_id("a/b")


def test_switch_persists_book_and_clears_broker(tmp_path: Path) -> None:
    from decimal import Decimal

    from quantlab.brokers.paper.book import PaperBook

    parent = tmp_path / "sessions"
    a = WorkbenchSession.create_or_load(parent, "book-a")
    WorkbenchSession.create_or_load(parent, "book-b")
    state = WorkbenchState(session=a, session_parent=parent)
    state.ensure_session()
    state.book = PaperBook(initial_cash=Decimal("99999"))
    state.venue = "binance"
    state.md_provider = "fake"
    state.broker = object()  # type: ignore[assignment]

    state.switch_session("book-b")
    assert state.venue is None
    assert state.broker is None
    assert state.session is not None
    assert state.session.session_id == "book-b"

    reloaded = WorkbenchSession.create_or_load(parent, "book-a")
    saved = reloaded.load_book()
    assert saved.cash == Decimal("99999")


def test_api_sessions_http(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, state = workbench_server
    parent = state.resolve_session_parent()
    WorkbenchSession.create_or_load(parent, "other46")

    status, body = _request(server, "GET", "/api/sessions")
    assert status == 200
    assert isinstance(body, dict)
    assert body["ok"] is True
    assert body["kind"] == "sessions"
    assert body["count"] >= 2
    assert body["live_blocked"] is True

    st2, switched = _request(server, "POST", "/api/sessions/switch", {"session_id": "other46"})
    assert st2 == 200
    assert isinstance(switched, dict)
    assert switched["session_id"] == "other46"

    st3, created = _request(server, "POST", "/api/sessions/new", {"session_id": "fresh46"})
    assert st3 == 200
    assert isinstance(created, dict)
    assert created["session_id"] == "fresh46"

    st4, err = _request(server, "POST", "/api/sessions/switch", {"session_id": "../x"})
    assert st4 == 400
    assert isinstance(err, dict)
    assert err.get("ok") is False or "error" in err or "message" in err


def test_sessions_ui_served(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    status, html = _request(server, "GET", "/")
    assert status == 200
    assert isinstance(html, str)
    assert "sessions.js" in html
    assert 'data-open="sessions"' in html
    assert ">Sessions<" in html

    st2, pane = _request(server, "GET", "/static/js/panes/sessions.js")
    assert st2 == 200
    assert isinstance(pane, str)
    assert "QLPanes.createSessionsPane" in pane
    assert "sessionsSwitch" in pane

    st3, shell = _request(server, "GET", "/static/js/shell.js")
    assert st3 == 200
    assert isinstance(shell, str)
    assert "openSessions" in shell
    assert "onSessionSwitched" in shell

    st4, api = _request(server, "GET", "/static/js/api.js")
    assert st4 == 200
    assert isinstance(api, str)
    assert "sessionsList" in api
    assert "/api/sessions/switch" in api

    st5, css = _request(server, "GET", "/static/css/workbench.css")
    assert st5 == 200
    assert isinstance(css, str)
    assert "sessions-list" in css
    assert "session-item" in css

    assert (STATIC_ROOT / "js" / "panes" / "sessions.js").is_file()


def test_commands_include_sessions() -> None:
    payload = list_commands()
    ids = {c["id"] for c in payload["commands"]}
    assert "open.sessions" in ids
    cmd = next(c for c in payload["commands"] if c["id"] == "open.sessions")
    assert cmd["pane_id"] == "sessions"
