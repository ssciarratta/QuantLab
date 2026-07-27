"""Tests Bring to Front / Send to Back (F85) — commands + static JS + layout z."""

from __future__ import annotations

from pathlib import Path

from quantlab import __version__
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


def test_live_blocked_and_version_f85() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.93.0"
    assert PHASES_SUMMARY == "F19–F101 INTERNAL"
    assert not Path("docs/audit/FASE_85_APPROVED.md").exists()


def test_commands_include_bring_send() -> None:
    payload = list_commands()
    assert payload["ok"] is True
    assert payload["live_blocked"] is True
    assert payload["live_routing"] is False
    ids = {c["id"] for c in payload["commands"]}
    assert "action.bring_to_front" in ids
    assert "action.send_to_back" in ids
    assert "action.cascade_windows" in ids

    by_id = {c["id"]: c for c in payload["commands"]}
    front = by_id["action.bring_to_front"]
    assert front["kind"] == "action"
    assert front["action"] == "bring_to_front"
    assert front["safe"] is True
    assert front["live"] is False
    assert "front" in [k.lower() for k in front["keywords"]]

    back = by_id["action.send_to_back"]
    assert back["kind"] == "action"
    assert back["action"] == "send_to_back"
    assert back["safe"] is True
    assert back["live"] is False
    assert "back" in [k.lower() for k in back["keywords"]]

    for cmd in payload["commands"]:
        blob = str(cmd).lower()
        assert "flip_live" not in blob
        assert "place_order" not in blob


def test_layout_persists_z_order() -> None:
    layout = normalize_layout(
        {
            "version": 1,
            "windows": {
                "health": {"x": 10, "y": 10, "w": 400, "h": 300, "z": 11},
                "market": {"x": 40, "y": 40, "w": 420, "h": 320, "z": 20},
            },
        }
    )
    assert layout["windows"]["health"]["z"] == 11
    assert layout["windows"]["market"]["z"] == 20


def test_wm_js_bring_send_and_context() -> None:
    js = _WM_JS.read_text(encoding="utf-8")
    assert "WindowManager.prototype.bringToFront" in js
    assert "WindowManager.prototype.sendToBack" in js
    assert "_showWindowContextMenu" in js
    assert 'addEventListener("dblclick"' in js
    assert 'addEventListener("contextmenu"' in js
    assert "scheduleSave()" in js
    assert "opts.z" in js


def test_palette_menu_and_css_wire_zorder() -> None:
    palette = _PALETTE_JS.read_text(encoding="utf-8")
    assert 'cmd.action === "bring_to_front"' in palette
    assert 'cmd.action === "send_to_back"' in palette
    assert "bringToFront" in palette
    assert "sendToBack" in palette

    shell = _SHELL_JS.read_text(encoding="utf-8")
    assert "bring_to_front" in shell
    assert "send_to_back" in shell
    assert "wm.bringToFront" in shell
    assert "wm.sendToBack" in shell
    assert "out.z = g.z" in shell or "g.z" in shell

    index = _INDEX.read_text(encoding="utf-8")
    assert 'data-wm-action="bring_to_front"' in index
    assert 'data-wm-action="send_to_back"' in index
    assert 'data-i18n="menu.windows"' in index

    css = _CSS.read_text(encoding="utf-8")
    assert ".win-ctx-menu" in css
