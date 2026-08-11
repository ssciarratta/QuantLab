"""Filtros de universo Binance spot: stablecoins + símbolos HTTP-safe (ASCII)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from quantlab.brokers.binance.public_md import (
    BinancePublicMdClient,
    is_http_safe_symbol,
    is_stablecoin_base,
)
from quantlab.core.exceptions import ValidationError


def test_is_stablecoin_base_variants() -> None:
    assert is_stablecoin_base("USDC") is True
    assert is_stablecoin_base("USDCUSDT") is True
    assert is_stablecoin_base("FDUSD") is True
    assert is_stablecoin_base("BTC") is False
    assert is_stablecoin_base("HOTUSDT") is False
    assert is_stablecoin_base("HOT") is False


def test_is_http_safe_symbol() -> None:
    assert is_http_safe_symbol("BTCUSDT") is True
    assert is_http_safe_symbol("HOTUSDT") is True
    assert is_http_safe_symbol("币安人生USDT") is False
    assert is_http_safe_symbol("BTC-USDT") is False
    assert is_http_safe_symbol("") is False


def test_list_spot_symbols_skips_stable_bases() -> None:
    client = BinancePublicMdClient()
    client._get_json = MagicMock(  # type: ignore[method-assign]
        return_value={
            "symbols": [
                {
                    "symbol": "BTCUSDT",
                    "status": "TRADING",
                    "baseAsset": "BTC",
                    "quoteAsset": "USDT",
                },
                {
                    "symbol": "USDCUSDT",
                    "status": "TRADING",
                    "baseAsset": "USDC",
                    "quoteAsset": "USDT",
                },
                {
                    "symbol": "FDUSDUSDT",
                    "status": "TRADING",
                    "baseAsset": "FDUSD",
                    "quoteAsset": "USDT",
                },
                {
                    "symbol": "HOTUSDT",
                    "status": "TRADING",
                    "baseAsset": "HOT",
                    "quoteAsset": "USDT",
                },
                {
                    "symbol": "TUSDUSDT",
                    "status": "TRADING",
                    "baseAsset": "TUSD",
                    "quoteAsset": "USDT",
                },
                {
                    "symbol": "ETHUSDT",
                    "status": "TRADING",
                    "baseAsset": "ETH",
                    "quoteAsset": "USDT",
                },
            ]
        }
    )
    syms = client.list_spot_symbols(quote="USDT", limit=10)
    assert syms == ["BTCUSDT", "HOTUSDT", "ETHUSDT"]
    assert "USDCUSDT" not in syms
    assert "FDUSDUSDT" not in syms


def test_list_spot_symbols_skips_non_ascii() -> None:
    """Regresión: CJK en symbol tumba urllib encode('ascii') del Scanner."""
    client = BinancePublicMdClient()
    client._get_json = MagicMock(  # type: ignore[method-assign]
        return_value={
            "symbols": [
                {
                    "symbol": "BTCUSDT",
                    "status": "TRADING",
                    "baseAsset": "BTC",
                    "quoteAsset": "USDT",
                },
                {
                    "symbol": "币安人生USDT",
                    "status": "TRADING",
                    "baseAsset": "币安人生",
                    "quoteAsset": "USDT",
                },
                {
                    "symbol": "ETHUSDT",
                    "status": "TRADING",
                    "baseAsset": "ETH",
                    "quoteAsset": "USDT",
                },
            ]
        }
    )
    syms = client.list_spot_symbols(quote="USDT", limit=10)
    assert syms == ["BTCUSDT", "ETHUSDT"]


def test_klines_rejects_non_ascii_symbol() -> None:
    client = BinancePublicMdClient()
    with pytest.raises(ValidationError, match="no-ASCII"):
        client.klines("币安人生USDT", interval="1h", limit=24)
