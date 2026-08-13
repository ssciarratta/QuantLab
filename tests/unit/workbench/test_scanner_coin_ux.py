"""UI: Alpha Scanner — typeahead moneda + preview velas al cambiar horizonte."""

from __future__ import annotations

from pathlib import Path

STATIC = Path(__file__).resolve().parents[3] / "src/quantlab/workbench/static"


def test_scanner_has_coin_typeahead() -> None:
    js = (STATIC / "js/panes/scanner.js").read_text(encoding="utf-8")
    assert "sc-coin-suggest" in js
    assert "openCoinSuggest" in js
    assert "loadCoinCatalog" in js
    assert "pickCoin" in js
    assert "simUniverse" in js


def test_scanner_free_quantity_controls() -> None:
    """Top / N monedas / Top Kronos son inputs numéricos editables."""
    js = (STATIC / "js/panes/scanner.js").read_text(encoding="utf-8")
    assert 'id="sc-limit-mode"' in js
    assert 'id="sc-limit-n"' in js
    assert 'id="sc-kronos-top" type="number"' in js
    assert 'id="sc-top" type="number"' in js
    assert "universeMode()" in js
    assert 'max="100"' in js
    assert 'max="500"' in js


def test_scanner_instant_nbars_preview() -> None:
    js = (STATIC / "js/panes/scanner.js").read_text(encoding="utf-8")
    assert "estimateBarsLocal" in js
    assert "INTERVAL_MINUTES" in js
    assert "refreshNBars" in js
    # label muestra período × TF
    assert "×" in js
    assert 'addEventListener("change", refreshNBars)' in js


def test_scanner_js_regex_valid() -> None:
    """Un regex roto en scanner.js impide cargar el panel (Buscar no abre)."""
    js = (STATIC / "js/panes/scanner.js").read_text(encoding="utf-8")
    assert ".replace(/^[^:]+:/" in js
    assert ".replace(/^[^:]+:\\/" not in js


def test_scanner_css_hides_toolbar_labels() -> None:
    css = (STATIC / "css/workbench.css").read_text(encoding="utf-8")
    assert ".pane-scanner .sc-toolbar label[hidden]" in css
    assert "display: none !important" in css
    assert ".sc-coin-suggest" in css
