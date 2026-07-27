"""Tests Guided Lab A3 paper submit (F107)."""

from __future__ import annotations

from pathlib import Path

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY


def test_version_f107() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.99.0"
    assert PHASES_SUMMARY == "F19–F107 INTERNAL"
    assert not Path("docs/audit/FASE_107_APPROVED.md").exists()


def test_guided_lab_has_a3_paper_submit() -> None:
    root = Path(__file__).resolve().parents[3] / "src" / "quantlab" / "workbench" / "static"
    js = (root / "js" / "panes" / "guided_lab.js").read_text(encoding="utf-8")
    assert "gl-a3-paper" in js
    assert "QLApi.paperSubmit" in js
    assert "gl-a3-qty" in js
    assert Path("docs/FASE_107_GUIDED_LAB_A3_PAPER_SUBMIT.md").is_file()
