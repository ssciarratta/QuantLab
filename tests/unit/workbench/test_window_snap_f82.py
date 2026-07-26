"""Tests window edge snap geometry (F82) — Python mirror + static JS contract."""

from __future__ import annotations

from pathlib import Path

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.snap_position import DEFAULT_SNAP_THRESHOLD_PX, snap_position

_STATIC = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "quantlab"
    / "workbench"
    / "static"
)
_WM_JS = _STATIC / "js" / "wm.js"


def test_live_blocked_and_version_f82() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.74.0"
    assert PHASES_SUMMARY == "F19–F82 INTERNAL"
    assert not Path("docs/audit/FASE_82_APPROVED.md").exists()


def test_snap_position_left_and_top() -> None:
    assert DEFAULT_SNAP_THRESHOLD_PX == 12
    assert snap_position(5, 8, 200, 150, 800, 600, 12) == (0, 0)
    assert snap_position(11, 11, 200, 150, 800, 600, 12) == (0, 0)
    assert snap_position(12, 12, 200, 150, 800, 600, 12) == (12, 12)


def test_snap_position_right_and_bottom() -> None:
    # right gap = 800 - (595 + 200) = 5 < 12 → x = 600
    assert snap_position(595, 100, 200, 150, 800, 600, 12) == (600, 100)
    # bottom gap = 600 - (445 + 150) = 5 < 12 → y = 450
    assert snap_position(100, 445, 200, 150, 800, 600, 12) == (100, 450)
    # both
    assert snap_position(595, 445, 200, 150, 800, 600, 12) == (600, 450)


def test_snap_position_no_snap_when_far() -> None:
    assert snap_position(40, 50, 200, 150, 800, 600, 12) == (40, 50)
    assert snap_position(100, 100, 200, 150, 800, 600, 12) == (100, 100)


def test_snap_position_left_priority_over_right() -> None:
    # Near full-bleed: left gap 5 and right gap would also qualify after left snap.
    # Left wins via elif (prefer left edge).
    assert snap_position(5, 20, 790, 100, 800, 600, 12) == (0, 20)


def test_snap_position_negative_x_snaps_left() -> None:
    assert snap_position(-5, 30, 200, 150, 800, 600, 12) == (0, 30)


def test_wm_js_contains_snap_logic() -> None:
    js = _WM_JS.read_text(encoding="utf-8")
    assert "function snapPosition(" in js
    assert "SNAP_THRESHOLD_PX" in js
    assert "snapPosition(" in js
    assert "QLSnapPosition" in js
    assert "scheduleSave()" in js
    # Drag release applies snap then persists layout
    assert "snapped = snapPosition(" in js or "snapPosition(\n" in js
    assert "self.scheduleSave()" in js
