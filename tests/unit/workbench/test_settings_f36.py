"""Tests Settings + Status Bar (F36) — settings.json + GET/PUT /api/settings."""

from __future__ import annotations

import http.client
import json
from decimal import Decimal
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import (
    ApiError,
    WorkbenchState,
    handle_get_settings,
    handle_put_settings,
)
from quantlab.workbench.session import WorkbenchSession
from quantlab.workbench.settings import (
    SETTINGS_VERSION,
    default_settings,
    load_settings,
    normalize_settings,
    save_settings,
)


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


def _put(
    server: ThreadingHTTPServer, path: str, body: dict[str, Any]
) -> tuple[int, dict[str, Any]]:
    host, port = _addr(server)
    payload = json.dumps(body).encode("utf-8")
    conn = http.client.HTTPConnection(host, port, timeout=30)
    conn.request(
        "PUT",
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


def test_default_settings_locale_es() -> None:
    s = default_settings()
    assert s["version"] == SETTINGS_VERSION
    assert s["theme"] == "slate"
    assert s["default_venue"] == "paper"
    assert s["default_strategy"] == "momentum"
    assert s["locale"] == "es"
    assert Decimal(s["slippage_bps"]) == Decimal("0")


def test_save_load_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    payload = {
        "version": 1,
        "theme": "high-contrast",
        "default_venue": "a3",
        "default_strategy": "buy_once",
        "slippage_bps": "12.5",
        "locale": "es",
    }
    saved = save_settings(path, payload)
    assert path.is_file()
    loaded = load_settings(path)
    assert loaded == saved
    assert loaded["theme"] == "high-contrast"
    assert loaded["default_venue"] == "a3"


def test_load_missing_returns_defaults(tmp_path: Path) -> None:
    assert load_settings(tmp_path / "nope.json") == default_settings()


def test_normalize_rejects_bad_theme() -> None:
    with pytest.raises(ValidationError, match="theme"):
        normalize_settings({"theme": "neon", "locale": "es"})


def test_normalize_rejects_bad_locale() -> None:
    with pytest.raises(ValidationError, match="locale"):
        normalize_settings({"locale": "fr"})


def test_normalize_rejects_bad_strategy() -> None:
    with pytest.raises(ValidationError, match="default_strategy"):
        normalize_settings({"default_strategy": "not_a_strategy"})


def test_normalize_rejects_negative_slippage() -> None:
    with pytest.raises(ValidationError, match="slippage"):
        normalize_settings({"slippage_bps": "-1"})


def test_normalize_strategy_alias() -> None:
    s = normalize_settings({"default_strategy": "simple_momentum"})
    assert s["default_strategy"] == "momentum"


def test_session_settings_path(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "set1")
    assert session.settings_path == session.root / "settings.json"
    assert "settings" in session.to_dict()


def test_api_handlers_put_get(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "api-set")
    state = WorkbenchState(session=session)
    state.ensure_session()
    put = handle_put_settings(
        state,
        {
            "theme": "high-contrast",
            "default_venue": "paper",
            "default_strategy": "inventory_mm",
            "slippage_bps": "5",
            "locale": "es",
        },
    )
    assert put["ok"] is True
    assert put["kind"] == "settings"
    assert put["live_blocked"] is True
    assert put["live_routing"] is False
    assert put["settings"]["theme"] == "high-contrast"
    assert put["settings"]["default_strategy"] == "inventory_mm"
    assert state.slippage_bps == Decimal("5")
    assert session.settings_path.is_file()

    got = handle_get_settings(state)
    assert got["ok"] is True
    assert got["settings"]["theme"] == "high-contrast"
    assert got["allowed_themes"] == ["slate", "high-contrast"]
    assert got["allowed_locales"] == ["en", "es"]
    assert got["allowed_timezones"] == ["UTC", "local"]
    assert got["settings"]["timezone"] == "UTC"


def test_api_put_nested_settings_key(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "nested-set")
    state = WorkbenchState(session=session)
    state.ensure_session()
    put = handle_put_settings(
        state,
        {"settings": {"theme": "slate", "default_venue": "binance", "slippage_bps": "1"}},
    )
    assert put["settings"]["default_venue"] == "binance"
    assert put["settings"]["locale"] == "es"


def test_api_put_rejects_bad_theme(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "bad-set")
    state = WorkbenchState(session=session)
    state.ensure_session()
    with pytest.raises(ApiError, match="theme"):
        handle_put_settings(state, {"theme": "purple"})


def test_api_settings_http(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, state = workbench_server
    status, body = _get(server, "/api/settings")
    assert status == 200
    assert isinstance(body, dict)
    assert body["ok"] is True
    assert body["kind"] == "settings"
    assert body["live_blocked"] is True
    assert body["settings"]["locale"] == "es"

    st2, put = _put(
        server,
        "/api/settings",
        {
            "theme": "high-contrast",
            "default_venue": "a3",
            "default_strategy": "momentum",
            "slippage_bps": "3.25",
            "locale": "es",
        },
    )
    assert st2 == 200
    assert put["settings"]["theme"] == "high-contrast"
    assert put["settings"]["default_venue"] == "a3"
    assert state.slippage_bps == Decimal("3.25")


def test_settings_ui_served(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    status, html = _get(server, "/")
    assert status == 200
    assert isinstance(html, str)
    assert "settings.js" in html
    assert "status-bar" in html
    assert "sb-mode" in html
    assert "sb-live" in html
    assert "sb-session" in html
    assert "sb-venue" in html
    assert "sb-md" in html
    assert "sb-clock" in html

    st2, js = _get(server, "/static/js/panes/settings.js")
    assert st2 == 200
    assert isinstance(js, str)
    assert "createSettingsPane" in js
    assert "putSettings" in js or "QLApi.putSettings" in js

    st3, shell = _get(server, "/static/js/shell.js")
    assert st3 == 200
    assert isinstance(shell, str)
    assert "openSettings" in shell
    assert "updateStatusBar" in shell
    assert "sb-clock" in shell or "sbClock" in shell or 'getElementById("sb-clock")' in shell

    st4, css = _get(server, "/static/css/workbench.css")
    assert st4 == 200
    assert isinstance(css, str)
    assert "status-bar" in css
    assert "high-contrast" in css

    st5, api = _get(server, "/static/js/api.js")
    assert st5 == 200
    assert isinstance(api, str)
    assert "getSettings" in api
    assert "putSettings" in api


def test_commands_include_settings_pane() -> None:
    from quantlab.workbench.commands import list_commands

    payload = list_commands()
    ids = {c["id"] for c in payload["commands"]}
    assert "open.settings" in ids
