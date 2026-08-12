"""Guías how_it_works del catálogo de estrategias."""

from __future__ import annotations

from quantlab.workbench.lab_services import lab_strategies
from quantlab.workbench.strategy_catalog import STRATEGY_CATALOG, list_strategy_catalog
from quantlab.workbench.strategy_guides import FAMILY_LABELS_ES, get_strategy_guide


def test_every_strategy_has_guide() -> None:
    for m in STRATEGY_CATALOG:
        g = get_strategy_guide(m.id)
        assert g["id"] == m.id
        assert g["idea"]
        assert g["in_plain_words"]
        assert g["example"]
        assert len(g["example"]) >= 80
        assert len(g["steps"]) >= 5
        assert g["example_steps"]
        assert len(g["example_steps"]) >= 4
        assert g["when_buy"]
        assert g["when_sell"]
        assert g["params_explained"]
        assert g["risks"]
        assert g["lab_notes"]
        assert g.get("when_to_use")
        assert isinstance(g["when_to_use"], list)
        assert len(g["when_to_use"]) >= 1


def test_catalog_rows_include_how_it_works() -> None:
    rows = list_strategy_catalog()
    assert len(rows) == len(STRATEGY_CATALOG)
    by_fam = {r["family"] for r in rows}
    assert "trend" in by_fam
    assert all("how_it_works" in r for r in rows)
    assert all("family_label_es" in r for r in rows)
    assert all(r["how_it_works"].get("example") for r in rows)
    assert all(r["how_it_works"].get("example_steps") for r in rows)
    assert all(r["how_it_works"].get("in_plain_words") for r in rows)
    assert all(r["how_it_works"].get("when_to_use") for r in rows)


def test_lab_strategies_exposes_family_labels() -> None:
    payload = lab_strategies()
    assert payload["ok"] is True
    assert "demo" in payload["family_labels_es"]
    assert payload["family_labels_es"]["demo"] == FAMILY_LABELS_ES["demo"]
    assert payload["strategies"][0]["how_it_works"]["steps"]
    assert payload["strategies"][0]["how_it_works"]["example"]
    assert payload["strategies"][0]["how_it_works"]["example_steps"]


def test_simulator_js_has_accordion_and_guide_window() -> None:
    from static_test_helpers import read_static

    sim_js = read_static("js/panes/simulator.js")
    strat_js = read_static("js/panes/strategies.js")
    assert 'data-panel="comparar"' in sim_js
    assert "sim-open-strategies" in sim_js
    assert "Guías de estrategias" in strat_js or "Guías" in strat_js
    assert "example_steps" in strat_js
    assert "when_to_use" in strat_js
    assert "how_it_works" in strat_js


def test_start_menu_has_accordion_groups() -> None:
    from static_test_helpers import read_static

    html = read_static("index.html")
    assert 'class="start-acc"' in html
    assert "Barra rápida" in html
    assert html.count("<details") >= 5
