"""Shared pytest fixtures."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quantlab.core.types.market import (
    Instrument,
)


@pytest.fixture
def utc_now() -> datetime:
    return datetime.now(UTC)


@pytest.fixture
def sample_instrument() -> Instrument:
    return Instrument.create(
        symbol="BTC-USDT",
        base_asset="BTC",
        quote_asset="USDT",
        tick_size=0.01,
        lot_size=0.001,
        min_notional=10.0,
        metadata={"exchange": "binance"},
    )
