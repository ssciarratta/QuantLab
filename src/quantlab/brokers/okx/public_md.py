"""OKX public market-data client (read-only, sin API keys)."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from quantlab.brokers.md_limits import MAX_KLINES_TOTAL, MIN_KLINES
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar

DEFAULT_BASE_URL = "https://www.okx.com"
DEFAULT_TIMEOUT_SECONDS = 10.0

MAX_KLINES_PER_REQUEST = 300

_OKX_BAR: dict[str, str] = {
    "1m": "1m",
    "3m": "3m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1H",
    "2h": "2H",
    "4h": "4H",
    "6h": "6H",
    "12h": "12H",
    "1d": "1D",
    "1w": "1W",
    "1M": "1M",
}

_INTERVAL_ORDER: tuple[str, ...] = tuple(_OKX_BAR.keys())


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
    if iv not in _OKX_BAR:
        raise ValidationError(
            f"interval inválido: {interval!r}; "
            f"permitidos: {', '.join(_INTERVAL_ORDER)}"
        )
    return iv


class OkxPublicMdClient:
    """Cliente HTTP mínimo para MD público OKX (stdlib only)."""

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
            raise ValidationError(f"okx MD HTTP {exc.code}: {exc.reason}") from exc
        except urllib.error.URLError as exc:
            raise ValidationError(f"okx MD red: {exc.reason}") from exc
        except TimeoutError as exc:
            raise ValidationError("okx MD timeout") from exc
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValidationError("okx MD JSON inválido") from exc

    def _parse_candle_rows(
        self,
        inst_id: str,
        interval: str,
        payload: object,
    ) -> list[Bar]:
        if not isinstance(payload, dict):
            raise ValidationError("okx candles inválido")
        code = str(payload.get("code", ""))
        if code != "0":
            raise ValidationError(f"okx candles error code={code}")
        data = payload.get("data")
        if not isinstance(data, list):
            raise ValidationError("okx candles sin data")
        iv_ms = _interval_ms(interval)
        out: list[Bar] = []
        for row in data:
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
                raise ValidationError(f"okx candle row inválida {inst_id}") from exc
            close_ms = open_ms + iv_ms - 1
            t_open = datetime.fromtimestamp(open_ms / 1000.0, tz=UTC)
            t_close = datetime.fromtimestamp(close_ms / 1000.0, tz=UTC)
            out.append(
                Bar(
                    instrument_id=f"OKX:{inst_id}",
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
        inst_id: str,
        *,
        interval: str = "1h",
        limit: int = 24,
    ) -> list[Bar]:
        """OHLCV público → ``Bar`` (read-only). Pagina con ``after`` si limit > 300."""
        iid = inst_id.strip()
        if not iid:
            raise ValidationError("instId vacío")
        if limit < MIN_KLINES or limit > MAX_KLINES_TOTAL:
            raise ValidationError(
                f"klines limit debe estar entre {MIN_KLINES} y {MAX_KLINES_TOTAL}"
            )
        iv = validate_kline_interval(interval)
        bar = _OKX_BAR[iv]

        by_open: dict[datetime, Bar] = {}
        remaining = limit
        after_ms: str | None = None
        max_pages = (MAX_KLINES_TOTAL // MAX_KLINES_PER_REQUEST) + 2
        for _ in range(max_pages):
            if remaining <= 0:
                break
            batch = min(MAX_KLINES_PER_REQUEST, remaining)
            path = (
                f"/api/v5/market/candles?instId={urllib.parse.quote(iid)}"
                f"&bar={bar}&limit={batch}"
            )
            if after_ms is not None:
                path += f"&after={after_ms}"
            payload = self._get_json(path)
            chunk = self._parse_candle_rows(iid, iv, payload)
            if not chunk:
                break
            for bar_obj in chunk:
                by_open[bar_obj.timestamp_open] = bar_obj
            oldest = min(chunk, key=lambda b: b.timestamp_open)
            after_ms = str(int(oldest.timestamp_open.timestamp() * 1000))
            remaining = limit - len(by_open)
            if len(chunk) < batch:
                break

        out = sorted(by_open.values(), key=lambda b: b.timestamp_open)
        if len(out) > limit:
            out = out[-limit:]
        if len(out) < MIN_KLINES:
            raise ValidationError(f"klines insuficientes para {iid}")
        return out

    def funding_rates(
        self,
        inst_id: str,
        *,
        limit: int = 100,
    ) -> list[Decimal]:
        """Historial funding → lista de rates (Decimal)."""
        iid = inst_id.strip()
        if not iid:
            raise ValidationError("instId vacío")
        lim = max(1, min(int(limit), 100))
        path = (
            f"/api/v5/public/funding-rate-history?instId={urllib.parse.quote(iid)}"
            f"&limit={lim}"
        )
        payload = self._get_json(path)
        if not isinstance(payload, dict):
            raise ValidationError("okx funding inválido")
        code = str(payload.get("code", ""))
        if code != "0":
            raise ValidationError(f"okx funding error code={code}")
        data = payload.get("data")
        if not isinstance(data, list):
            raise ValidationError("okx funding sin data")
        out: list[Decimal] = []
        for row in data:
            if not isinstance(row, dict):
                continue
            try:
                out.append(Decimal(str(row.get("fundingRate", "0"))))
            except (InvalidOperation, ValueError) as exc:
                raise ValidationError(f"okx fundingRate inválido {iid}") from exc
        return out
