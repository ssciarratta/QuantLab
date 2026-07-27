"""Tests Guided Lab A3 paper path (F104)."""

from __future__ import annotations

from pathlib import Path

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY


def test_version_f104() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.96.0"
    assert PHASES_SUMMARY == "F19–F104 INTERNAL"
    assert not Path("docs/audit/FASE_104_APPROVED.md").exists()


def test_guided_lab_has_a3_connect() -> None:
    root = Path(__file__).resolve().parents[3] / "src" / "quantlab" / "workbench" / "static"
    js = (root / "js" / "panes" / "guided_lab.js").read_text(encoding="utf-8")
    assert "gl-a3-connect" in js
    assert 'QLApi.connect("a3"' in js or "QLApi.connect('a3'" in js
    assert "gl-a3-instr" in js
    assert "instruments()" in js
    assert Path("docs/FASE_104_GUIDED_LAB_A3.md").is_file()
