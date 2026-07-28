"""Universo de monedas + pairs en sim compare."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from quantlab.research.sim.universe import SIM_COINS, list_sim_universe
from quantlab.workbench.api import WorkbenchState, handle_get_lab_sim_universe


def test_list_sim_universe_has_full_name_and_ticker() -> None:
    payload = list_sim_universe()
    assert payload["ok"] is True
    assert len(payload["coins"]) == len(SIM_COINS)
    btc = next(c for c in payload["coins"] if c["id"] == "BTC")
    assert btc["name"] == "Bitcoin"
    assert "Bitcoin (BTC)" in btc["label"]
    assert {v["id"] for v in payload["venues"]} >= {
        "binance",
        "okx",
        "bybit",
        "hyperliquid",
    }


def test_api_sim_universe_handler() -> None:
    state = MagicMock(spec=WorkbenchState)
    out = handle_get_lab_sim_universe(state)
    assert out["kind"] == "sim_universe"
    assert out["live_blocked"] is True
    assert out["coins"][0]["label"]


def test_run_sim_compare_accepts_pairs(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from quantlab.research.sim import compare as compare_mod

    calls: list[tuple[str, str]] = []

    def fake_fetch(underlying: str, *, venue: str, market_type: str, **kwargs):  # type: ignore[no-untyped-def]
        calls.append((venue, underlying))
        raise compare_mod.ValidationError("skip-fetch-for-test")

    monkeypatch.setattr(compare_mod, "fetch_bars_for_instrument", fake_fetch)
    out = compare_mod.run_sim_compare(
        {
            "pairs": [
                {"venue": "binance", "underlying": "BTC"},
                {"venue": "okx", "underlying": "ETH"},
            ],
            "market_type": "futures",
            "leverages": [1],
            "strategy_id": "momentum",
            "interval": "1h",
            "period_days": 1,
            "initial_capital": "10000",
            "per_trade_usd": "500",
        }
    )
    assert calls == [("binance", "BTC"), ("okx", "ETH")]
    assert len(out["rows"]) == 2
    assert all(not r["ok"] for r in out["rows"])


def test_simulator_js_has_per_venue_coin_menu() -> None:
    from pathlib import Path

    js = (
        Path(__file__).resolve().parents[3]
        / "src/quantlab/workbench/static/js/panes/simulator.js"
    ).read_text(encoding="utf-8")
    assert "sim-venue-picks" in js
    assert "sim-coin-select" in js
    assert "loadUniverse" in js
    assert "pairs:" in js or "pairs =" in js
    assert "sim-symbols" not in js


def test_guided_lab_js_has_tabs() -> None:
    from pathlib import Path

    js = (
        Path(__file__).resolve().parents[3]
        / "src/quantlab/workbench/static/js/panes/guided_lab.js"
    ).read_text(encoding="utf-8")
    assert "installGuidedTabs" in js
    assert "Histórico Binance" in js
    assert "showGlTab" in js
