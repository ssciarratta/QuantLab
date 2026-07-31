"""UX: coordinador global Stop + diálogo esperar/cortar entre corridas."""

from __future__ import annotations

from pathlib import Path

STATIC = Path(__file__).resolve().parents[3] / "src/quantlab/workbench/static"


def test_run_gate_script_and_api_signal() -> None:
    gate = (STATIC / "js/run_gate.js").read_text(encoding="utf-8")
    assert "QLRunGate" in gate
    assert "Esperar a que termine la anterior" in gate
    assert "Cortar la anterior y correr esta" in gate
    assert "bindStopButton" in gate

    api = (STATIC / "js/api.js").read_text(encoding="utf-8")
    assert "fetchOpts" in api
    assert "opts.signal = fetchOpts.signal" in api

    html = (STATIC / "index.html").read_text(encoding="utf-8")
    assert "run_gate.js" in html
    assert "sb-run-gate-stop" in html


def test_panes_have_stop_and_gate() -> None:
    sim = (STATIC / "js/panes/simulator.js").read_text(encoding="utf-8")
    assert 'id="sim-stop"' in sim
    assert "QLRunGate.begin" in sim
    assert "sim_compare" in sim
    assert "sim_rank" in sim

    mc = (STATIC / "js/panes/montecarlo.js").read_text(encoding="utf-8")
    assert "QLRunGate.begin" in mc
    assert "montecarlo" in mc
    assert ">Stop</button>" in mc

    sc = (STATIC / "js/panes/scanner.js").read_text(encoding="utf-8")
    assert 'id="sc-stop"' in sc
    assert 'kind: "scanner"' in sc

    bt = (STATIC / "js/panes/backtest.js").read_text(encoding="utf-8")
    assert 'id="bt-stop"' in bt

    css = (STATIC / "css/workbench.css").read_text(encoding="utf-8")
    assert ".ql-run-gate-modal" in css
