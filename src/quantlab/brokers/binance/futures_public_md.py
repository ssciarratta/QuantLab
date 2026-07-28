"""Binance USDT-M futures public MD (read-only, sin API keys)."""

from __future__ import annotations

from quantlab.brokers.binance.public_md import (
    ALLOWED_KLINE_INTERVALS,
    MAX_KLINES_PER_REQUEST,
    MAX_KLINES_TOTAL,
    MIN_KLINES,
    BinancePublicMdClient,
    validate_kline_interval,
)
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar

DEFAULT_FUTURES_BASE_URL = "https://fapi.binance.com"


class BinanceFuturesPublicMdClient(BinancePublicMdClient):
    """Klines USDT-M vía ``fapi.binance.com``."""

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_FUTURES_BASE_URL,
        timeout_seconds: float = 10.0,
    ) -> None:
        super().__init__(base_url=base_url, timeout_seconds=timeout_seconds)

    def klines(
        self,
        symbol: str,
        *,
        interval: str = "1h",
        limit: int = 24,
    ) -> list[Bar]:
        sym = symbol.strip().upper()
        if not sym:
            raise ValidationError("symbol vacío")
        if limit < MIN_KLINES or limit > MAX_KLINES_TOTAL:
            raise ValidationError(
                f"klines limit debe estar entre {MIN_KLINES} y {MAX_KLINES_TOTAL}"
            )
        iv = validate_kline_interval(interval)
        path = f"/fapi/v1/klines?symbol={sym}&interval={iv}&limit={min(limit, 1500)}"
        payload = self._get_json(path)
        bars = self._parse_kline_rows(sym, iv, payload)
        for i, bar in enumerate(bars):
            bars[i] = Bar(
                instrument_id=f"BNF:{sym}",
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
                timestamp_open=bar.timestamp_open,
                timestamp_close=bar.timestamp_close,
                timeframe=bar.timeframe,
            )
        if len(bars) < MIN_KLINES:
            raise ValidationError(f"klines futures insuficientes para {sym}")
        return bars[-limit:]

    def funding_rates(
        self,
        symbol: str,
        *,
        limit: int = 100,
    ) -> list[dict[str, str]]:
        """Historial funding (para overlay opcional)."""
        sym = symbol.strip().upper()
        lim = max(1, min(int(limit), 1000))
        path = f"/fapi/v1/fundingRate?symbol={sym}&limit={lim}"
        payload = self._get_json(path)
        if not isinstance(payload, list):
            raise ValidationError("fundingRate inválido")
        out: list[dict[str, str]] = []
        for row in payload:
            if isinstance(row, dict):
                out.append(
                    {
                        "fundingTime": str(row.get("fundingTime", "")),
                        "fundingRate": str(row.get("fundingRate", "0")),
                    }
                )
        return out


def fetch_futures_bars(
    symbols: list[str],
    *,
    interval: str = "1h",
    kline_limit: int = 24,
    base_url: str = DEFAULT_FUTURES_BASE_URL,
) -> dict[str, list[Bar]]:
    client = BinanceFuturesPublicMdClient(base_url=base_url)
    out: dict[str, list[Bar]] = {}
    for sym in symbols:
        try:
            out[sym] = client.klines(sym, interval=interval, limit=kline_limit)
        except ValidationError:
            continue
    return out


__all__ = [
    "ALLOWED_KLINE_INTERVALS",
    "BinanceFuturesPublicMdClient",
    "DEFAULT_FUTURES_BASE_URL",
    "fetch_futures_bars",
]
