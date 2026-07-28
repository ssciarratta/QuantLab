"""Binance USDT-M futures public MD (read-only, sin API keys)."""

from __future__ import annotations

from datetime import datetime

from quantlab.brokers.binance.public_md import (
    ALLOWED_KLINE_INTERVALS,
    BinancePublicMdClient,
    validate_kline_interval,
)
from quantlab.brokers.md_limits import MAX_KLINES_TOTAL, MIN_KLINES
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar

DEFAULT_FUTURES_BASE_URL = "https://fapi.binance.com"

# Binance futures API: máx 1500 klines por request.
MAX_KLINES_PER_REQUEST = 1500


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
        """OHLCV futures → ``Bar`` (read-only).

        ``limit`` hasta ``MAX_KLINES_TOTAL`` (pagina de a 1500 hacia atrás).
        """
        sym = symbol.strip().upper()
        if not sym:
            raise ValidationError("symbol vacío")
        if limit < MIN_KLINES or limit > MAX_KLINES_TOTAL:
            raise ValidationError(
                f"klines limit debe estar entre {MIN_KLINES} y {MAX_KLINES_TOTAL}"
            )
        iv = validate_kline_interval(interval)

        by_open: dict[datetime, Bar] = {}
        remaining = limit
        end_ms: int | None = None
        max_pages = (MAX_KLINES_TOTAL // MAX_KLINES_PER_REQUEST) + 2
        for _ in range(max_pages):
            if remaining <= 0:
                break
            batch = min(MAX_KLINES_PER_REQUEST, remaining)
            path = f"/fapi/v1/klines?symbol={sym}&interval={iv}&limit={batch}"
            if end_ms is not None:
                path += f"&endTime={end_ms}"
            payload = self._get_json(path)
            chunk = self._parse_kline_rows(sym, iv, payload)
            for i, bar in enumerate(chunk):
                chunk[i] = Bar(
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
            if not chunk:
                break
            for bar in chunk:
                by_open[bar.timestamp_open] = bar
            oldest_open_ms = int(chunk[0].timestamp_open.timestamp() * 1000)
            end_ms = oldest_open_ms - 1
            remaining = limit - len(by_open)
            if len(chunk) < batch:
                break

        out = sorted(by_open.values(), key=lambda b: b.timestamp_open)
        if len(out) > limit:
            out = out[-limit:]
        if len(out) < MIN_KLINES:
            raise ValidationError(f"klines futures insuficientes para {sym}")
        return out

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
    "MAX_KLINES_PER_REQUEST",
    "fetch_futures_bars",
]
