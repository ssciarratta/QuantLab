"""Tests leverage overlay + symbol map."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.research.sim.benchmark import compute_benchmark
from quantlab.research.sim.leverage_overlay import (
    LeverageOverlayConfig,
    apply_leverage_overlay,
)
from quantlab.research.sim.symbol_map import resolve_instrument


def test_resolve_binance_futures() -> None:
    r = resolve_instrument("BTC", venue="binance", market_type="futures")
    assert r.symbol == "BTCUSDT"
    assert r.instrument_id == "BNF:BTCUSDT"


def test_resolve_okx_futures() -> None:
    r = resolve_instrument("ETH", venue="okx", market_type="futures")
    assert r.symbol == "ETH-USDT-SWAP"
    assert r.instrument_id == "OKX:ETH-USDT-SWAP"


def test_resolve_hyperliquid() -> None:
    r = resolve_instrument("BTC", venue="hyperliquid", market_type="futures")
    assert r.symbol == "BTC"
    assert r.instrument_id == "HL:BTC"


def test_leverage_doubles_pnl() -> None:
    bt = {
        "initial_equity": "1000",
        "final_equity": "1100",
        "equity_curve_tail": [
            {"ts": "t0", "equity": "1000"},
            {"ts": "t1", "equity": "1100"},
        ],
    }
    out = apply_leverage_overlay(
        bt,
        config=LeverageOverlayConfig(
            leverage=Decimal("2"),
            simulate_liquidation=False,
            apply_funding=False,
        ),
    )
    assert out["final_equity"] == "1200"
    assert out["pnl"] == "200"


def test_liquidation_stops_curve() -> None:
    bt = {
        "initial_equity": "1000",
        "final_equity": "500",
        "equity_curve_tail": [
            {"ts": "t0", "equity": "1000"},
            {"ts": "t1", "equity": "800"},
            {"ts": "t2", "equity": "200"},
            {"ts": "t3", "equity": "500"},
        ],
    }
    out = apply_leverage_overlay(
        bt,
        config=LeverageOverlayConfig(
            leverage=Decimal("10"),
            simulate_liquidation=True,
            apply_funding=False,
            maintenance_rate=Decimal("0.05"),
        ),
    )
    assert out["liquidated"] is True
    assert out["liquidation_bar_index"] is not None


def test_funding_toggle_off() -> None:
    bt = {
        "initial_equity": "1000",
        "final_equity": "1100",
        "equity_curve_tail": [{"ts": "t0", "equity": "1000"}, {"ts": "t1", "equity": "1100"}],
    }
    out = apply_leverage_overlay(
        bt,
        config=LeverageOverlayConfig(leverage=Decimal("1"), apply_funding=False),
        funding_rates=[Decimal("0.001")],
    )
    assert out["funding_applied"] is False
    assert out["total_funding"] == "0"


def test_invalid_leverage() -> None:
    with pytest.raises(ValidationError):
        apply_leverage_overlay(
            {"initial_equity": "1000", "final_equity": "1100"},
            config=LeverageOverlayConfig(leverage=Decimal("200")),
        )


def test_benchmark_zero_duration() -> None:
    bench = compute_benchmark(
        Decimal("1000"),
        Decimal("0.10"),
        timedelta(0),
    )
    assert bench.period_return == Decimal("0")
    assert bench.to_dict()["period_return"] == "0"
