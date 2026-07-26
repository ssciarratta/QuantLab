"""Tests Access Log panel UI wiring (F62)."""

from __future__ import annotations

from pathlib import Path

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.commands import list_commands


def _static_root() -> Path:
    return Path(__file__).resolve().parents[3] / "src" / "quantlab" / "workbench" / "static"


def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.61.0"
    assert PHASES_SUMMARY == "F19–F69 INTERNAL"
    assert not Path("docs/audit/FASE_62_APPROVED.md").exists()


def test_command_open_access_log() -> None:
    payload = list_commands()
    ids = {c["id"] for c in payload["commands"]}
    assert "open.access_log" in ids
    cmd = next(c for c in payload["commands"] if c["id"] == "open.access_log")
    assert cmd["pane_id"] == "access_log"
    assert cmd["kind"] == "pane"
    assert cmd["safe"] is True
    assert cmd["live"] is False
    assert "access" in cmd["keywords"]


def test_static_access_log_pane_present() -> None:
    root = _static_root()
    index = root / "index.html"
    pane_js = root / "js" / "panes" / "access_log.js"
    shell = root / "js" / "shell.js"
    api = root / "js" / "api.js"
    i18n = root / "js" / "i18n.js"

    assert index.is_file()
    assert pane_js.is_file()

    index_text = index.read_text(encoding="utf-8")
    assert 'data-open="access_log"' in index_text
    assert "panes/access_log.js" in index_text

    js = pane_js.read_text(encoding="utf-8")
    assert "QLApi.getAccessLog" in js
    assert "Auto-refresh" in js
    assert "createAccessLogPane" in js
    assert "acc-auto" in js

    shell_text = shell.read_text(encoding="utf-8")
    assert "openAccessLog" in shell_text
    assert "access_log: openAccessLog" in shell_text

    api_text = api.read_text(encoding="utf-8")
    assert "/api/access-log" in api_text
    assert "getAccessLog" in api_text

    i18n_text = i18n.read_text(encoding="utf-8")
    assert '"pane.access_log"' in i18n_text
