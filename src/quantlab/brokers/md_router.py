"""Router MD público por venue + market_type (spot/futures)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from quantlab.brokers.binance.futures_public_md import BinanceFuturesPublicMdClient
from quantlab.brokers.binance.public_md import fetch_universe_bars
from quantlab.brokers.md_limits import LAB_KLINE_LIMIT_MAX, LAB_KLINE_LIMIT_MIN
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.research.sim.symbol_map import ResolvedInstrument, resolve_instrument


def _fetch_a3_bars(
    symbol: str,
    *,
    interval: str,
    kline_limit: int,
) -> list[Bar]:
    """Barras A3: trades del backend (fake o MD env) → OHLCV."""
    from quantlab.brokers.a3.md_backend import resolve_a3_md_backend, try_build_env_md_backend
    from quantlab.data.exchanges.a3.mappers import trade_dto_to_domain
    from quantlab.data.normalization.bars import build_bars_from_trades

    env_b, _reason = try_build_env_md_backend()
    if env_b is not None:
        backend = env_b
    else:
        backend, _meta = resolve_a3_md_backend("fake")
    if hasattr(backend, "connect"):
        backend.connect()

    end = datetime.now(tz=UTC)
    start = end - timedelta(days=max(45, kline_limit))
    try:
        dtos = backend.get_historical_trades(symbol, start, end)
    except Exception as exc:  # noqa: BLE001
        raise ValidationError(
            f"A3 sin trades para {symbol}: {exc}. "
            "Con MD real (QUANTLAB_A3_MD_READONLY=1) Guided Lab lista vigentes."
        ) from exc

    trades = [trade_dto_to_domain(d) for d in dtos]
    if not trades:
        raise ValidationError(
            f"A3 sin trades en ventana para {symbol}. "
            "Fake lab incluye series demo de soja/maíz/trigo/DLR."
        )

    try:
        build = build_bars_from_trades(
            trades,
            timeframe=interval,
            instrument_id=f"a3:{symbol}",
        )
    except Exception as exc:  # noqa: BLE001
        raise ValidationError(
            f"A3 no pudo armar velas {interval} para {symbol}: {exc}. "
            "Timeframes A3 lab: 1m,5m,15m,30m,1h,1d."
        ) from exc

    bars = list(build.bars)
    if len(bars) > kline_limit:
        bars = bars[-kline_limit:]
    if len(bars) < LAB_KLINE_LIMIT_MIN:
        raise ValidationError(
            f"A3: pocas barras ({len(bars)}) para {symbol}."
        )
    return bars


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
    if kline_limit < LAB_KLINE_LIMIT_MIN or kline_limit > LAB_KLINE_LIMIT_MAX:
        raise ValidationError(
            f"kline_limit debe estar entre {LAB_KLINE_LIMIT_MIN} y {LAB_KLINE_LIMIT_MAX}"
        )

    v = resolved.venue
    mt = resolved.market_type
    sym = resolved.symbol

    if v == "binance" and mt == "spot":
        bars_map = fetch_universe_bars([sym], interval=interval, kline_limit=kline_limit)
    elif v == "binance" and mt == "futures":
        bn_fut = BinanceFuturesPublicMdClient()
        bars_map = {sym: bn_fut.klines(sym, interval=interval, limit=kline_limit)}
    elif v == "okx":
        from quantlab.brokers.okx.public_md import OkxPublicMdClient

        okx = OkxPublicMdClient()
        bars_map = {sym: okx.klines(sym, interval=interval, limit=kline_limit)}
    elif v == "bybit":
        from quantlab.brokers.bybit.public_md import BybitPublicMdClient

        bybit = BybitPublicMdClient()
        bars_map = {sym: bybit.klines(sym, interval=interval, limit=kline_limit)}
    elif v == "hyperliquid":
        from quantlab.brokers.hyperliquid.public_md import HyperliquidPublicMdClient

        hl = HyperliquidPublicMdClient()
        bars_map = {sym: hl.klines(sym, interval=interval, limit=kline_limit)}
    elif v == "a3":
        a3_bars = _fetch_a3_bars(sym, interval=interval, kline_limit=kline_limit)
        return resolved, a3_bars
    else:
        raise ValidationError(f"fetch no implementado: {v}/{mt}")

    bars_raw = bars_map.get(sym)
    if not bars_raw:
        raise ValidationError(f"sin klines para {resolved.instrument_id}")
    return resolved, list(bars_raw)


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
