"""Capital inicial/final + fees por operación en simulaciones lab."""

from __future__ import annotations

from pathlib import Path

from quantlab.workbench import lab_services


def test_backtest_exposes_capital_and_fee_per_side() -> None:
    out = lab_services.run_lab_backtest(strategy_id="buy_once", n_bars=12)
    assert out["initial_equity"] == "100000"
    assert out["final_equity"] is not None
    assert out["pnl"] is not None
    assert out["fee_per_side"]["taker_bps"] == "10"
    assert float(out["fee_per_side"]["taker_pct"]) == 0.1
    assert "as_of" in out["fee_per_side"]
    if int(out["n_fills"]) > 0:
        assert out["avg_fee_per_fill"] is not None
        assert float(out["total_fees"]) > 0


def test_montecarlo_exposes_capital_and_fee_summary(tmp_path: Path) -> None:
    out = lab_services.run_lab_montecarlo(
        n_scenarios=3,
        n_bars=12,
        seed=3,
        persist=False,
        montecarlo_root=tmp_path,
    )
    assert out["initial_equity"] == 50000.0
    assert out["capital_summary"]["initial_equity"] == 50000.0
    assert out["capital_summary"]["mean_final_equity"] == out["mean_equity"]
    fee = out["fee_summary"]
    assert fee["taker_bps"] == "10"
    assert float(fee["taker_pct"]) == 0.1
    assert fee["mean_total_fees"] is not None
    assert "Por operación" in fee["fee_per_side_note"]
