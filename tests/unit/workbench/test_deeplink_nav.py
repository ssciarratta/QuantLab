"""Smoke deep-link / nav estático Workbench."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STATIC = ROOT / "src" / "quantlab" / "workbench" / "static"


def test_index_includes_nav_js() -> None:
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    assert "/static/js/nav.js" in html
    assert "montecarlo.js" in html


def test_nav_js_exports_qlnav() -> None:
    src = (STATIC / "js" / "nav.js").read_text(encoding="utf-8")
    assert "global.QLNav" in src
    assert "setFocus" in src
    assert "takeFocus" in src
    assert "open:" in src or "open =" in src or "function open" in src


def test_montecarlo_uses_qlnav_open() -> None:
    src = (STATIC / "js" / "panes" / "montecarlo.js").read_text(encoding="utf-8")
    assert "applyNavFocus" in src
    assert "QLNav" in src
    assert 'mode: bt ? "normal" : "technical_lab"' in src


def test_reports_has_montecarlo_button() -> None:
    src = (STATIC / "js" / "panes" / "reports.js").read_text(encoding="utf-8")
    assert "rp-to-mc" in src
    assert "applyNavFocus" in src


def test_backtest_has_montecarlo_button() -> None:
    src = (STATIC / "js" / "panes" / "backtest.js").read_text(encoding="utf-8")
    assert "bt-to-mc" in src
    assert "montecarlo" in src


def test_guided_lab_has_montecarlo_button() -> None:
    src = (STATIC / "js" / "panes" / "guided_lab.js").read_text(encoding="utf-8")
    assert "gl-to-mc" in src
    assert "applyNavFocus" in src
