"""Tests Guided Lab A3 snapshot (F106)."""

from __future__ import annotations

from pathlib import Path

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY


def test_version_f106() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.99.0"
    assert PHASES_SUMMARY == "F19–F107 INTERNAL"
    assert not Path("docs/audit/FASE_106_APPROVED.md").exists()


def test_guided_lab_has_a3_snapshot() -> None:
    root = Path(__file__).resolve().parents[3] / "src" / "quantlab" / "workbench" / "static"
    js = (root / "js" / "panes" / "guided_lab.js").read_text(encoding="utf-8")
    assert "gl-a3-snap" in js
    assert "QLApi.snapshot" in js
    assert "gl-a3-sym" in js
    assert Path("docs/FASE_106_A3_SNAPSHOT_GUIDED.md").is_file()
