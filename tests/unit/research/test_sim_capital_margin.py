"""Tests capital modes + margen pico / shortfall."""

from __future__ import annotations

from decimal import Decimal

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.research.sim.sizing import (
    build_margin_report,
    estimate_peak_margin_from_fills,
    validate_trade_size,
)


def test_unconstrained_allows_per_trade_above_dummy_capital() -> None:
    out = validate_trade_size(
        Decimal("100"),
        Decimal("500"),
        Decimal("5"),
        market_type="futures",
        capital_mode="unconstrained",
    )
    assert out["ok"] is True
    assert out["margin"] == "500"
    assert out["notional"] == "2500"
    assert out["capital_mode"] == "unconstrained"


def test_fixed_still_rejects_per_trade_over_capital() -> None:
    out = validate_trade_size(
        Decimal("100"),
        Decimal("500"),
        Decimal("2"),
        market_type="futures",
        capital_mode="fixed",
    )
    assert out["ok"] is False


def test_bad_capital_mode() -> None:
    with pytest.raises(ValidationError):
        validate_trade_size(
            Decimal("1000"),
            Decimal("100"),
            Decimal("1"),
            capital_mode="infinite",
        )


def test_peak_margin_from_fills_futures() -> None:
    fills = [
        {"side": "buy", "quantity": "2", "price": "100"},
        {"side": "sell", "quantity": "1", "price": "110"},
    ]
    # After buy: notional 200 → margin 200/10=20; after sell: qty 1 → notional 110 → margin 11
    out = estimate_peak_margin_from_fills(
        fills,
        leverage=Decimal("10"),
        market_type="futures",
        margin_per_trade=Decimal("20"),
    )
    assert out["peak_notional"] == "200"
    assert out["peak_margin"] == "20"


def test_margin_report_fixed_shortfall() -> None:
    fills = [{"side": "buy", "quantity": "10", "price": "100"}]
    # spot: peak margin = 1000; capital 500 → shortfall 500
    rep = build_margin_report(
        capital_mode="fixed",
        initial_capital=Decimal("500"),
        per_trade=Decimal("100"),
        leverage=Decimal("1"),
        market_type="spot",
        fills=fills,
    )
    assert rep["needed_more_money"] is True
    assert Decimal(rep["capital_shortfall"]) == Decimal("500")
    assert Decimal(rep["peak_margin"]) == Decimal("1000")
    assert rep["margin_per_trade"] == "100"


def test_margin_report_unconstrained_required() -> None:
    fills = [{"side": "buy", "quantity": "1", "price": "250"}]
    rep = build_margin_report(
        capital_mode="unconstrained",
        initial_capital=None,
        per_trade=Decimal("100"),
        leverage=Decimal("5"),
        market_type="futures",
        fills=fills,
    )
    # notional 250 / 5 = 50
    assert rep["capital_mode"] == "unconstrained"
    assert Decimal(rep["peak_margin"]) == Decimal("50")
    assert Decimal(rep["capital_required"]) == Decimal("50")
    assert rep["needed_more_money"] is False
    assert rep["initial_capital"] is None
