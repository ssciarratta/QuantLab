"""Tests Minimize / Restore All (F83) — commands API + static JS contract."""

from __future__ import annotations

from pathlib import Path

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.commands import list_commands

_STATIC = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "quantlab"
    / "workbench"
    / "static"
)
_WM_JS = _STATIC / "js" / "wm.js"
_PALETTE_JS = _STATIC / "js" / "command_palette.js"
_SHELL_JS = _STATIC / "js" / "shell.js"
_INDEX = _STATIC / "index.html"


def test_live_blocked_and_version_f83() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "1.01.0"
    assert PHASES_SUMMARY == "F19–F111 INTERNAL"
    assert not Path("docs/audit/FASE_83_APPROVED.md").exists()


def test_commands_include_minimize_restore_all() -> None:
    payload = list_commands()
    assert payload["ok"] is True
    assert payload["live_blocked"] is True
    assert payload["live_routing"] is False
    ids = {c["id"] for c in payload["commands"]}
    assert "action.minimize_all" in ids
    assert "action.restore_all" in ids
    assert "action.close_focused" in ids

    by_id = {c["id"]: c for c in payload["commands"]}
    min_cmd = by_id["action.minimize_all"]
    assert min_cmd["kind"] == "action"
    assert min_cmd["action"] == "minimize_all"
    assert min_cmd["safe"] is True
    assert min_cmd["live"] is False
    assert "minimize" in [k.lower() for k in min_cmd["keywords"]]

    restore_cmd = by_id["action.restore_all"]
    assert restore_cmd["kind"] == "action"
    assert restore_cmd["action"] == "restore_all"
    assert restore_cmd["safe"] is True
    assert restore_cmd["live"] is False
    assert "restore" in [k.lower() for k in restore_cmd["keywords"]]

    for cmd in payload["commands"]:
        blob = str(cmd).lower()
        assert "flip_live" not in blob
        assert "place_order" not in blob


def test_wm_js_minimize_restore_all() -> None:
    js = _WM_JS.read_text(encoding="utf-8")
    assert "minimizeAll" in js
    assert "restoreAll" in js
    assert "WindowManager.prototype.minimizeAll" in js
    assert "WindowManager.prototype.restoreAll" in js
    assert "scheduleSave()" in js
    # Both batch ops persist layout unless silent
    assert "prototype.minimizeAll" in js
    assert "prototype.restoreAll" in js


def test_palette_and_menu_wire_minimize_restore() -> None:
    palette = _PALETTE_JS.read_text(encoding="utf-8")
    assert 'cmd.action === "minimize_all"' in palette
    assert 'cmd.action === "restore_all"' in palette
    assert "minimizeAll" in palette
    assert "restoreAll" in palette

    shell = _SHELL_JS.read_text(encoding="utf-8")
    assert "data-wm-action" in shell
    assert "minimize_all" in shell
    assert "restore_all" in shell
    assert "wm.minimizeAll" in shell
    assert "wm.restoreAll" in shell

    index = _INDEX.read_text(encoding="utf-8")
    assert 'data-wm-action="minimize_all"' in index
    assert 'data-wm-action="restore_all"' in index
    assert 'data-i18n="menu.windows"' in index
