"""Cliente Binance Spot **Testnet** firmado (F102) — opt-in estricto.

Solo se usa si:
1. Unlock LIVE activo (scope binance_demo)
2. ``QUANTLAB_DEMO_USE_TESTNET=1``
3. ``BINANCE_DEMO_API_KEY`` + ``BINANCE_DEMO_API_SECRET`` en env local

Nunca apunta a ``api.binance.com``. Secrets nunca se loguean ni van a git.
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

from quantlab.core.exceptions import ValidationError

TESTNET_BASE_URL = "https://testnet.binance.vision"
_ENV_KEY = "BINANCE_DEMO_API_KEY"
_ENV_SECRET = "BINANCE_DEMO_API_SECRET"
_ENV_USE = "QUANTLAB_DEMO_USE_TESTNET"
_PROD_HOST_MARKERS = (
    "api.binance.com",
    "api.binance.us",
    "api1.binance.com",
    "api2.binance.com",
    "api3.binance.com",
)
_DEFAULT_RECV_WINDOW_MS = 5000
_MAX_RECV_WINDOW_MS = 60000
_BINANCE_ERROR_CODE_RE = re.compile(r'"code"\s*:\s*(-?\d+)')


def testnet_keys_configured() -> bool:
    return bool(os.environ.get(_ENV_KEY, "").strip()) and bool(
        os.environ.get(_ENV_SECRET, "").strip()
    )


def testnet_remote_enabled() -> bool:
    """Doble gate: flag explícito + keys presentes."""
    flag = os.environ.get(_ENV_USE, "").strip().lower()
    if flag not in {"1", "true", "yes", "on"}:
        return False
    return testnet_keys_configured()


def testnet_status() -> dict[str, Any]:
    return {
        "keys_configured": testnet_keys_configured(),
        "use_testnet_flag": os.environ.get(_ENV_USE, "").strip() or None,
        "remote_enabled": testnet_remote_enabled(),
        "base_url": TESTNET_BASE_URL,
        "env_key": _ENV_KEY,
        "env_secret": _ENV_SECRET,
        "env_use_flag": _ENV_USE,
        "note": (
            "Sin QUANTLAB_DEMO_USE_TESTNET=1 + keys locales, el demo usa "
            "simulador local (F101)."
        ),
    }


@dataclass(frozen=True, slots=True)
class TestnetOrderResult:
    order_id: str
    client_order_id: str
    status: str
    symbol: str
    side: str
    raw: dict[str, Any]


@dataclass(frozen=True, slots=True)
class TestnetBalance:
    asset: str
    free: str
    locked: str

    @property
    def total(self) -> str:
        try:
            value = Decimal(self.free) + Decimal(self.locked)
        except InvalidOperation:
            return "0"
        return format(value, "f")


@dataclass(frozen=True, slots=True)
class TestnetConnectivityResult:
    ok: bool
    ping_ok: bool
    server_time_ms: int | None
    base_url: str
    error: str | None = None


@dataclass(frozen=True, slots=True)
class TestnetAuthResult:
    ok: bool
    can_trade: bool
    permissions: tuple[str, ...]
    uid: int | None
    account_type: str | None
    error: str | None = None


def _parse_binance_error_code(message: str) -> int | None:
    match = _BINANCE_ERROR_CODE_RE.search(message)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def public_connectivity_check(
    base_url: str = TESTNET_BASE_URL,
    *,
    timeout_seconds: float = 15.0,
) -> TestnetConnectivityResult:
    """Probe público sin credenciales (ping + time)."""
    base = base_url.rstrip("/")
    lower = base.lower()
    for marker in _PROD_HOST_MARKERS:
        if marker in lower:
            raise ValidationError("public_connectivity_check rechaza hosts de producción")
    if "testnet" not in lower and "binance.vision" not in lower:
        raise ValidationError("base_url debe ser Spot Testnet")
    client = BinanceTestnetClient(
        api_key="__public_probe__",
        api_secret="__public_probe__",
        base_url=base,
        timeout_seconds=timeout_seconds,
    )
    return client.connectivity_check()


def _balance_from_raw(row: dict[str, Any]) -> TestnetBalance:
    asset = str(row.get("asset") or "").strip().upper()
    if not asset:
        raise ValidationError("balance sin asset")
    return TestnetBalance(
        asset=asset,
        free=str(row.get("free") or "0"),
        locked=str(row.get("locked") or "0"),
    )


class BinanceTestnetClient:
    """HTTP firmado mínimo hacia Spot Testnet (stdlib)."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_secret: str | None = None,
        base_url: str = TESTNET_BASE_URL,
        timeout_seconds: float = 15.0,
        recv_window_ms: int = _DEFAULT_RECV_WINDOW_MS,
    ) -> None:
        key = (api_key if api_key is not None else os.environ.get(_ENV_KEY, "")).strip()
        secret = (
            api_secret if api_secret is not None else os.environ.get(_ENV_SECRET, "")
        ).strip()
        if not key or not secret:
            raise ValidationError(
                f"Testnet requiere {_ENV_KEY} y {_ENV_SECRET} en env local"
            )
        base = base_url.rstrip("/")
        lower = base.lower()
        for marker in _PROD_HOST_MARKERS:
            if marker in lower:
                raise ValidationError(
                    "BinanceTestnetClient rechaza hosts de producción"
                )
        if "testnet" not in lower and "binance.vision" not in lower:
            raise ValidationError(
                "base_url debe ser Spot Testnet (testnet.binance.vision)"
            )
        if recv_window_ms < 1 or recv_window_ms > _MAX_RECV_WINDOW_MS:
            raise ValidationError(
                f"recv_window_ms debe estar entre 1 y {_MAX_RECV_WINDOW_MS}"
            )
        self._key = key
        self._secret = secret.encode("utf-8")
        self._base = base
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
        data = self._request("GET", "/api/v3/time", {}, signed=False, _retry=False)
        server_time = data.get("serverTime")
        if not isinstance(server_time, int):
            raise ValidationError("binance testnet serverTime inválido")
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
            "User-Agent": "QuantLab/1.01 (+binance-testnet)",
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
            message = f"binance testnet HTTP {exc.code}: {body}"
            code = _parse_binance_error_code(body)
            if signed and _retry and code == -1021:
                self._sync_time_offset()
                return self._request(
                    method, path, params, signed=signed, _retry=False
                )
            raise ValidationError(message) from exc
        except urllib.error.URLError as exc:
            raise ValidationError(f"binance testnet red: {exc.reason}") from exc
        except TimeoutError as exc:
            raise ValidationError("binance testnet timeout") from exc
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValidationError("binance testnet JSON inválido") from exc
        if not isinstance(data, dict):
            raise ValidationError("binance testnet respuesta no-objeto")
        return data

    def server_time(self) -> int:
        """GET /api/v3/time → serverTime (unix ms)."""
        data = self._request("GET", "/api/v3/time", {}, signed=False)
        server_time = data.get("serverTime")
        if not isinstance(server_time, int):
            raise ValidationError("binance testnet serverTime inválido")
        return server_time

    def ping(self) -> bool:
        data = self._request("GET", "/api/v3/ping", {}, signed=False)
        return data == {}

    def connectivity_check(self) -> TestnetConnectivityResult:
        """Probe público: ping + server time (sin validar secret)."""
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
        ok = ping_ok and server_time_ms is not None
        return TestnetConnectivityResult(
            ok=ok,
            ping_ok=ping_ok,
            server_time_ms=server_time_ms,
            base_url=self._base,
            error=error,
        )

    def get_account(self, *, omit_zero_balances: bool = False) -> dict[str, Any]:
        """GET /api/v3/account (firmado, USER_DATA)."""
        params: dict[str, str] = {}
        if omit_zero_balances:
            params["omitZeroBalances"] = "true"
        return self._request("GET", "/api/v3/account", params, signed=True)

    def get_balances(
        self,
        *,
        omit_zero: bool = True,
        assets: frozenset[str] | None = None,
    ) -> list[TestnetBalance]:
        """Balances parseados desde GET /api/v3/account."""
        data = self.get_account(omit_zero_balances=omit_zero)
        raw_balances = data.get("balances")
        if not isinstance(raw_balances, list):
            raise ValidationError("binance testnet balances inválidos")
        balances: list[TestnetBalance] = []
        for row in raw_balances:
            if not isinstance(row, dict):
                continue
            balance = _balance_from_raw(row)
            if assets is not None and balance.asset not in assets:
                continue
            balances.append(balance)
        return balances

    def auth_check(self) -> TestnetAuthResult:
        """Valida credenciales/permisos vía GET /api/v3/account (sin órdenes)."""
        try:
            data = self.get_account(omit_zero_balances=True)
        except ValidationError as exc:
            return TestnetAuthResult(
                ok=False,
                can_trade=False,
                permissions=(),
                uid=None,
                account_type=None,
                error=str(exc),
            )
        permissions_raw = data.get("permissions")
        permissions: tuple[str, ...]
        if isinstance(permissions_raw, list):
            permissions = tuple(str(p) for p in permissions_raw)
        else:
            permissions = ()
        uid_raw = data.get("uid")
        uid = int(uid_raw) if isinstance(uid_raw, int) else None
        account_type = (
            str(data.get("accountType")) if data.get("accountType") is not None else None
        )
        return TestnetAuthResult(
            ok=True,
            can_trade=bool(data.get("canTrade")),
            permissions=permissions,
            uid=uid,
            account_type=account_type,
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
            raise ValidationError("side testnet inválido")
        params = {
            "symbol": sym,
            "side": side_u,
            "type": "MARKET",
            "quantity": quantity,
            "newClientOrderId": client_order_id,
        }
        data = self._request("POST", "/api/v3/order", params, signed=True)
        order_id = str(data.get("orderId") or data.get("order_id") or "")
        if not order_id:
            raise ValidationError("testnet sin orderId en respuesta")
        status = str(data.get("status") or "UNKNOWN")
        return TestnetOrderResult(
            order_id=f"BN-TN-{order_id}",
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
            raise ValidationError("side testnet inválido")
        params = {
            "symbol": sym,
            "side": side_u,
            "type": "LIMIT",
            "timeInForce": time_in_force,
            "quantity": quantity,
            "price": price,
            "newClientOrderId": client_order_id,
        }
        data = self._request("POST", "/api/v3/order", params, signed=True)
        order_id = str(data.get("orderId") or data.get("order_id") or "")
        if not order_id:
            raise ValidationError("testnet sin orderId en respuesta LIMIT")
        status = str(data.get("status") or "UNKNOWN")
        return TestnetOrderResult(
            order_id=f"BN-TN-{order_id}",
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
            raise ValidationError("symbol y order_id requeridos para cancel testnet")
        params = {"symbol": sym, "orderId": oid}
        data = self._request("DELETE", "/api/v3/order", params, signed=True)
        if not isinstance(data, dict):
            raise ValidationError("testnet cancel respuesta inválida")
        return data
