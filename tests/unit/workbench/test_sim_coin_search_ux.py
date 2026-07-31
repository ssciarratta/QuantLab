"""Simulador UX: sin monedas default, búsqueda on-demand, MC desde selección."""

from __future__ import annotations

from pathlib import Path

STATIC = Path(__file__).resolve().parents[3] / "src/quantlab/workbench/static"


def test_simulator_no_default_btc_eth_selection() -> None:
    js = (STATIC / "js/panes/simulator.js").read_text(encoding="utf-8")
    assert 'vid === "binance" ? ["BTC", "ETH"]' not in js
    assert "selectedByVenue[vid] = []" in js
    assert 'binance: false' in js


def test_simulator_coin_list_hidden_until_search() -> None:
    js = (STATIC / "js/panes/simulator.js").read_text(encoding="utf-8")
    assert "listOpen" in js
    assert "escribí para buscar" in js
    assert '(listOpen ? "" : " hidden")' in js
    css = (STATIC / "css/workbench.css").read_text(encoding="utf-8")
    assert ".sim-coin-select[hidden]" in css


def test_simulator_mc_button_from_selection() -> None:
    js = (STATIC / "js/panes/simulator.js").read_text(encoding="utf-8")
    assert "sim-open-mc-sel" in js
    assert "Monte Carlo con esta selección" in js
    assert "Monte Carlo con esta corrida" in js
    assert "sim-compare-mc-btn" in js
    assert "openMonteCarloFromSelection" in js
    assert "syncMcSelHint" in js
