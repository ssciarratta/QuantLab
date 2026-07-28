"""Hyperliquid public market-data client (read-only, sin API keys)."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from quantlab.brokers.md_limits import MAX_KLINES_TOTAL, MIN_KLINES
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar

DEFAULT_BASE_URL = "https://api.hyperliquid.xyz"
DEFAULT_TIMEOUT_SECONDS = 10.0

_HL_INTERVAL: dict[str, str] = {
    "1m": "1m",
    "3m": "3m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "2h": "2h",
    "4h": "4h",
    "6h": "6h",
    "12h": "12h",
    "1d": "1d",
    "1w": "1w",
    "1M": "1M",
}

_INTERVAL_ORDER: tuple[str, ...] = tuple(_HL_INTERVAL.keys())


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
    if iv not in _HL_INTERVAL:
        raise ValidationError(
            f"interval inválido: {interval!r}; "
            f"permitidos: {', '.join(_INTERVAL_ORDER)}"
        )
    return iv


class HyperliquidPublicMdClient:
    """Cliente HTTP mínimo para MD público Hyperliquid (stdlib only)."""

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout_seconds

    def _post_json(self, body: dict[str, Any]) -> Any:
        url = f"{self._base}/info"
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "User-Agent": "QuantLab/1.00 (+read-only-md)",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise ValidationError(f"hyperliquid MD HTTP {exc.code}: {exc.reason}") from exc
        except urllib.error.URLError as exc:
            raise ValidationError(f"hyperliquid MD red: {exc.reason}") from exc
        except TimeoutError as exc:
            raise ValidationError("hyperliquid MD timeout") from exc
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValidationError("hyperliquid MD JSON inválido") from exc

    def _parse_candle_rows(
        self,
        coin: str,
        interval: str,
        payload: object,
    ) -> list[Bar]:
        if not isinstance(payload, list):
            raise ValidationError("hyperliquid candles inválido")
        out: list[Bar] = []
        for row in payload:
            if not isinstance(row, dict):
                continue
            try:
                open_ms = int(row["t"])
                close_ms = int(row.get("T", open_ms))
                o = Decimal(str(row["o"]))
                h = Decimal(str(row["h"]))
                lo = Decimal(str(row["l"]))
                c = Decimal(str(row["c"]))
                vol = Decimal(str(row.get("v", "0")))
            except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
                raise ValidationError(f"hyperliquid candle inválida {coin}") from exc
            t_open = datetime.fromtimestamp(open_ms / 1000.0, tz=UTC)
            t_close = datetime.fromtimestamp(close_ms / 1000.0, tz=UTC)
            if t_close < t_open:
                iv_ms = _interval_ms(interval)
                close_ms = open_ms + iv_ms - 1
                t_close = datetime.fromtimestamp(close_ms / 1000.0, tz=UTC)
            out.append(
                Bar(
                    instrument_id=f"HL:{coin}",
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
        out.sort(key=lambda b: b.timestamp_open)
        return out

    def klines(
        self,
        coin: str,
        *,
        interval: str = "1h",
        limit: int = 24,
    ) -> list[Bar]:
        """OHLCV vía ``candleSnapshot`` → ``Bar`` (read-only)."""
        c = coin.strip().upper()
        if not c:
            raise ValidationError("coin vacío")
        if limit < MIN_KLINES or limit > MAX_KLINES_TOTAL:
            raise ValidationError(
                f"klines limit debe estar entre {MIN_KLINES} y {MAX_KLINES_TOTAL}"
            )
        iv = validate_kline_interval(interval)
        hl_iv = _HL_INTERVAL[iv]
        iv_ms = _interval_ms(iv)
        end_ms = int(time.time() * 1000)
        start_ms = end_ms - limit * iv_ms
        body = {
            "type": "candleSnapshot",
            "req": {
                "coin": c,
                "interval": hl_iv,
                "startTime": start_ms,
                "endTime": end_ms,
            },
        }
        payload = self._post_json(body)
        bars = self._parse_candle_rows(c, iv, payload)
        if len(bars) > limit:
            bars = bars[-limit:]
        if len(bars) < MIN_KLINES:
            raise ValidationError(f"klines insuficientes para {c}")
        return bars

    def funding_rates(
        self,
        coin: str,
        *,
        limit: int = 100,
    ) -> list[Decimal]:
        """Historial funding vía ``fundingHistory`` → lista de rates (Decimal)."""
        c = coin.strip().upper()
        if not c:
            raise ValidationError("coin vacío")
        lim = max(1, min(int(limit), 500))
        # funding cada ~1h; ventana generosa hacia atrás
        end_ms = int(time.time() * 1000)
        start_ms = end_ms - lim * 3_600_000
        body = {
            "type": "fundingHistory",
            "coin": c,
            "startTime": start_ms,
            "endTime": end_ms,
        }
        payload = self._post_json(body)
        if not isinstance(payload, list):
            raise ValidationError("hyperliquid funding inválido")
        out: list[Decimal] = []
        for row in payload:
            if not isinstance(row, dict):
                continue
            try:
                out.append(Decimal(str(row.get("fundingRate", "0"))))
            except (InvalidOperation, ValueError) as exc:
                raise ValidationError(f"hyperliquid fundingRate inválido {c}") from exc
        if len(out) > lim:
            out = out[-lim:]
        return out
