"""Tests Binance Futures USD-M Testnet client + transport dual."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from quantlab.brokers.binance.demo_router import get_shared_demo_router
from quantlab.brokers.binance.demo_transport import (
    remote_testnet_conflict,
    resolve_demo_transport,
)
from quantlab.brokers.binance.futures_testnet_client import (
    BinanceFuturesTestnetClient,
    futures_testnet_remote_enabled,
    public_futures_connectivity_check,
)
from quantlab.brokers.binance.testnet_diagnostic import (
    run_combined_testnet_diagnostic,
    run_futures_testnet_diagnostic,
)
from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.execution.live_unlock import reset_live_unlock_for_tests, unlock_live_session
from quantlab.workbench.api import WorkbenchState, handle_post_live_demo_submit
from quantlab.workbench.session import WorkbenchSession


@pytest.fixture(autouse=True)
def _clean(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_live_unlock_for_tests()
    for key in (
        "QUANTLAB_DEMO_USE_TESTNET",
        "BINANCE_DEMO_API_KEY",
        "BINANCE_DEMO_API_SECRET",
        "QUANTLAB_DEMO_USE_FUTURES_TESTNET",
        "BINANCE_FUTURES_DEMO_API_KEY",
        "BINANCE_FUTURES_DEMO_API_SECRET",
    ):
        monkeypatch.delenv(key, raising=False)
    yield
    reset_live_unlock_for_tests()


def test_live_still_blocked() -> None:
    assert LIVE_BLOCKED is True


def test_futures_disabled_by_default() -> None:
    assert futures_testnet_remote_enabled() is False
    assert resolve_demo_transport(unlocked=True) == "local_demo_sim"


def test_rejects_production_fapi() -> None:
    for host in (
        "https://fapi.binance.com",
        "https://dapi.binance.com",
        "https://api.binance.com",
    ):
        with pytest.raises(ValidationError, match="producción"):
            BinanceFuturesTestnetClient(api_key="k", api_secret="s", base_url=host)


def test_rejects_spot_testnet_host() -> None:
    with pytest.raises(ValidationError, match="Futures Testnet"):
        BinanceFuturesTestnetClient(
            api_key="k",
            api_secret="s",
            base_url="https://testnet.binance.vision",
        )


def test_public_futures_connectivity_rejects_prod() -> None:
    with pytest.raises(ValidationError, match="producción"):
        public_futures_connectivity_check("https://fapi.binance.com")


def test_conflict_spot_and_futures(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QUANTLAB_DEMO_USE_TESTNET", "1")
    monkeypatch.setenv("BINANCE_DEMO_API_KEY", "sk")
    monkeypatch.setenv("BINANCE_DEMO_API_SECRET", "ss")
    monkeypatch.setenv("QUANTLAB_DEMO_USE_FUTURES_TESTNET", "1")
    monkeypatch.setenv("BINANCE_FUTURES_DEMO_API_KEY", "fk")
    monkeypatch.setenv("BINANCE_FUTURES_DEMO_API_SECRET", "fs")
    assert remote_testnet_conflict() is True
    with pytest.raises(ValidationError, match="activos a la vez"):
        resolve_demo_transport(unlocked=True)


def test_futures_transport_when_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QUANTLAB_DEMO_USE_FUTURES_TESTNET", "1")
    monkeypatch.setenv("BINANCE_FUTURES_DEMO_API_KEY", "fk")
    monkeypatch.setenv("BINANCE_FUTURES_DEMO_API_SECRET", "fs")
    assert resolve_demo_transport(unlocked=True) == "binance_futures_testnet"


def test_futures_submit_mocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("QUANTLAB_LIVE_USER", "op")
    monkeypatch.setenv("QUANTLAB_LIVE_PASSWORD", "secret")
    monkeypatch.setenv("QUANTLAB_DEMO_USE_FUTURES_TESTNET", "1")
    monkeypatch.setenv("BINANCE_FUTURES_DEMO_API_KEY", "test_key")
    monkeypatch.setenv("BINANCE_FUTURES_DEMO_API_SECRET", "test_secret")
    unlock_live_session(username="op", password="secret")

    def fake_request(
        self: BinanceFuturesTestnetClient,
        method: str,
        path: str,
        params: dict[str, str],
        *,
        signed: bool,
        _retry: bool = True,
    ) -> dict[str, object]:
        assert method == "POST"
        assert path == "/fapi/v1/order"
        assert signed is True
        assert params["symbol"] == "BTCUSDT"
        return {
            "orderId": 777,
            "clientOrderId": params["newClientOrderId"],
            "status": "FILLED",
            "symbol": "BTCUSDT",
            "avgPrice": "60100.5",
        }

    session = WorkbenchSession.create_or_load(tmp_path, "fut")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    with patch.object(BinanceFuturesTestnetClient, "_request", fake_request):
        out = handle_post_live_demo_submit(
            state, {"symbol": "BTCUSDT", "side": "BUY", "quantity": "0.001"}
        )
    assert out["ok"] is True
    assert out["transport"] == "binance_futures_testnet"
    assert out["order_id"] == "BN-FUT-TN-777"
    st = get_shared_demo_router().status()
    assert st["remote_market"] == "futures"


def test_get_balances_from_assets() -> None:
    client = BinanceFuturesTestnetClient(api_key="k", api_secret="s")

    def fake_request(
        _self: BinanceFuturesTestnetClient,
        method: str,
        path: str,
        _params: dict[str, str],
        *,
        signed: bool,
        _retry: bool = True,
    ) -> dict[str, object]:
        assert method == "GET"
        assert path == "/fapi/v2/account"
        assert signed is True
        return {
            "canTrade": True,
            "assets": [
                {
                    "asset": "USDT",
                    "walletBalance": "1000",
                    "availableBalance": "900",
                    "unrealizedProfit": "10",
                },
                {
                    "asset": "BTC",
                    "walletBalance": "0",
                    "availableBalance": "0",
                    "unrealizedProfit": "0",
                },
            ],
        }

    with patch.object(BinanceFuturesTestnetClient, "_request", fake_request):
        bals = client.get_balances(omit_zero=True)
    assert len(bals) == 1
    assert bals[0].asset == "USDT"
    assert bals[0].available_balance == "900"
    tn = bals[0].as_testnet_balance()
    assert tn.free == "900"
    assert tn.locked == "100"


def test_futures_diagnostic_skip_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QUANTLAB_DEMO_USE_FUTURES_TESTNET", "1")
    monkeypatch.setenv("BINANCE_FUTURES_DEMO_API_KEY", "fk")
    monkeypatch.setenv("BINANCE_FUTURES_DEMO_API_SECRET", "fs")
    payload = run_futures_testnet_diagnostic(skip_network=True)
    assert payload["market"] == "futures"
    assert payload["testnet_ready"] is False
    assert any("Unlock" in i for i in payload["issues"])


def test_combined_diagnostic_structure(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = run_combined_testnet_diagnostic(skip_network=True)
    assert "spot" in payload and "futures" in payload
    assert payload["spot_ready"] is False
    assert payload["futures_ready"] is False
    assert payload["production_blocked"] is True
