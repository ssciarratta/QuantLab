"""Binance public market-data client (read-only, sin API keys) — F100.

Usa endpoints públicos de Binance Spot. No envía órdenes. Fail-closed ante error.
Para demo/testnet de trading se usará otro módulo + unlock LIVE.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from quantlab.core.exceptions import ValidationError

DEFAULT_BASE_URL = "https://api.binance.com"
DEFAULT_TIMEOUT_SECONDS = 10.0


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
            headers={"User-Agent": "QuantLab/0.94 (+read-only-md)"},
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
