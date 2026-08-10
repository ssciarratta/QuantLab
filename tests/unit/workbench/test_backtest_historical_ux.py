"""Backtest histórico: moneda/período + UI memo/reopen."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.research.sim.symbol_map import ResolvedInstrument
from quantlab.workbench import lab_services
from quantlab.workbench.lab_services import make_synthetic_bars

STATIC = Path(__file__).resolve().parents[3] / "src/quantlab/workbench/static"


def test_backtest_ui_has_historical_controls() -> None:
    js = (STATIC / "js/panes/backtest.js").read_text(encoding="utf-8")
    assert 'id="bt-mode"' in js
    assert 'id="bt-coin"' in js
    assert 'id="bt-venue"' in js
    assert 'id="bt-period"' in js
    assert "mode: \"historical\"" in js or "mode: 'historical'" in js
    assert "presentBtMemo" in js
    assert "QLSimRegistry" in js
    assert "applyPrefill" in js
    assert 'id="bt-memo"' in js


def test_registry_supports_backtest_reopen() -> None:
    reg = (STATIC / "js/sim_registry.js").read_text(encoding="utf-8")
    assert 'kind === "backtest"' in reg
    assert "renderBacktestTable" in reg
    assert 'open("backtest"' in reg or "open('backtest'" in reg


def test_shell_backtest_prefill() -> None:
    shell = (STATIC / "js/shell.js").read_text(encoding="utf-8")
    assert "opts.prefill" in shell
    # openBacktest applies prefill
    assert "createBacktestPane" in shell


def test_run_market_lab_backtest_uses_fetched_bars() -> None:
    bars = make_synthetic_bars(40)
    resolved = ResolvedInstrument(
        venue="binance",
        market_type="futures",
        underlying="BTC",
        symbol="BTCUSDT",
        instrument_id="BNF:BTCUSDT",
    )

    def fake_fetch(underlying, **kwargs):  # noqa: ANN001, ANN003
        assert underlying == "BTC"
        assert kwargs.get("venue") == "binance"
        return resolved, bars

    with patch(
        "quantlab.brokers.md_router.fetch_bars_for_instrument",
        side_effect=fake_fetch,
    ):
        out = lab_services.run_market_lab_backtest(
            strategy_id="buy_once",
            venue="binance",
            underlying="BTC",
            market_type="futures",
            interval="1h",
            n_bars=40,
            initial_cash=None,
            reports_dir=None,
        )
    assert out["ok"] is True
    assert out["mode"] == "historical"
    assert out["venue"] == "binance"
    assert out["underlying"] == "BTC"
    assert out["data_source"].startswith("binance_")
    assert out["context"]["mode"] == "historical"
    assert out["n_bars"] == 40


def test_run_market_lab_backtest_requires_coin() -> None:
    with pytest.raises(ValidationError, match="venue y moneda"):
        lab_services.run_market_lab_backtest(
            strategy_id="buy_once",
            venue="",
            underlying="",
        )


def test_api_synthetic_still_default_without_venue(tmp_path: Path) -> None:
    from quantlab.workbench.api import WorkbenchState, handle_post_lab_backtest
    from quantlab.workbench.session import WorkbenchSession

    session = WorkbenchSession.create_or_load(tmp_path, "bt-hist")
    state = WorkbenchState(session=session)
    state.ensure_session()
    out = handle_post_lab_backtest(
        state,
        {"strategy_id": "buy_once", "n_bars": 12, "mode": "synthetic"},
    )
    assert out["ok"] is True
    assert out.get("mode") == "synthetic" or out.get("data_source") == "synthetic"
