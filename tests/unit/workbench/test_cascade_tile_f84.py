"""Tests Cascade / Tile Windows (F84) — pure geometry + commands + static JS."""

from __future__ import annotations

from pathlib import Path

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.commands import list_commands
from quantlab.workbench.window_layout import (
    DEFAULT_CASCADE_OFFSET_PX,
    DEFAULT_TILE_GAP_PX,
    DEFAULT_TILE_MARGIN_PX,
    cascade_rects,
    tile_rects,
)

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


def test_live_blocked_and_version_f84() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.97.0"
    assert PHASES_SUMMARY == "F19–F105 INTERNAL"
    assert not Path("docs/audit/FASE_84_APPROVED.md").exists()


def test_commands_include_cascade_tile() -> None:
    payload = list_commands()
    assert payload["ok"] is True
    assert payload["live_blocked"] is True
    assert payload["live_routing"] is False
    ids = {c["id"] for c in payload["commands"]}
    assert "action.cascade_windows" in ids
    assert "action.tile_windows" in ids
    assert "action.minimize_all" in ids

    by_id = {c["id"]: c for c in payload["commands"]}
    casc = by_id["action.cascade_windows"]
    assert casc["kind"] == "action"
    assert casc["action"] == "cascade_windows"
    assert casc["safe"] is True
    assert casc["live"] is False
    assert "cascade" in [k.lower() for k in casc["keywords"]]

    tile = by_id["action.tile_windows"]
    assert tile["kind"] == "action"
    assert tile["action"] == "tile_windows"
    assert tile["safe"] is True
    assert tile["live"] is False
    assert "tile" in [k.lower() for k in tile["keywords"]]

    for cmd in payload["commands"]:
        blob = str(cmd).lower()
        assert "flip_live" not in blob
        assert "place_order" not in blob


def test_cascade_rects_diagonal_offset() -> None:
    assert DEFAULT_CASCADE_OFFSET_PX == 28
    rects = cascade_rects(3, 800, 600)
    assert len(rects) == 3
    assert rects[0] == {"x": 24, "y": 24, "w": 420, "h": 320}
    assert rects[1] == {"x": 52, "y": 52, "w": 420, "h": 320}
    assert rects[2] == {"x": 80, "y": 80, "w": 420, "h": 320}


def test_cascade_rects_empty_and_wrap() -> None:
    assert cascade_rects(0, 800, 600) == []
    # Tiny viewport forces wrap back to origin after first windows.
    rects = cascade_rects(5, 500, 400, offset=100, win_w=420, win_h=320)
    assert len(rects) == 5
    assert rects[0]["x"] == 24 and rects[0]["y"] == 24
    # After offset pushes past max, next resets
    assert all(r["w"] == 420 for r in rects)
    assert all(r["h"] == 320 for r in rects)


def test_tile_rects_grid_2x2() -> None:
    assert DEFAULT_TILE_GAP_PX == 4
    assert DEFAULT_TILE_MARGIN_PX == 4
    rects = tile_rects(4, 800, 600)
    assert len(rects) == 4
    # cols=2, rows=2; avail 788x588 → cell 394x294
    assert rects[0] == {"x": 4, "y": 4, "w": 394, "h": 294}
    assert rects[1] == {"x": 402, "y": 4, "w": 394, "h": 294}
    assert rects[2] == {"x": 4, "y": 302, "w": 394, "h": 294}
    assert rects[3] == {"x": 402, "y": 302, "w": 394, "h": 294}


def test_tile_rects_three_windows_2x2_grid() -> None:
    rects = tile_rects(3, 800, 600)
    assert len(rects) == 3
    # cols = ceil(sqrt(3)) = 2
    assert rects[0]["x"] == 4
    assert rects[1]["x"] > rects[0]["x"]
    assert rects[2]["y"] > rects[0]["y"]


def test_tile_rects_empty() -> None:
    assert tile_rects(0, 800, 600) == []


def test_wm_js_cascade_tile() -> None:
    js = _WM_JS.read_text(encoding="utf-8")
    assert "function cascadeRects(" in js
    assert "function tileRects(" in js
    assert "WindowManager.prototype.cascadeWindows" in js
    assert "WindowManager.prototype.tileWindows" in js
    assert "QLCascadeRects" in js
    assert "QLTileRects" in js
    assert "scheduleSave()" in js


def test_palette_and_menu_wire_cascade_tile() -> None:
    palette = _PALETTE_JS.read_text(encoding="utf-8")
    assert 'cmd.action === "cascade_windows"' in palette
    assert 'cmd.action === "tile_windows"' in palette
    assert "cascadeWindows" in palette
    assert "tileWindows" in palette

    shell = _SHELL_JS.read_text(encoding="utf-8")
    assert "cascade_windows" in shell
    assert "tile_windows" in shell
    assert "wm.cascadeWindows" in shell
    assert "wm.tileWindows" in shell

    index = _INDEX.read_text(encoding="utf-8")
    assert 'data-wm-action="cascade_windows"' in index
    assert 'data-wm-action="tile_windows"' in index
    assert 'data-i18n="menu.windows"' in index
