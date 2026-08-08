"""Tests cuenta/balances/auth Binance Spot Testnet."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch

import pytest

from quantlab.brokers.binance.testnet_client import (
    BinanceTestnetClient,
    TestnetBalance as TNBalance,
    public_connectivity_check,
)
from quantlab.brokers.binance.testnet_diagnostic import (
    assess_strategy_funds,
    format_diagnostic_report,
    run_testnet_diagnostic,
)
from quantlab.core.exceptions import ValidationError


@pytest.fixture
def client() -> BinanceTestnetClient:
    return BinanceTestnetClient(api_key="k", api_secret="s")


def test_rejects_production_hosts() -> None:
    for host in (
        "https://api.binance.com",
        "https://api.binance.us",
    ):
        with pytest.raises(ValidationError, match="producción"):
            BinanceTestnetClient(api_key="k", api_secret="s", base_url=host)
    with pytest.raises(ValidationError, match="producción"):
        BinanceTestnetClient(api_key="k", api_secret="s", base_url="https://api1.binance.com")


def test_rejects_non_testnet_host() -> None:
    with pytest.raises(ValidationError, match="Spot Testnet"):
        BinanceTestnetClient(api_key="k", api_secret="s", base_url="https://example.com")


def test_recv_window_bounds() -> None:
    with pytest.raises(ValidationError, match="recv_window_ms"):
        BinanceTestnetClient(api_key="k", api_secret="s", recv_window_ms=0)
    with pytest.raises(ValidationError, match="recv_window_ms"):
        BinanceTestnetClient(api_key="k", api_secret="s", recv_window_ms=70000)


def test_missing_credentials() -> None:
    with pytest.raises(ValidationError, match="BINANCE_DEMO_API_KEY"):
        BinanceTestnetClient(api_key="", api_secret="")


def test_server_time(client: BinanceTestnetClient) -> None:
    with patch.object(client, "_request", return_value={"serverTime": 1_700_000_000_000}):
        assert client.server_time() == 1_700_000_000_000


def test_connectivity_check_ok(client: BinanceTestnetClient) -> None:
    def fake_request(
        _self: BinanceTestnetClient,
        method: str,
        path: str,
        _params: dict[str, str],
        *,
        signed: bool,
        _retry: bool = True,
    ) -> dict[str, object]:
        assert signed is False
        if path == "/api/v3/ping":
            return {}
        if path == "/api/v3/time":
            return {"serverTime": 123}
        raise AssertionError(path)

    with patch.object(BinanceTestnetClient, "_request", fake_request):
        result = client.connectivity_check()
    assert result.ok is True
    assert result.ping_ok is True
    assert result.server_time_ms == 123


def test_public_connectivity_check_rejects_production() -> None:
    with pytest.raises(ValidationError, match="producción"):
        public_connectivity_check("https://api.binance.com")


def test_get_account_signed(client: BinanceTestnetClient) -> None:
    captured: dict[str, str] = {}

    def fake_request(
        self: BinanceTestnetClient,
        method: str,
        path: str,
        params: dict[str, str],
        *,
        signed: bool,
        _retry: bool = True,
    ) -> dict[str, object]:
        assert method == "GET"
        assert path == "/api/v3/account"
        assert signed is True
        payload = dict(params)
        if signed:
            payload["timestamp"] = str(self._signed_timestamp_ms())
            payload["recvWindow"] = str(self._recv_window_ms)
            payload["signature"] = self._sign(payload)
        captured.update(payload)
        return {
            "canTrade": True,
            "accountType": "SPOT",
            "uid": 42,
            "permissions": ["SPOT"],
            "balances": [
                {"asset": "USDT", "free": "1000.0", "locked": "0"},
                {"asset": "BTC", "free": "0.5", "locked": "0"},
            ],
        }

    with patch.object(BinanceTestnetClient, "_request", fake_request):
        data = client.get_account(omit_zero_balances=True)
    assert data["canTrade"] is True
    assert captured.get("omitZeroBalances") == "true"
    assert "timestamp" in captured
    assert "recvWindow" in captured
    assert "signature" in captured


def test_get_balances_filter(client: BinanceTestnetClient) -> None:
    with patch.object(
        BinanceTestnetClient,
        "get_account",
        return_value={
            "balances": [
                {"asset": "USDT", "free": "100", "locked": "0"},
                {"asset": "BTC", "free": "0.01", "locked": "0"},
                {"asset": "ETH", "free": "0", "locked": "0"},
            ]
        },
    ):
        all_bal = client.get_balances(omit_zero=False)
        assert len(all_bal) == 3
        filtered = client.get_balances(assets=frozenset({"USDT"}))
        assert filtered == [
            TNBalance(asset="USDT", free="100", locked="0"),
        ]


def test_auth_check_ok(client: BinanceTestnetClient) -> None:
    with patch.object(
        BinanceTestnetClient,
        "get_account",
        return_value={
            "canTrade": True,
            "uid": 7,
            "accountType": "SPOT",
            "permissions": ["SPOT"],
        },
    ):
        result = client.auth_check()
    assert result.ok is True
    assert result.can_trade is True
    assert result.uid == 7


def test_auth_check_failure(client: BinanceTestnetClient) -> None:
    with patch.object(
        BinanceTestnetClient,
        "get_account",
        side_effect=ValidationError("binance testnet HTTP 401"),
    ):
        result = client.auth_check()
    assert result.ok is False
    assert result.error is not None


def test_timestamp_retry_on_1021(client: BinanceTestnetClient) -> None:
    calls = {"n": 0}

    def fake_urlopen(req: object, timeout: float = 15.0) -> object:
        calls["n"] += 1
        if calls["n"] == 1:
            import io
            import urllib.error

            body = b'{"code":-1021,"msg":"timestamp"}'
            raise urllib.error.HTTPError(
                url="https://testnet.binance.vision/api/v3/account",
                code=400,
                msg="Bad Request",
                hdrs=None,
                fp=io.BytesIO(body),
            )
        if calls["n"] == 2:
            import io

            class _Resp:
                def read(self) -> bytes:
                    return b'{"serverTime": 9000000000000}'

                def __enter__(self) -> object:
                    return self

                def __exit__(self, *args: object) -> None:
                    return None

            return _Resp()
        import io

        class _Resp:
            def read(self) -> bytes:
                return b'{"canTrade": true, "balances": []}'

            def __enter__(self) -> object:
                return self

            def __exit__(self, *args: object) -> None:
                return None

        return _Resp()

    with patch("urllib.request.urlopen", fake_urlopen):
        data = client.get_account()
    assert data["canTrade"] is True
    assert calls["n"] >= 3


def test_assess_strategy_funds_sufficient() -> None:
    balances = [
        TNBalance(asset="USDT", free="100", locked="0"),
        TNBalance(asset="BTC", free="0.01", locked="0"),
    ]
    check = assess_strategy_funds(balances, symbol="BTCUSDT")
    assert check.sufficient_for_strategy is True
    assert check.has_quote_usdt is True


def test_assess_strategy_funds_insufficient() -> None:
    balances = [TNBalance(asset="ETH", free="1", locked="0")]
    check = assess_strategy_funds(balances, symbol="BTCUSDT", min_notional_usdt=Decimal("10"))
    assert check.sufficient_for_strategy is False


def test_run_diagnostic_skip_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BINANCE_DEMO_API_KEY", raising=False)
    monkeypatch.delenv("BINANCE_DEMO_API_SECRET", raising=False)
    payload = run_testnet_diagnostic(skip_network=True)
    assert payload["testnet_ready"] is False
    assert payload["connectivity"]["skipped"] is True
    report = format_diagnostic_report(payload)
    assert "TESTNET READY: NO" in report
