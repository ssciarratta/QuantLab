"""UI: registro de simulaciones como ventana WM."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STATIC = ROOT / "src/quantlab/workbench/static"
CMD = ROOT / "src/quantlab/workbench/commands.py"


def test_sim_registry_is_wm_window() -> None:
    js = (STATIC / "js/sim_registry.js").read_text(encoding="utf-8")
    assert "QLSimRegistry" in js
    assert "openWindow" in js
    assert 'WIN_ID = "sim_registry"' in js
    assert "pane-sim-registry" in js
    assert "ql_sim_registry_v1" in js


def test_shell_opens_sim_registry() -> None:
    js = (STATIC / "js/shell.js").read_text(encoding="utf-8")
    assert "openSimRegistry" in js
    assert "sim_registry: openSimRegistry" in js


def test_index_menu_and_status_sim_registry() -> None:
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    assert "sim_registry.js" in html
    assert 'data-open="sim_registry"' in html
    assert 'id="sb-sim-registry"' in html
    assert 'id="ql-sim-registry"' not in html  # ya no es aside fijo


def test_registry_css_is_pane_not_fixed() -> None:
    css = (STATIC / "css/workbench.css").read_text(encoding="utf-8")
    assert ".pane-sim-registry" in css
    assert "position: absolute;\n  top: calc(var(--banner-h)" not in css


def test_simulator_registers_runs() -> None:
    js = (STATIC / "js/panes/simulator.js").read_text(encoding="utf-8")
    assert "registerSimRun" in js
    assert "QLSimRegistry" in js
    assert "register: true" in js


def test_montecarlo_memo_and_registry() -> None:
    js = (STATIC / "js/panes/montecarlo.js").read_text(encoding="utf-8")
    assert "buildMcMemo" in js
    assert "presentMcMemo" in js
    assert "QLSimRegistry" in js


def test_commands_include_sim_registry() -> None:
    text = CMD.read_text(encoding="utf-8")
    assert "open.sim_registry" in text
    assert 'pane_id": "sim_registry"' in text
