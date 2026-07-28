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
        assert len(g["steps"]) >= 3
        assert g["when_buy"]
        assert g["when_sell"]
        assert g["params_explained"]
        assert g["risks"]
        assert g["lab_notes"]


def test_catalog_rows_include_how_it_works() -> None:
    rows = list_strategy_catalog()
    assert len(rows) == len(STRATEGY_CATALOG)
    by_fam = {r["family"] for r in rows}
    assert "trend" in by_fam
    assert all("how_it_works" in r for r in rows)
    assert all("family_label_es" in r for r in rows)
    assert all(r["how_it_works"].get("example") for r in rows)
    assert all(r["how_it_works"].get("in_plain_words") for r in rows)


def test_lab_strategies_exposes_family_labels() -> None:
    payload = lab_strategies()
    assert payload["ok"] is True
    assert "demo" in payload["family_labels_es"]
    assert payload["family_labels_es"]["demo"] == FAMILY_LABELS_ES["demo"]
    assert payload["strategies"][0]["how_it_works"]["steps"]
    assert payload["strategies"][0]["how_it_works"]["example"]


def test_simulator_js_has_accordion_and_guide_window() -> None:
    from pathlib import Path

    js = (
        Path(__file__).resolve().parents[3]
        / "src"
        / "quantlab"
        / "workbench"
        / "static"
        / "js"
        / "panes"
        / "simulator.js"
    ).read_text(encoding="utf-8")
    assert 'data-tab="comparar"' in js
    assert 'data-tab="estrategias"' in js
    assert "sim-strat-group" in js
    assert "openStrategyGuide" in js
    assert "in_plain_words" in js
    assert "sim-fee-source" in js
    assert "optgroup" in js
    assert "how_it_works" in js
    assert "Aprender" not in js or "Guided Lab" in js
    assert 'data-tab="aprender"' not in js
    assert 'data-tab="estres"' not in js
    assert 'data-tab="practicar"' not in js


def test_start_menu_has_accordion_groups() -> None:
    from pathlib import Path

    html = (
        Path(__file__).resolve().parents[3]
        / "src"
        / "quantlab"
        / "workbench"
        / "static"
        / "index.html"
    ).read_text(encoding="utf-8")
    assert 'class="start-acc"' in html
    assert "Empezar aquí (lab)" in html
    assert html.count("<details") >= 5
