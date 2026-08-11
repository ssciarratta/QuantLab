"""UI: Monte Carlo hereda contexto del Simulador (moneda + params)."""

from __future__ import annotations

from pathlib import Path

STATIC = Path(__file__).resolve().parents[3] / "src/quantlab/workbench/static"


def test_simulator_builds_mc_handoff() -> None:
    js = (STATIC / "js/panes/simulator.js").read_text(encoding="utf-8")
    assert "buildSimHandoff" in js
    assert "formatHandoffBlock" in js
    assert "sim_context" in js
    assert "IDENTIDAD DE ESTA CORRIDA" in js
    assert 'QLShell.open("montecarlo"' in js
    assert "freezeHandoffCapital" in js
    assert "lastSimHandoff" in js
    assert "Preferir snapshot" in js


def test_montecarlo_shows_source_banner() -> None:
    js = (STATIC / "js/panes/montecarlo.js").read_text(encoding="utf-8")
    assert "mc-source-banner" in js
    assert "setSimContext" in js
    assert "renderSourceBanner" in js
    assert "CONTEXTO ORIGEN" in js
    assert "sim_context" in js
    assert "applyPrefill" in js


def test_montecarlo_banner_css() -> None:
    css = (STATIC / "css/workbench.css").read_text(encoding="utf-8")
    assert "mc-source-banner" in css
    assert "mc-source-linked" in css


def test_montecarlo_confirms_identity_before_run() -> None:
    js = (STATIC / "js/panes/montecarlo.js").read_text(encoding="utf-8")
    assert "confirmRunIdentity" in js
    assert "formatConfirmIdentity" in js
    assert "Vas a estresar ESTA simulación" in js
    assert "body.sim_context = ctx" in js or "body.sim_context = ctx" in js
    assert "sim_context" in js
    assert "getSimHandoff" in (STATIC / "js/shell.js").read_text(encoding="utf-8")
