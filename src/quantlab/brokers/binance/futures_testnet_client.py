"""Cliente Binance **Futures USD-M Testnet** firmado — opt-in estricto.

Solo se usa si:
1. Unlock LIVE activo (scope binance_demo)
2. ``QUANTLAB_DEMO_USE_FUTURES_TESTNET=1``
3. ``BINANCE_FUTURES_DEMO_API_KEY`` + ``BINANCE_FUTURES_DEMO_API_SECRET``

Host permitido: ``testnet.binancefuture.com`` (fapi).
Nunca ``fapi.binance.com`` / producción. Keys Spot ≠ Futures.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from quantlab.brokers.binance.testnet_client import (
    TestnetAuthResult,
    TestnetBalance,
    TestnetConnectivityResult,
    TestnetOrderResult,
)
from quantlab.core.exceptions import ValidationError

FUTURES_TESTNET_BASE_URL = "https://testnet.binancefuture.com"
_ENV_KEY = "BINANCE_FUTURES_DEMO_API_KEY"
_ENV_SECRET = "BINANCE_FUTURES_DEMO_API_SECRET"
_ENV_USE = "QUANTLAB_DEMO_USE_FUTURES_TESTNET"
_PROD_HOST_MARKERS = (
    "fapi.binance.com",
    "dapi.binance.com",
    "papi.binance.com",
    "api.binance.com",
    "api.binance.us",
)
_DEFAULT_RECV_WINDOW_MS = 5000
_MAX_RECV_WINDOW_MS = 60000
_BINANCE_ERROR_CODE_RE = re.compile(r'"code"\s*:\s*(-?\d+)')


def futures_testnet_keys_configured() -> bool:
    return bool(os.environ.get(_ENV_KEY, "").strip()) and bool(
        os.environ.get(_ENV_SECRET, "").strip()
    )


def futures_testnet_remote_enabled() -> bool:
    """Doble gate: flag explícito + keys Futures presentes."""
    flag = os.environ.get(_ENV_USE, "").strip().lower()
    if flag not in {"1", "true", "yes", "on"}:
        return False
    return futures_testnet_keys_configured()


def futures_testnet_status() -> dict[str, Any]:
    return {
        "market": "futures_usdm",
        "keys_configured": futures_testnet_keys_configured(),
        "use_testnet_flag": os.environ.get(_ENV_USE, "").strip() or None,
        "remote_enabled": futures_testnet_remote_enabled(),
        "base_url": FUTURES_TESTNET_BASE_URL,
        "env_key": _ENV_KEY,
        "env_secret": _ENV_SECRET,
        "env_use_flag": _ENV_USE,
        "note": (
            "Futures Testnet es independiente del Spot. "
            "Keys de testnet.binancefuture.com no sirven en testnet.binance.vision."
        ),
    }


def _parse_binance_error_code(message: str) -> int | None:
    match = _BINANCE_ERROR_CODE_RE.search(message)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _validate_futures_testnet_base(base_url: str) -> str:
    base = base_url.rstrip("/")
    lower = base.lower()
    for marker in _PROD_HOST_MARKERS:
        if marker in lower:
            raise ValidationError(
                "BinanceFuturesTestnetClient rechaza hosts de producción"
            )
    if "testnet" not in lower or "binancefuture" not in lower:
        raise ValidationError(
            "base_url debe ser Futures Testnet (testnet.binancefuture.com)"
        )
    return base


def public_futures_connectivity_check(
    base_url: str = FUTURES_TESTNET_BASE_URL,
    *,
    timeout_seconds: float = 15.0,
) -> TestnetConnectivityResult:
    """Probe público sin credenciales (ping + time fapi)."""
    base = _validate_futures_testnet_base(base_url)
    client = BinanceFuturesTestnetClient(
        api_key="__public_probe__",
        api_secret="__public_probe__",
        base_url=base,
        timeout_seconds=timeout_seconds,
    )
    return client.connectivity_check()


@dataclass(frozen=True, slots=True)
class FuturesAssetBalance:
    asset: str
    wallet_balance: str
    available_balance: str
    unrealized_profit: str

    def as_testnet_balance(self) -> TestnetBalance:
        """Vista compat para assess_strategy_funds (available → free)."""
        try:
            wallet = Decimal(self.wallet_balance)
            available = Decimal(self.available_balance)
            locked = wallet - available
            if locked < 0:
                locked = Decimal("0")
        except InvalidOperation:
            return TestnetBalance(
                asset=self.asset, free=self.available_balance, locked="0"
            )
        return TestnetBalance(
            asset=self.asset,
            free=format(available, "f"),
            locked=format(locked, "f"),
        )


class BinanceFuturesTestnetClient:
    """HTTP firmado mínimo hacia Futures USD-M Testnet (stdlib, fapi)."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_secret: str | None = None,
        base_url: str = FUTURES_TESTNET_BASE_URL,
        timeout_seconds: float = 15.0,
        recv_window_ms: int = _DEFAULT_RECV_WINDOW_MS,
    ) -> None:
        key = (api_key if api_key is not None else os.environ.get(_ENV_KEY, "")).strip()
        secret = (
            api_secret if api_secret is not None else os.environ.get(_ENV_SECRET, "")
        ).strip()
        if not key or not secret:
            raise ValidationError(
                f"Futures Testnet requiere {_ENV_KEY} y {_ENV_SECRET} en env local"
            )
        if recv_window_ms < 1 or recv_window_ms > _MAX_RECV_WINDOW_MS:
            raise ValidationError(
                f"recv_window_ms debe estar entre 1 y {_MAX_RECV_WINDOW_MS}"
            )
        self._key = key
        self._secret = secret.encode("utf-8")
        self._base = _validate_futures_testnet_base(base_url)
        self._timeout = timeout_seconds
        self._recv_window_ms = recv_window_ms
        self._time_offset_ms = 0

    @property
    def base_url(self) -> str:
        return self._base

    def _sign(self, params: dict[str, str]) -> str:
        query = urllib.parse.urlencode(params)
        return hmac.new(self._secret, query.encode("utf-8"), hashlib.sha256).hexdigest()

    def _signed_timestamp_ms(self) -> int:
        return int(time.time() * 1000) + self._time_offset_ms

    def _sync_time_offset(self) -> None:
        data = self._request("GET", "/fapi/v1/time", {}, signed=False, _retry=False)
        server_time = data.get("serverTime")
        if not isinstance(server_time, int):
            raise ValidationError("binance futures testnet serverTime inválido")
        local_ms = int(time.time() * 1000)
        self._time_offset_ms = server_time - local_ms

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, str],
        *,
        signed: bool,
        _retry: bool = True,
    ) -> dict[str, Any]:
        payload = dict(params)
        headers = {
            "User-Agent": "QuantLab/1.01 (+binance-futures-testnet)",
            "X-MBX-APIKEY": self._key,
        }
        if signed:
            payload["timestamp"] = str(self._signed_timestamp_ms())
            payload["recvWindow"] = str(self._recv_window_ms)
            payload["signature"] = self._sign(payload)
        query = urllib.parse.urlencode(payload)
        url = f"{self._base}{path}?{query}"
        req = urllib.request.Request(url, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:300]
            message = f"binance futures testnet HTTP {exc.code}: {body}"
            code = _parse_binance_error_code(body)
            if signed and _retry and code == -1021:
                self._sync_time_offset()
                return self._request(
                    method, path, params, signed=signed, _retry=False
                )
            raise ValidationError(message) from exc
        except urllib.error.URLError as exc:
            raise ValidationError(f"binance futures testnet red: {exc.reason}") from exc
        except TimeoutError as exc:
            raise ValidationError("binance futures testnet timeout") from exc
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValidationError("binance futures testnet JSON inválido") from exc
        if not isinstance(data, dict):
            raise ValidationError("binance futures testnet respuesta no-objeto")
        return data

    def server_time(self) -> int:
        data = self._request("GET", "/fapi/v1/time", {}, signed=False)
        server_time = data.get("serverTime")
        if not isinstance(server_time, int):
            raise ValidationError("binance futures testnet serverTime inválido")
        return server_time

    def ping(self) -> bool:
        data = self._request("GET", "/fapi/v1/ping", {}, signed=False)
        return data == {}

    def connectivity_check(self) -> TestnetConnectivityResult:
        ping_ok = False
        server_time_ms: int | None = None
        error: str | None = None
        try:
            ping_ok = self.ping()
        except ValidationError as exc:
            error = str(exc)
        try:
            server_time_ms = self.server_time()
        except ValidationError as exc:
            if error is None:
                error = str(exc)
        return TestnetConnectivityResult(
            ok=ping_ok and server_time_ms is not None,
            ping_ok=ping_ok,
            server_time_ms=server_time_ms,
            base_url=self._base,
            error=error,
        )

    def get_account(self) -> dict[str, Any]:
        """GET /fapi/v2/account (firmado, USER_DATA)."""
        return self._request("GET", "/fapi/v2/account", {}, signed=True)

    def get_balances(self, *, omit_zero: bool = True) -> list[FuturesAssetBalance]:
        data = self.get_account()
        raw_assets = data.get("assets")
        if not isinstance(raw_assets, list):
            raise ValidationError("binance futures testnet assets inválidos")
        out: list[FuturesAssetBalance] = []
        for row in raw_assets:
            if not isinstance(row, dict):
                continue
            asset = str(row.get("asset") or "").strip().upper()
            if not asset:
                continue
            wallet = str(row.get("walletBalance") or "0")
            available = str(row.get("availableBalance") or "0")
            upnl = str(row.get("unrealizedProfit") or "0")
            try:
                total = abs(Decimal(wallet)) + abs(Decimal(available))
            except InvalidOperation:
                total = Decimal("0")
            if omit_zero and total == 0:
                continue
            out.append(
                FuturesAssetBalance(
                    asset=asset,
                    wallet_balance=wallet,
                    available_balance=available,
                    unrealized_profit=upnl,
                )
            )
        return out

    def auth_check(self) -> TestnetAuthResult:
        try:
            data = self.get_account()
        except ValidationError as exc:
            return TestnetAuthResult(
                ok=False,
                can_trade=False,
                permissions=(),
                uid=None,
                account_type="FUTURES_USDM",
                error=str(exc),
            )
        return TestnetAuthResult(
            ok=True,
            can_trade=bool(data.get("canTrade")),
            permissions=("FUTURES",),
            uid=None,
            account_type="FUTURES_USDM",
            error=None,
        )

    def place_market_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: str,
        client_order_id: str,
    ) -> TestnetOrderResult:
        sym = symbol.strip().upper()
        side_u = side.strip().upper()
        if side_u not in {"BUY", "SELL"}:
            raise ValidationError("side futures testnet inválido")
        params = {
            "symbol": sym,
            "side": side_u,
            "type": "MARKET",
            "quantity": quantity,
            "newClientOrderId": client_order_id,
        }
        data = self._request("POST", "/fapi/v1/order", params, signed=True)
        order_id = str(data.get("orderId") or data.get("order_id") or "")
        if not order_id:
            raise ValidationError("futures testnet sin orderId en respuesta")
        status = str(data.get("status") or "UNKNOWN")
        return TestnetOrderResult(
            order_id=f"BN-FUT-TN-{order_id}",
            client_order_id=str(data.get("clientOrderId") or client_order_id),
            status=status,
            symbol=sym,
            side=side_u,
            raw={k: data[k] for k in data if k.lower() not in {"fills"}},
        )

    def place_limit_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: str,
        price: str,
        client_order_id: str,
        time_in_force: str = "GTC",
    ) -> TestnetOrderResult:
        sym = symbol.strip().upper()
        side_u = side.strip().upper()
        if side_u not in {"BUY", "SELL"}:
            raise ValidationError("side futures testnet inválido")
        params = {
            "symbol": sym,
            "side": side_u,
            "type": "LIMIT",
            "timeInForce": time_in_force,
            "quantity": quantity,
            "price": price,
            "newClientOrderId": client_order_id,
        }
        data = self._request("POST", "/fapi/v1/order", params, signed=True)
        order_id = str(data.get("orderId") or data.get("order_id") or "")
        if not order_id:
            raise ValidationError("futures testnet sin orderId en respuesta LIMIT")
        status = str(data.get("status") or "UNKNOWN")
        return TestnetOrderResult(
            order_id=f"BN-FUT-TN-{order_id}",
            client_order_id=str(data.get("clientOrderId") or client_order_id),
            status=status,
            symbol=sym,
            side=side_u,
            raw={k: data[k] for k in data if k.lower() not in {"fills"}},
        )

    def cancel_order(self, *, symbol: str, order_id: str) -> dict[str, Any]:
        sym = symbol.strip().upper()
        oid = order_id.strip()
        if not sym or not oid:
            raise ValidationError(
                "symbol y order_id requeridos para cancel futures testnet"
            )
        params = {"symbol": sym, "orderId": oid}
        data = self._request("DELETE", "/fapi/v1/order", params, signed=True)
        if not isinstance(data, dict):
            raise ValidationError("futures testnet cancel respuesta inválida")
        return data
