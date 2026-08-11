"""Tests universo multi-producto (A3 + HL meta + contract kind)."""

from __future__ import annotations

from quantlab.research.sim.symbol_map import resolve_instrument
from quantlab.research.sim.universe import list_sim_universe, tradingview_url


def test_list_sim_universe_includes_a3_and_contract_meta() -> None:
    payload = list_sim_universe(market_type="futures", hl_live=False)
    assert payload["ok"] is True
    venues = {v["id"] for v in payload["venues"]}
    assert "a3" in venues
    assert "hyperliquid" in venues
    a3 = payload["products_by_venue"]["a3"]
    assert any(p["id"].startswith("SOJ/") for p in a3)
    assert any(p["has_daily_variation"] for p in a3)
    assert all(p.get("expiry_label") for p in a3)
    assert all(p.get("margin_note") for p in a3)
    bn = payload["products_by_venue"]["binance"]
    assert bn[0]["contract_kind"] == "perpetual"
    assert bn[0]["has_daily_variation"] is False


def test_resolve_a3_keeps_ticker_with_slash() -> None:
    r = resolve_instrument("SOJ/MAY26", venue="a3", market_type="futures")
    assert r.symbol == "SOJ/MAY26"
    assert r.instrument_id == "A3:SOJ/MAY26"


def test_tradingview_url_binance_and_a3() -> None:
    assert "BINANCE" in (tradingview_url(venue="binance", symbol="BTCUSDT", market_type="futures") or "")
    assert "tradingview.com" in (tradingview_url(venue="a3", symbol="SOJ/MAY26", market_type="futures") or "")


def test_resolve_hl_hip3_preserves_case() -> None:
    r = resolve_instrument("xyz:GOLD", venue="hyperliquid", market_type="futures")
    assert r.symbol == "xyz:GOLD"
    assert r.instrument_id == "HL:xyz:GOLD"


def test_hl_asset_kind_commodity() -> None:
    from quantlab.research.sim.universe import _hl_asset_kind

    assert _hl_asset_kind("xyz:GOLD", is_core=False) == "commodity"
    assert _hl_asset_kind("xyz:TSLA", is_core=False) == "equity"
    assert _hl_asset_kind("BTC", is_core=True) == "crypto"


def test_simulator_js_auto_add_and_sort_rentab() -> None:
    from pathlib import Path

    js = (
        Path(__file__).resolve().parents[3]
        / "src/quantlab/workbench/static/js/panes/simulator.js"
    ).read_text(encoding="utf-8")
    assert "autoAddSameTickerToChecked" in js
    assert "findProductIdByTicker" in js
    assert "fee-op" in js
    assert "pnl_pct" in js
    assert "sort(function (a, b)" in js


def test_simulator_js_has_product_search() -> None:
    from pathlib import Path

    js = (
        Path(__file__).resolve().parents[3]
        / "src/quantlab/workbench/static/js/panes/simulator.js"
    ).read_text(encoding="utf-8")
    assert "sim-coin-search" in js
    assert "SEARCH_ALIASES" in js
    assert "petroleo" in js
    assert "sortByLabel" in js
    assert "expandSearchQuery" in js


def test_simulator_js_has_a3_and_margin_warn() -> None:
    from pathlib import Path

    js = (
        Path(__file__).resolve().parents[3]
        / "src/quantlab/workbench/static/js/panes/simulator.js"
    ).read_text(encoding="utf-8")
    assert '"a3"' in js or "'a3'" in js
    assert "maybeWarnMargin" in js
    assert "products_by_venue" in js or "productsByVenue" in js
    assert "tradingview_url" in js or "sim-tv-link" in js
