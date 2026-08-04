"""Stablecoins no deben entrar al universo automático Binance spot."""

from __future__ import annotations

from unittest.mock import MagicMock

from quantlab.brokers.binance.public_md import (
    BinancePublicMdClient,
    is_stablecoin_base,
)


def test_is_stablecoin_base_variants() -> None:
    assert is_stablecoin_base("USDC") is True
    assert is_stablecoin_base("USDCUSDT") is True
    assert is_stablecoin_base("FDUSD") is True
    assert is_stablecoin_base("BTC") is False
    assert is_stablecoin_base("HOTUSDT") is False
    assert is_stablecoin_base("HOT") is False


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
