"""Optimizer histórico: moneda/período + UI memo/reopen."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.research.sim.symbol_map import ResolvedInstrument
from quantlab.workbench import lab_services
from quantlab.workbench.lab_services import make_synthetic_bars

STATIC = Path(__file__).resolve().parents[3] / "src/quantlab/workbench/static"


def test_optimize_ui_has_historical_controls() -> None:
    js = (STATIC / "js/panes/optimize.js").read_text(encoding="utf-8")
    assert 'id="op-mode"' in js
    assert 'id="op-coin"' in js
    assert 'id="op-venue"' in js
    assert 'id="op-period"' in js
    assert "presentOpMemo" in js
    assert "QLSimRegistry" in js
    assert "applyPrefill" in js
    assert 'id="op-memo"' in js
    assert 'mode: "historical"' in js or "mode: 'historical'" in js


def test_registry_supports_optimize_reopen() -> None:
    reg = (STATIC / "js/sim_registry.js").read_text(encoding="utf-8")
    assert 'kind === "optimize"' in reg
    assert "renderOptimizeTable" in reg
    assert 'open("optimize"' in reg or "open('optimize'" in reg


def test_shell_optimize_prefill() -> None:
    shell = (STATIC / "js/shell.js").read_text(encoding="utf-8")
    assert "createOptimizePane" in shell
    assert "opts.prefill" in shell


def test_run_lab_optimize_historical_uses_fetched_bars() -> None:
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
        return resolved, bars

    with patch(
        "quantlab.brokers.md_router.fetch_bars_for_instrument",
        side_effect=fake_fetch,
    ):
        out = lab_services.run_lab_optimize(
            lookbacks=(2, 3),
            quantities=("1",),
            mode="historical",
            venue="binance",
            underlying="BTC",
            market_type="futures",
            interval="1h",
            n_bars=40,
            persist=False,
        )
    assert out["ok"] is True
    assert out["mode"] == "historical"
    assert out["venue"] == "binance"
    assert out["underlying"] == "BTC"
    assert out["context"]["mode"] == "historical"
    assert out["n_bars"] == 40
    assert out["n_trials"] >= 1


def test_run_lab_optimize_historical_requires_coin() -> None:
    with pytest.raises(ValidationError, match="venue y moneda"):
        lab_services.run_lab_optimize(
            mode="historical",
            venue="",
            underlying="",
            persist=False,
        )


def test_run_lab_optimize_synthetic_still_works() -> None:
    out = lab_services.run_lab_optimize(
        lookbacks=(2, 3),
        n_bars=16,
        mode="synthetic",
        persist=False,
    )
    assert out["ok"] is True
    assert out.get("mode") == "synthetic"
    assert out["data_source"] == "synthetic"
