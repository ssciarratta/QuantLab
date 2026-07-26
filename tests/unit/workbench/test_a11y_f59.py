"""F59 — A11y basics (focus + aria) en static HTML/JS del workbench."""

from __future__ import annotations

from pathlib import Path

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY

_STATIC = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "quantlab"
    / "workbench"
    / "static"
)
_INDEX = _STATIC / "index.html"
_PALETTE_JS = _STATIC / "js" / "command_palette.js"
_ABOUT_JS = _STATIC / "js" / "about.js"
_ONBOARDING_JS = _STATIC / "js" / "onboarding.js"
_WM_JS = _STATIC / "js" / "wm.js"


def test_live_blocked_and_version_f59() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.85.0"
    assert PHASES_SUMMARY == "F19–F93 INTERNAL"


def test_index_html_contains_aria_and_role_dialog() -> None:
    html = _INDEX.read_text(encoding="utf-8")
    assert "aria-label" in html
    assert 'role="dialog"' in html
    assert html.count('role="dialog"') >= 3
    assert "Ir al contenido" in html
    assert 'href="#workspace"' in html
    assert 'aria-label="Menú inicio"' in html
    assert 'aria-label="Barra de tareas"' in html
    assert 'aria-modal="true"' in html


def test_dialog_shells_in_index() -> None:
    html = _INDEX.read_text(encoding="utf-8")
    assert 'id="command-palette"' in html
    assert 'id="about-dialog"' in html
    assert 'id="onboarding-wizard"' in html
    for label in ("Command Palette", "Acerca de QuantLab", "Onboarding QuantLab"):
        assert label in html


def test_palette_js_focus_trap_and_aria() -> None:
    js = _PALETTE_JS.read_text(encoding="utf-8")
    assert 'role", "dialog"' in js or 'role="dialog"' in js
    assert "aria-modal" in js
    assert "_trapFocus" in js
    assert 'ev.key !== "Tab"' in js or 'ev.key === "Tab"' in js
    assert "addEventListener(\"keydown\"" in js


def test_about_onboarding_aria_dialog() -> None:
    about = _ABOUT_JS.read_text(encoding="utf-8")
    onboarding = _ONBOARDING_JS.read_text(encoding="utf-8")
    assert "role" in about and "dialog" in about
    assert "aria-modal" in about
    assert "Acerca de QuantLab" in about
    assert "role" in onboarding and "dialog" in onboarding
    assert "aria-modal" in onboarding
    assert "Onboarding QuantLab" in onboarding


def test_taskbar_buttons_aria_label() -> None:
    wm = _WM_JS.read_text(encoding="utf-8")
    assert 'aria-label' in wm
    assert "Ventana " in wm
    html = _INDEX.read_text(encoding="utf-8")
    assert 'id="btn-start"' in html
    assert 'aria-label="Menú inicio"' in html


def test_no_fase_59_approved() -> None:
    root = Path(__file__).resolve().parents[3]
    assert not (root / "docs" / "audit" / "FASE_59_APPROVED.md").exists()
