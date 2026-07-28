"""Tests fee schedules, benchmark y sizing del sim engine."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.research.sim.benchmark import (
    annual_rate_to_period_return,
    compute_benchmark,
)
from quantlab.research.sim.costs import ExtraCost, apply_extra_costs
from quantlab.research.sim.fee_schedules import (
    get_fee_schedule,
    list_fee_schedules,
)
from quantlab.research.sim.sizing import validate_trade_size
from quantlab.workbench.lab_services import make_synthetic_bars, run_lab_backtest


def test_get_fee_schedule_binance_futures() -> None:
    sched = get_fee_schedule("binance", "futures")
    assert sched.maker_bps == Decimal("2")
    assert sched.taker_bps == Decimal("5")
    assert sched.venue == "binance"


def test_get_fee_schedule_hyperliquid_spot() -> None:
    sched = get_fee_schedule("hyperliquid", "spot")
    assert sched.maker_bps == Decimal("4")
    assert sched.taker_bps == Decimal("7")


def test_list_fee_schedules_covers_all_venues() -> None:
    rows = list_fee_schedules()
    assert len(rows) == 8
    venues = {r["venue"] for r in rows}
    assert venues == {"binance", "okx", "bybit", "hyperliquid"}


def test_unknown_fee_schedule_raises() -> None:
    with pytest.raises(ValidationError):
        get_fee_schedule("kraken", "spot")


def test_benchmark_two_hours_simple() -> None:
    capital = Decimal("10000")
    annual_rate = Decimal("0.05")
    duration = timedelta(hours=2)
    expected = capital * annual_rate * (
        Decimal(str(duration.total_seconds()))
        / (Decimal("365") * Decimal("24") * Decimal("3600"))
    )
    got = annual_rate_to_period_return(capital, annual_rate, duration)
    assert got == expected
    assert got > Decimal("0")
    assert got < Decimal("1")

    bench = compute_benchmark(capital, annual_rate, duration)
    d = bench.to_dict()
    assert d["capital"] == "10000"
    assert d["annual_rate"] == "0.05"
    assert d["duration_seconds"] == "7200"
    assert d["period_return"] == str(expected)


def test_validate_trade_size_futures_ok() -> None:
    out = validate_trade_size(
        Decimal("10000"),
        Decimal("1000"),
        Decimal("5"),
        market_type="futures",
    )
    assert out["ok"] is True
    assert out["margin"] == "1000"
    assert out["notional"] == "5000"
    assert out["errors"] == []


def test_validate_trade_size_spot_notional_equals_margin() -> None:
    out = validate_trade_size(
        Decimal("5000"),
        Decimal("500"),
        Decimal("10"),
        market_type="spot",
    )
    assert out["ok"] is True
    assert out["notional"] == "500"


def test_validate_trade_size_per_trade_exceeds_capital() -> None:
    out = validate_trade_size(
        Decimal("1000"),
        Decimal("1500"),
        Decimal("2"),
        market_type="futures",
    )
    assert out["ok"] is False
    assert "per_trade excede capital" in out["errors"][0]


def test_validate_trade_size_min_notional() -> None:
    out = validate_trade_size(
        Decimal("10000"),
        Decimal("100"),
        Decimal("2"),
        min_notional=Decimal("500"),
        market_type="futures",
    )
    assert out["ok"] is False
    assert "mínimo" in out["errors"][-1]


def test_apply_extra_costs_mixed() -> None:
    costs = [
        ExtraCost("wire", "fixed_usd", Decimal("5")),
        ExtraCost("spread", "percent_notional", Decimal("0.1")),
    ]
    total = apply_extra_costs(costs=costs, notional=Decimal("10000"))
    # 5 + 10000 * 0.1 / 100 = 5 + 10 = 15
    assert total == Decimal("15")


def test_run_lab_backtest_custom_initial_cash() -> None:
    bars = make_synthetic_bars(12, instrument_id="WB:TEST")
    out = run_lab_backtest(
        strategy_id="buy_once",
        bars=bars,
        initial_cash=Decimal("5000"),
        experiment_id="sim-initial-cash-test",
    )
    assert out["initial_equity"] == "5000"
    assert out["ok"] is True
