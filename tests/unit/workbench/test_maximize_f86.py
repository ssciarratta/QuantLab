"""Tests Maximize / Restore Window (F86) — commands + static JS + layout."""

from __future__ import annotations

from pathlib import Path

import pytest

from quantlab import __version__
from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.commands import list_commands
from quantlab.workbench.layout import normalize_layout

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
_CSS = _STATIC / "css" / "workbench.css"
_I18N = _STATIC / "js" / "i18n.js"


def test_live_blocked_and_version_f86() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.97.0"
    assert PHASES_SUMMARY == "F19–F105 INTERNAL"
    assert not Path("docs/audit/FASE_86_APPROVED.md").exists()


def test_commands_include_maximize_restore() -> None:
    payload = list_commands()
    assert payload["ok"] is True
    assert payload["live_blocked"] is True
    assert payload["live_routing"] is False
    ids = {c["id"] for c in payload["commands"]}
    assert "action.maximize_window" in ids
    assert "action.restore_from_maximize" in ids
    assert "action.bring_to_front" in ids

    by_id = {c["id"]: c for c in payload["commands"]}
    mx = by_id["action.maximize_window"]
    assert mx["kind"] == "action"
    assert mx["action"] == "maximize_window"
    assert mx["safe"] is True
    assert mx["live"] is False
    assert "maximize" in [k.lower() for k in mx["keywords"]]

    rest = by_id["action.restore_from_maximize"]
    assert rest["kind"] == "action"
    assert rest["action"] == "restore_from_maximize"
    assert rest["safe"] is True
    assert rest["live"] is False
    assert "restore" in [k.lower() for k in rest["keywords"]]

    for cmd in payload["commands"]:
        blob = str(cmd).lower()
        assert "flip_live" not in blob
        assert "place_order" not in blob


def test_layout_persists_maximized() -> None:
    layout = normalize_layout(
        {
            "version": 1,
            "windows": {
                "health": {
                    "x": 40,
                    "y": 40,
                    "w": 420,
                    "h": 320,
                    "maximized": True,
                    "z": 12,
                },
                "market": {
                    "x": 10,
                    "y": 10,
                    "w": 400,
                    "h": 300,
                    "maximized": False,
                },
            },
        }
    )
    assert layout["windows"]["health"]["maximized"] is True
    assert layout["windows"]["health"]["x"] == 40
    assert layout["windows"]["market"]["maximized"] is False


def test_layout_rejects_non_bool_maximized() -> None:
    with pytest.raises(ValidationError, match="maximized"):
        normalize_layout(
            {
                "version": 1,
                "windows": {
                    "health": {
                        "x": 1,
                        "y": 2,
                        "w": 300,
                        "h": 200,
                        "maximized": "yes",
                    }
                },
            }
        )


def test_wm_js_maximize_restore_and_toggle() -> None:
    js = _WM_JS.read_text(encoding="utf-8")
    assert "WindowManager.prototype.maximize" in js
    assert "WindowManager.prototype.restoreFromMaximize" in js
    assert "WindowManager.prototype.toggleMaximize" in js
    assert "rec.preMax" in js
    assert "maximized" in js
    assert 'addEventListener("dblclick"' in js
    assert "toggleMaximize(id)" in js
    assert "btn-max" in js
    assert "scheduleSave()" in js
    assert "opts.maximized" in js


def test_palette_menu_css_i18n_wire_maximize() -> None:
    palette = _PALETTE_JS.read_text(encoding="utf-8")
    assert 'cmd.action === "maximize_window"' in palette
    assert 'cmd.action === "restore_from_maximize"' in palette
    assert "wm.maximize" in palette
    assert "wm.restoreFromMaximize" in palette

    shell = _SHELL_JS.read_text(encoding="utf-8")
    assert "maximize_window" in shell
    assert "restore_from_maximize" in shell
    assert "wm.maximize" in shell
    assert "wm.restoreFromMaximize" in shell
    assert "maximized: !!g.maximized" in shell

    index = _INDEX.read_text(encoding="utf-8")
    assert 'data-wm-action="maximize_window"' in index
    assert 'data-wm-action="restore_from_maximize"' in index
    assert 'data-i18n="menu.windows"' in index

    css = _CSS.read_text(encoding="utf-8")
    assert ".win.maximized" in css

    i18n = _I18N.read_text(encoding="utf-8")
    assert "action.maximize_window" in i18n
    assert "action.restore_from_maximize" in i18n
