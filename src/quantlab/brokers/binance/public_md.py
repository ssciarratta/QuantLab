"""Binance public market-data client (read-only, sin API keys) — F100.

Usa endpoints públicos de Binance Spot. No envía órdenes. Fail-closed ante error.
Para demo/testnet de trading se usará otro módulo + unlock LIVE.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar

DEFAULT_BASE_URL = "https://api.binance.com"
DEFAULT_TIMEOUT_SECONDS = 10.0

# Binance API: máx 1000 klines por request. Lab permite paginar hasta MAX_KLINES_TOTAL.
MAX_KLINES_PER_REQUEST = 1000
MAX_KLINES_TOTAL = 3000  # ~50× el default histórico de 60
MIN_KLINES = 3

# Intervalos Spot públicos (sin ticks/L2). 1m = más fino disponible aquí.
ALLOWED_KLINE_INTERVALS: frozenset[str] = frozenset(
    {"1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d"}
)

_INTERVAL_ORDER: tuple[str, ...] = (
    "1m",
    "3m",
    "5m",
    "15m",
    "30m",
    "1h",
    "4h",
    "1d",
)


def _interval_sort_key(interval: str) -> int:
    try:
        return _INTERVAL_ORDER.index(interval)
    except ValueError:
        return 99


def validate_kline_interval(interval: str) -> str:
    """Normaliza y valida interval de klines Binance."""
    if not isinstance(interval, str) or not interval.strip():
        raise ValidationError("interval requerido")
    iv = interval.strip()
    if iv not in ALLOWED_KLINE_INTERVALS:
        raise ValidationError(
            f"interval inválido: {interval!r}; "
            f"permitidos: {', '.join(_INTERVAL_ORDER)}"
        )
    return iv


@dataclass(frozen=True, slots=True)
class BinancePublicTicker:
    symbol: str
    bid: Decimal | None
    ask: Decimal | None
    last: Decimal | None


class BinancePublicMdClient:
    """Cliente HTTP mínimo para MD público Binance (stdlib only)."""

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout_seconds

    def _get_json(self, path: str) -> Any:
        url = f"{self._base}{path}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "QuantLab/1.00 (+read-only-md)"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise ValidationError(f"binance MD HTTP {exc.code}: {exc.reason}") from exc
        except urllib.error.URLError as exc:
            raise ValidationError(f"binance MD red: {exc.reason}") from exc
        except TimeoutError as exc:
            raise ValidationError("binance MD timeout") from exc
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValidationError("binance MD JSON inválido") from exc

    def ping(self) -> bool:
        payload = self._get_json("/api/v3/ping")
        return isinstance(payload, dict) and len(payload) == 0

    def list_spot_symbols(self, *, quote: str = "USDT", limit: int = 50) -> list[str]:
        if limit < 1 or limit > 500:
            raise ValidationError("limit debe estar entre 1 y 500")
        info = self._get_json("/api/v3/exchangeInfo")
        symbols = info.get("symbols")
        if not isinstance(symbols, list):
            raise ValidationError("exchangeInfo sin symbols")
        out: list[str] = []
        q = quote.strip().upper()
        for item in symbols:
            if not isinstance(item, dict):
                continue
            if item.get("status") != "TRADING":
                continue
            if str(item.get("quoteAsset", "")).upper() != q:
                continue
            sym = str(item.get("symbol", "")).upper()
            if sym:
                out.append(sym)
            if len(out) >= limit:
                break
        return out

    def book_ticker(self, symbol: str) -> BinancePublicTicker:
        sym = symbol.strip().upper()
        if not sym:
            raise ValidationError("symbol vacío")
        payload = self._get_json(f"/api/v3/ticker/bookTicker?symbol={sym}")
        if not isinstance(payload, dict):
            raise ValidationError("bookTicker inválido")

        def _dec(key: str) -> Decimal | None:
            raw = payload.get(key)
            if raw is None:
                return None
            try:
                return Decimal(str(raw))
            except (InvalidOperation, ValueError):
                return None

        return BinancePublicTicker(
            symbol=str(payload.get("symbol") or sym),
            bid=_dec("bidPrice"),
            ask=_dec("askPrice"),
            last=None,
        )

    def _parse_kline_rows(self, symbol: str, interval: str, payload: object) -> list[Bar]:
        if not isinstance(payload, list):
            raise ValidationError("klines inválido")
        out: list[Bar] = []
        for row in payload:
            if not isinstance(row, list) or len(row) < 7:
                continue
            try:
                open_ms = int(row[0])
                close_ms = int(row[6])
                o = Decimal(str(row[1]))
                h = Decimal(str(row[2]))
                lo = Decimal(str(row[3]))
                c = Decimal(str(row[4]))
                vol = Decimal(str(row[5]))
            except (TypeError, ValueError, InvalidOperation) as exc:
                raise ValidationError(f"klines row inválida {symbol}") from exc
            t_open = datetime.fromtimestamp(open_ms / 1000.0, tz=UTC)
            t_close = datetime.fromtimestamp(close_ms / 1000.0, tz=UTC)
            out.append(
                Bar(
                    instrument_id=f"BN:{symbol}",
                    open=o,
                    high=h,
                    low=lo,
                    close=c,
                    volume=vol,
                    timestamp_open=t_open,
                    timestamp_close=t_close,
                    timeframe=interval,
                )
            )
        return out

    def klines(
        self,
        symbol: str,
        *,
        interval: str = "1h",
        limit: int = 24,
    ) -> list[Bar]:
        """OHLCV público → ``Bar`` (read-only).

        ``limit`` hasta ``MAX_KLINES_TOTAL`` (pagina de a 1000 hacia atrás).
        Sin ``startTime``/``endTime`` explícitos: siempre las **últimas N** velas
        hasta el momento de la consulta.
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
        # Páginas hacia atrás hasta completar N o agotar historial.
        max_pages = (MAX_KLINES_TOTAL // MAX_KLINES_PER_REQUEST) + 2
        for _ in range(max_pages):
            if remaining <= 0:
                break
            batch = min(MAX_KLINES_PER_REQUEST, remaining)
            path = f"/api/v3/klines?symbol={sym}&interval={iv}&limit={batch}"
            if end_ms is not None:
                path += f"&endTime={end_ms}"
            payload = self._get_json(path)
            chunk = self._parse_kline_rows(sym, iv, payload)
            if not chunk:
                break
            for bar in chunk:
                by_open[bar.timestamp_open] = bar
            oldest_open_ms = int(chunk[0].timestamp_open.timestamp() * 1000)
            end_ms = oldest_open_ms - 1
            remaining = limit - len(by_open)
            if len(chunk) < batch:
                break  # no hay más historial

        out = sorted(by_open.values(), key=lambda b: b.timestamp_open)
        if len(out) > limit:
            out = out[-limit:]
        if len(out) < MIN_KLINES:
            raise ValidationError(f"klines insuficientes para {sym}")
        return out


def fetch_universe_bars(
    symbols: list[str],
    *,
    interval: str = "1h",
    kline_limit: int = 24,
    base_url: str = DEFAULT_BASE_URL,
) -> dict[str, list[Bar]]:
    """Descarga klines por símbolo; omite símbolos con error."""
    client = BinancePublicMdClient(base_url=base_url)
    out: dict[str, list[Bar]] = {}
    for sym in symbols:
        try:
            out[sym] = client.klines(sym, interval=interval, limit=kline_limit)
        except ValidationError:
            continue
    return out


def scan_binance_usdt(*, limit: int = 20, base_url: str = DEFAULT_BASE_URL) -> dict[str, Any]:
    """Scan read-only: lista símbolos USDT + book ticker de los primeros."""
    client = BinancePublicMdClient(base_url=base_url)
    symbols = client.list_spot_symbols(quote="USDT", limit=limit)
    tickers: list[dict[str, Any]] = []
    for sym in symbols[: min(10, len(symbols))]:
        try:
            t = client.book_ticker(sym)
            tickers.append(
                {
                    "symbol": t.symbol,
                    "bid": None if t.bid is None else str(t.bid),
                    "ask": None if t.ask is None else str(t.ask),
                }
            )
        except ValidationError:
            continue
    return {
        "ok": True,
        "kind": "binance_public_scan",
        "venue": "binance",
        "quote": "USDT",
        "n_symbols": len(symbols),
        "symbols": symbols,
        "tickers": tickers,
        "live_routing": False,
        "read_only": True,
    }
