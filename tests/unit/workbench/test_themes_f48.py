"""Tests Theme CSS Completion (F48) — slate + high-contrast tokens + roundtrip."""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import WorkbenchState, handle_get_settings, handle_put_settings
from quantlab.workbench.server import STATIC_ROOT
from quantlab.workbench.session import WorkbenchSession
from quantlab.workbench.settings import ALLOWED_THEMES, load_settings

REQUIRED_TOKENS = (
    "--bg-deep",
    "--bg-panel",
    "--bg-elevated",
    "--bg-title",
    "--bg-title-end",
    "--bg-banner",
    "--bg-banner-end",
    "--bg-status",
    "--bg-status-end",
    "--bg-taskbar",
    "--bg-taskbar-end",
    "--bg-desktop-a",
    "--bg-desktop-b",
    "--bg-desktop-c",
    "--desktop-glow-amber",
    "--desktop-glow-cool",
    "--border",
    "--border-soft",
    "--text",
    "--text-muted",
    "--amber",
    "--amber-dim",
    "--amber-glow",
    "--amber-soft",
    "--amber-hover",
    "--amber-focus",
    "--danger",
    "--ok",
    "--warn",
    "--accent",
    "--muted",
    "--hover-surface",
    "--overlay",
    "--shadow-win",
    "--shadow-modal",
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


def test_live_blocked_f48() -> None:
    assert LIVE_BLOCKED is True


def test_version_and_phases_f48() -> None:
    assert __version__ == "0.85.0"
    assert PHASES_SUMMARY == "F19–F93 INTERNAL"


def test_css_theme_tokens_complete() -> None:
    css = (STATIC_ROOT / "css" / "workbench.css").read_text(encoding="utf-8")
    assert 'html[data-theme="slate"]' in css
    assert 'html[data-theme="high-contrast"]' in css
    assert 'body[data-theme="slate"]' in css
    assert 'body[data-theme="high-contrast"]' in css
    for token in REQUIRED_TOKENS:
        assert token in css, f"missing token {token}"
    # Chrome surfaces use tokens (not hardcoded slate-only hex in rules)
    assert "var(--bg-banner)" in css
    assert "var(--bg-status)" in css
    assert "var(--bg-taskbar)" in css
    assert "var(--bg-desktop-a)" in css
    assert "var(--desktop-glow-amber)" in css


def test_html_default_data_theme() -> None:
    html = (STATIC_ROOT / "index.html").read_text(encoding="utf-8")
    assert 'data-theme="slate"' in html


def test_shell_and_settings_apply_data_theme() -> None:
    shell = (STATIC_ROOT / "js" / "shell.js").read_text(encoding="utf-8")
    assert "function applyTheme" in shell
    assert 'document.documentElement.setAttribute("data-theme"' in shell
    assert "settingsData.settings.theme" in shell

    settings_js = (STATIC_ROOT / "js" / "panes" / "settings.js").read_text(encoding="utf-8")
    assert "function applyTheme" in settings_js
    assert 'document.documentElement.setAttribute("data-theme"' in settings_js
    assert "putSettings" in settings_js or "QLApi.putSettings" in settings_js


def test_settings_theme_roundtrip(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "theme48")
    state = WorkbenchState(session=session)
    state.ensure_session()

    got = handle_get_settings(state)
    assert got["settings"]["theme"] == "slate"
    assert set(got["allowed_themes"]) == set(ALLOWED_THEMES)

    put = handle_put_settings(state, {"theme": "high-contrast", "locale": "es"})
    assert put["ok"] is True
    assert put["settings"]["theme"] == "high-contrast"
    assert put["live_blocked"] is True
    loaded = load_settings(session.settings_path)
    assert loaded["theme"] == "high-contrast"

    put2 = handle_put_settings(state, {"theme": "slate"})
    assert put2["settings"]["theme"] == "slate"
    assert load_settings(session.settings_path)["theme"] == "slate"


def test_settings_theme_http_roundtrip(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    st, body = _get(server, "/api/settings")
    assert st == 200
    assert isinstance(body, dict)
    assert body["settings"]["theme"] in ALLOWED_THEMES

    st2, put = _put(server, "/api/settings", {"theme": "high-contrast", "locale": "es"})
    assert st2 == 200
    assert put["settings"]["theme"] == "high-contrast"

    st3, got = _get(server, "/api/settings")
    assert st3 == 200
    assert isinstance(got, dict)
    assert got["settings"]["theme"] == "high-contrast"

    st4, put2 = _put(server, "/api/settings", {"theme": "slate"})
    assert st4 == 200
    assert put2["settings"]["theme"] == "slate"
