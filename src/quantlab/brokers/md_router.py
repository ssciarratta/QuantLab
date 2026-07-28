"""Router MD público por venue + market_type (spot/futures)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from quantlab.brokers.binance.futures_public_md import BinanceFuturesPublicMdClient
from quantlab.brokers.binance.public_md import BinancePublicMdClient, fetch_universe_bars
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.research.sim.symbol_map import ResolvedInstrument, resolve_instrument


def fetch_bars_for_instrument(
    underlying: str,
    *,
    venue: str,
    market_type: str,
    interval: str = "1h",
    kline_limit: int = 24,
) -> tuple[ResolvedInstrument, list[Bar]]:
    """Descarga klines para un subyacente en venue/modo."""
    resolved = resolve_instrument(underlying, venue=venue, market_type=market_type)
    if kline_limit < 8 or kline_limit > 3000:
        raise ValidationError("kline_limit debe estar entre 8 y 3000")

    v = resolved.venue
    mt = resolved.market_type
    sym = resolved.symbol

    if v == "binance" and mt == "spot":
        bars_map = fetch_universe_bars([sym], interval=interval, kline_limit=kline_limit)
    elif v == "binance" and mt == "futures":
        client = BinanceFuturesPublicMdClient()
        bars_map = {sym: client.klines(sym, interval=interval, limit=kline_limit)}
    elif v == "okx":
        from quantlab.brokers.okx.public_md import OkxPublicMdClient

        client = OkxPublicMdClient()
        bars_map = {sym: client.klines(sym, interval=interval, limit=kline_limit)}
    elif v == "bybit":
        from quantlab.brokers.bybit.public_md import BybitPublicMdClient

        client = BybitPublicMdClient()
        bars_map = {sym: client.klines(sym, interval=interval, limit=kline_limit)}
    elif v == "hyperliquid":
        from quantlab.brokers.hyperliquid.public_md import HyperliquidPublicMdClient

        client = HyperliquidPublicMdClient()
        bars_map = {sym: client.klines(sym, interval=interval, limit=kline_limit)}
    else:
        raise ValidationError(f"fetch no implementado: {v}/{mt}")

    bars = bars_map.get(sym)
    if not bars:
        raise ValidationError(f"sin klines para {resolved.instrument_id}")
    return resolved, bars


def fetch_funding_rates(
    resolved: ResolvedInstrument,
    *,
    limit: int = 100,
) -> list[Decimal]:
    """Rates históricos para overlay funding (vacío si spot o no disponible)."""
    if resolved.market_type != "futures":
        return []
    v = resolved.venue
    sym = resolved.symbol
    rates: list[Decimal] = []
    try:
        if v == "binance":
            client = BinanceFuturesPublicMdClient()
            for row in client.funding_rates(sym, limit=limit):
                rates.append(Decimal(row.get("fundingRate", "0")))
        elif v == "okx":
            from quantlab.brokers.okx.public_md import OkxPublicMdClient

            rates = OkxPublicMdClient().funding_rates(sym, limit=limit)
        elif v == "bybit":
            from quantlab.brokers.bybit.public_md import BybitPublicMdClient

            rates = BybitPublicMdClient().funding_rates(sym, limit=limit)
        elif v == "hyperliquid":
            from quantlab.brokers.hyperliquid.public_md import HyperliquidPublicMdClient

            rates = HyperliquidPublicMdClient().funding_rates(sym, limit=limit)
    except (ValidationError, ValueError):
        return []
    return rates
