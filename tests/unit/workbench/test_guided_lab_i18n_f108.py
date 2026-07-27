"""Tests Guided Lab i18n + venue-aware UX (F108)."""

from __future__ import annotations

import json
from pathlib import Path


def test_guided_lab_i18n_keys_parity() -> None:
    root = Path(__file__).resolve().parents[3]
    es = json.loads((root / "src/quantlab/workbench/static/i18n/es.json").read_text(encoding="utf-8"))
    en = json.loads((root / "src/quantlab/workbench/static/i18n/en.json").read_text(encoding="utf-8"))
    gl_es = {k for k in es if k.startswith("guided_lab.")}
    gl_en = {k for k in en if k.startswith("guided_lab.")}
    assert gl_es == gl_en
    assert len(gl_es) >= 40


def test_guided_lab_uses_i18n_and_venue_sections() -> None:
    js = (
        Path(__file__).resolve().parents[3]
        / "src"
        / "quantlab"
        / "workbench"
        / "static"
        / "js"
        / "panes"
        / "guided_lab.js"
    ).read_text(encoding="utf-8")
    assert "function t(key, fallback)" in js
    assert "data-i18n=" in js
    assert "applyVenueUi" in js
    assert "gl-section-a3" in js
    assert "gl-section-demo" in js
    assert "QLi18n.applyDom(root)" in js
    assert Path("docs/FASE_108_GUIDED_LAB_I18N.md").is_file()
