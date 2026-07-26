"""Tests layout persistencia + API GET/PUT /api/layout (F28)."""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import WorkbenchState, handle_get_layout, handle_put_layout
from quantlab.workbench.layout import (
    LAYOUT_VERSION,
    empty_layout,
    load_layout,
    normalize_layout,
    save_layout,
)
from quantlab.workbench.session import WorkbenchSession


def test_live_blocked_still_true() -> None:
    assert LIVE_BLOCKED is True


def test_empty_layout_canonical() -> None:
    layout = empty_layout()
    assert layout == {"version": LAYOUT_VERSION, "windows": {}}


def test_save_load_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "layout.json"
    payload = {
        "version": 1,
        "windows": {
            "health": {"x": 24, "y": 20, "w": 440, "h": 360, "minimized": False},
            "market": {"x": 100, "y": 40, "w": 500, "h": 400, "z": 12},
        },
    }
    saved = save_layout(path, payload)
    assert path.is_file()
    loaded = load_layout(path)
    assert loaded == saved
    assert loaded["windows"]["health"]["w"] == 440
    assert loaded["windows"]["market"]["z"] == 12


def test_load_missing_returns_empty(tmp_path: Path) -> None:
    assert load_layout(tmp_path / "nope.json") == empty_layout()


def test_normalize_rejects_bad_id() -> None:
    with pytest.raises(ValidationError, match="window id"):
        normalize_layout({"version": 1, "windows": {"../x": {"x": 1, "y": 1, "w": 300, "h": 200}}})


def test_normalize_rejects_out_of_range() -> None:
    with pytest.raises(ValidationError, match="fuera de rango"):
        normalize_layout({"version": 1, "windows": {"w1": {"x": 1, "y": 1, "w": 10, "h": 200}}})


def test_session_layout_path(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "lay1")
    assert session.layout_path == session.root / "layout.json"
    assert "layout" in session.to_dict()


def test_api_handlers_put_get(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "api-lay")
    state = WorkbenchState(session=session)
    state.ensure_session()
    put = handle_put_layout(
        state,
        {
            "version": 1,
            "windows": {"blotter": {"x": 10, "y": 20, "w": 520, "h": 400}},
        },
    )
    assert put["ok"] is True
    assert put["live_blocked"] is True
    assert put["layout"]["windows"]["blotter"]["w"] == 520
    assert session.layout_path.is_file()

    got = handle_get_layout(state)
    assert got["ok"] is True
    assert got["layout"]["windows"]["blotter"]["x"] == 10


def test_api_put_nested_layout_key(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "nested")
    state = WorkbenchState(session=session)
    state.ensure_session()
    put = handle_put_layout(
        state,
        {"layout": {"version": 1, "windows": {"journal": {"x": 1, "y": 2, "w": 300, "h": 250}}}},
    )
    assert put["layout"]["windows"]["journal"]["h"] == 250


def test_http_get_put_layout(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)

    body = json.dumps(
        {
            "version": 1,
            "windows": {
                "health": {"x": 30, "y": 25, "w": 450, "h": 350, "minimized": True},
            },
        }
    ).encode("utf-8")

    conn = http.client.HTTPConnection(host, port, timeout=5)
    conn.request(
        "PUT",
        "/api/layout",
        body=body,
        headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
    )
    resp = conn.getresponse()
    put_payload = json.loads(resp.read().decode("utf-8"))
    assert resp.status == 200
    assert put_payload["ok"] is True
    assert put_payload["layout"]["windows"]["health"]["minimized"] is True

    conn.request("GET", "/api/layout")
    resp = conn.getresponse()
    get_payload = json.loads(resp.read().decode("utf-8"))
    conn.close()
    assert resp.status == 200
    assert get_payload["layout"]["windows"]["health"]["x"] == 30
    assert state.ensure_session().layout_path.is_file()


def test_http_put_invalid_rejected(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    body = json.dumps({"version": 99, "windows": {}}).encode("utf-8")
    conn = http.client.HTTPConnection(host, port, timeout=5)
    conn.request(
        "PUT",
        "/api/layout",
        body=body,
        headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
    )
    # Content-Type typo above — still JSON body; server reads by length
    resp = conn.getresponse()
    payload = json.loads(resp.read().decode("utf-8"))
    conn.close()
    assert resp.status == 400
    assert payload["ok"] is False
