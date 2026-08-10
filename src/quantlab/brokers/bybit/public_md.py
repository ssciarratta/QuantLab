"""Bybit public market-data client (read-only, sin API keys)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from quantlab.brokers.md_limits import MAX_KLINES_TOTAL, MIN_KLINES
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar

DEFAULT_BASE_URL = "https://api.bybit.com"
DEFAULT_TIMEOUT_SECONDS = 10.0

MAX_KLINES_PER_REQUEST = 1000

_BYBIT_INTERVAL: dict[str, str] = {
    "1m": "1",
    "3m": "3",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "1h": "60",
    "2h": "120",
    "4h": "240",
    "6h": "360",
    "12h": "720",
    "1d": "D",
    "1w": "W",
    "1M": "M",
}

_INTERVAL_ORDER: tuple[str, ...] = tuple(_BYBIT_INTERVAL.keys())


def _interval_ms(interval: str) -> int:
    unit = interval[-1]
    n = int(interval[:-1])
    if unit == "m":
        return n * 60_000
    if unit == "h":
        return n * 3_600_000
    if unit == "d":
        return n * 86_400_000
    if unit == "w":
        return n * 7 * 86_400_000
    if unit == "M":
        return n * 30 * 86_400_000
    raise ValidationError(f"interval inválido: {interval!r}")


def validate_kline_interval(interval: str) -> str:
    if not isinstance(interval, str) or not interval.strip():
        raise ValidationError("interval requerido")
    iv = interval.strip()
    if iv not in _BYBIT_INTERVAL:
        raise ValidationError(
            f"interval inválido: {interval!r}; "
            f"permitidos: {', '.join(_INTERVAL_ORDER)}"
        )
    return iv


class BybitPublicMdClient:
    """Cliente HTTP mínimo para MD público Bybit linear (stdlib only)."""

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
            raise ValidationError(f"bybit MD HTTP {exc.code}: {exc.reason}") from exc
        except urllib.error.URLError as exc:
            raise ValidationError(f"bybit MD red: {exc.reason}") from exc
        except TimeoutError as exc:
            raise ValidationError("bybit MD timeout") from exc
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValidationError("bybit MD JSON inválido") from exc

    def _parse_kline_rows(
        self,
        symbol: str,
        interval: str,
        payload: object,
    ) -> list[Bar]:
        if not isinstance(payload, dict):
            raise ValidationError("bybit kline inválido")
        if int(payload.get("retCode", -1)) != 0:
            raise ValidationError(
                f"bybit kline error: {payload.get('retMsg', 'unknown')}"
            )
        result = payload.get("result")
        if not isinstance(result, dict):
            raise ValidationError("bybit kline sin result")
        rows = result.get("list")
        if not isinstance(rows, list):
            raise ValidationError("bybit kline sin list")
        iv_ms = _interval_ms(interval)
        out: list[Bar] = []
        for row in rows:
            if not isinstance(row, list) or len(row) < 6:
                continue
            try:
                open_ms = int(row[0])
                o = Decimal(str(row[1]))
                h = Decimal(str(row[2]))
                lo = Decimal(str(row[3]))
                c = Decimal(str(row[4]))
                vol = Decimal(str(row[5]))
            except (TypeError, ValueError, InvalidOperation) as exc:
                raise ValidationError(f"bybit kline row inválida {symbol}") from exc
            close_ms = open_ms + iv_ms - 1
            t_open = datetime.fromtimestamp(open_ms / 1000.0, tz=UTC)
            t_close = datetime.fromtimestamp(close_ms / 1000.0, tz=UTC)
            out.append(
                Bar(
                    instrument_id=f"BYB:{symbol}",
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
        # Bybit devuelve newest-first → orden cronológico
        out.sort(key=lambda b: b.timestamp_open)
        return out

    def klines(
        self,
        symbol: str,
        *,
        interval: str = "1h",
        limit: int = 24,
    ) -> list[Bar]:
        """OHLCV linear → ``Bar`` (read-only).

        ``limit`` hasta ``MAX_KLINES_TOTAL`` (pagina de a 1000 hacia atrás con ``end``).
        """
        sym = symbol.strip().upper()
        if not sym:
            raise ValidationError("symbol vacío")
        if limit < MIN_KLINES or limit > MAX_KLINES_TOTAL:
            raise ValidationError(
                f"klines limit debe estar entre {MIN_KLINES} y {MAX_KLINES_TOTAL}"
            )
        iv = validate_kline_interval(interval)
        bybit_iv = _BYBIT_INTERVAL[iv]

        by_open: dict[datetime, Bar] = {}
        remaining = limit
        end_ms: int | None = None
        max_pages = (MAX_KLINES_TOTAL // MAX_KLINES_PER_REQUEST) + 2
        for _ in range(max_pages):
            if remaining <= 0:
                break
            batch = min(MAX_KLINES_PER_REQUEST, remaining)
            path = (
                f"/v5/market/kline?category=linear&symbol={sym}"
                f"&interval={bybit_iv}&limit={batch}"
            )
            if end_ms is not None:
                path += f"&end={end_ms}"
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
                break

        out = sorted(by_open.values(), key=lambda b: b.timestamp_open)
        if len(out) > limit:
            out = out[-limit:]
        if len(out) < MIN_KLINES:
            raise ValidationError(f"klines insuficientes para {sym}")
        return out

    def funding_rates(
        self,
        symbol: str,
        *,
        limit: int = 100,
    ) -> list[Decimal]:
        """Historial funding linear → lista de rates (Decimal)."""
        sym = symbol.strip().upper()
        if not sym:
            raise ValidationError("symbol vacío")
        lim = max(1, min(int(limit), 200))
        path = (
            f"/v5/market/funding/history?category=linear&symbol={sym}&limit={lim}"
        )
        payload = self._get_json(path)
        if not isinstance(payload, dict):
            raise ValidationError("bybit funding inválido")
        if int(payload.get("retCode", -1)) != 0:
            raise ValidationError(
                f"bybit funding error: {payload.get('retMsg', 'unknown')}"
            )
        result = payload.get("result")
        if not isinstance(result, dict):
            raise ValidationError("bybit funding sin result")
        rows = result.get("list")
        if not isinstance(rows, list):
            raise ValidationError("bybit funding sin list")
        out: list[Decimal] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            try:
                out.append(Decimal(str(row.get("fundingRate", "0"))))
            except (InvalidOperation, ValueError) as exc:
                raise ValidationError(f"bybit fundingRate inválido {sym}") from exc
        return out
