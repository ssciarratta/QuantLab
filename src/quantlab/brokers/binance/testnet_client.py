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
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from quantlab.core.exceptions import ValidationError

TESTNET_BASE_URL = "https://testnet.binance.vision"
_ENV_KEY = "BINANCE_DEMO_API_KEY"
_ENV_SECRET = "BINANCE_DEMO_API_SECRET"
_ENV_USE = "QUANTLAB_DEMO_USE_TESTNET"
_PROD_HOST_MARKERS = ("api.binance.com", "api.binance.us")


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


class BinanceTestnetClient:
    """HTTP firmado mínimo hacia Spot Testnet (stdlib)."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_secret: str | None = None,
        base_url: str = TESTNET_BASE_URL,
        timeout_seconds: float = 15.0,
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
        self._key = key
        self._secret = secret.encode("utf-8")
        self._base = base
        self._timeout = timeout_seconds

    def _sign(self, params: dict[str, str]) -> str:
        query = urllib.parse.urlencode(params)
        return hmac.new(self._secret, query.encode("utf-8"), hashlib.sha256).hexdigest()

    def _request(
        self, method: str, path: str, params: dict[str, str], *, signed: bool
    ) -> dict[str, Any]:
        payload = dict(params)
        headers = {"User-Agent": "QuantLab/0.95 (+binance-testnet)", "X-MBX-APIKEY": self._key}
        if signed:
            payload["timestamp"] = str(int(time.time() * 1000))
            payload["signature"] = self._sign(payload)
        query = urllib.parse.urlencode(payload)
        url = f"{self._base}{path}?{query}"
        req = urllib.request.Request(url, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:300]
            raise ValidationError(
                f"binance testnet HTTP {exc.code}: {body}"
            ) from exc
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

    def ping(self) -> bool:
        data = self._request("GET", "/api/v3/ping", {}, signed=False)
        return data == {}

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
