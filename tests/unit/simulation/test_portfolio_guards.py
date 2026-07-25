"""Guardias PortfolioTracker anti-NaN / avg_entry."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import OrderSide
from quantlab.simulation.portfolio_tracker import PortfolioTracker


def test_mark_equity_rejects_nan_mark() -> None:
    tracker = PortfolioTracker(cash_asset="USDT", cash=Decimal("1000"))
    tracker.apply_fill(
        instrument_id="X",
        side=OrderSide.BUY,
        quantity=Decimal("1"),
        price=Decimal("10"),
        fee=Decimal("0"),
    )
    with pytest.raises(ValidationError):
        tracker.mark_equity(
            {"X": Decimal("NaN")},
            datetime(2024, 1, 1, tzinfo=UTC),
        )


def test_avg_entry_weighted() -> None:
    tracker = PortfolioTracker(cash_asset="USDT", cash=Decimal("10000"))
    tracker.apply_fill(
        instrument_id="X",
        side=OrderSide.BUY,
        quantity=Decimal("2"),
        price=Decimal("10"),
        fee=Decimal("0"),
    )
    tracker.apply_fill(
        instrument_id="X",
        side=OrderSide.BUY,
        quantity=Decimal("2"),
        price=Decimal("20"),
        fee=Decimal("0"),
    )
    assert tracker.positions["X"].avg_entry == Decimal("15")
