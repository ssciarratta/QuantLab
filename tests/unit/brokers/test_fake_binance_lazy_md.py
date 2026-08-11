"""FakeBinanceBroker — MD público lazy para símbolos no listados."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch

import pytest

from quantlab.brokers.binance.fake import FakeBinanceBroker
from quantlab.brokers.binance.public_md import BinancePublicMdClient, BinancePublicTicker


def test_fake_binance_lazy_md_uniusdt() -> None:
    broker = FakeBinanceBroker()
    ticker = BinancePublicTicker(
        symbol="UNIUSDT",
        bid=Decimal("10.5"),
        ask=Decimal("10.51"),
        last=None,
    )
    with patch.object(BinancePublicMdClient, "book_ticker", return_value=ticker):
        snap = broker.get_snapshot("UNIUSDT")
    assert snap.symbol == "UNIUSDT"
    assert snap.bid == Decimal("10.5")
    assert snap.ask == Decimal("10.51")
    assert broker.get_snapshot("UNIUSDT") is snap


def test_binance_public_client_alias() -> None:
    from quantlab.brokers.binance.public_md import BinancePublicClient

    assert BinancePublicClient is BinancePublicMdClient
