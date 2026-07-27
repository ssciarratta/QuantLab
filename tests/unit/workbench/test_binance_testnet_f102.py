"""Tests Binance Spot Testnet opt-in (F102)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from quantlab import __version__
from quantlab.brokers.binance.demo_router import get_shared_demo_router
from quantlab.brokers.binance.testnet_client import (
    BinanceTestnetClient,
    testnet_remote_enabled as is_testnet_remote_enabled,
    testnet_status as read_testnet_status,
)
from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED, LiveOrderRouter
from quantlab.execution.live_unlock import reset_live_unlock_for_tests, unlock_live_session
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import WorkbenchState, handle_post_live_demo_submit
from quantlab.workbench.session import WorkbenchSession


@pytest.fixture(autouse=True)
def _clean(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_live_unlock_for_tests()
    monkeypatch.delenv("QUANTLAB_DEMO_USE_TESTNET", raising=False)
    monkeypatch.delenv("BINANCE_DEMO_API_KEY", raising=False)
    monkeypatch.delenv("BINANCE_DEMO_API_SECRET", raising=False)
    yield
    reset_live_unlock_for_tests()


def test_version_f102() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.95.0"
    assert PHASES_SUMMARY == "F19–F103 INTERNAL"
    assert not Path("docs/audit/FASE_102_APPROVED.md").exists()


def test_testnet_disabled_by_default() -> None:
    assert is_testnet_remote_enabled() is False
    st = read_testnet_status()
    assert st["remote_enabled"] is False
    assert st["keys_configured"] is False


def test_rejects_production_host() -> None:
    with pytest.raises(ValidationError, match="producción"):
        BinanceTestnetClient(
            api_key="k",
            api_secret="s",
            base_url="https://api.binance.com",
        )


def test_testnet_submit_mocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("QUANTLAB_LIVE_USER", "op")
    monkeypatch.setenv("QUANTLAB_LIVE_PASSWORD", "secret")
    monkeypatch.setenv("QUANTLAB_DEMO_USE_TESTNET", "1")
    monkeypatch.setenv("BINANCE_DEMO_API_KEY", "test_key")
    monkeypatch.setenv("BINANCE_DEMO_API_SECRET", "test_secret")
    unlock_live_session(username="op", password="secret")

    assert is_testnet_remote_enabled() is True

    def fake_request(
        self: BinanceTestnetClient,
        method: str,
        path: str,
        params: dict[str, str],
        *,
        signed: bool,
    ) -> dict[str, object]:
        assert method == "POST"
        assert path == "/api/v3/order"
        assert signed is True
        assert params["symbol"] == "BTCUSDT"
        assert params["side"] == "BUY"
        return {
            "orderId": 4242,
            "clientOrderId": params["newClientOrderId"],
            "status": "FILLED",
            "symbol": "BTCUSDT",
        }

    session = WorkbenchSession.create_or_load(tmp_path, "tn")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    with patch.object(BinanceTestnetClient, "_request", fake_request):
        out = handle_post_live_demo_submit(
            state, {"symbol": "BTCUSDT", "side": "BUY", "quantity": "0.001"}
        )
    assert out["ok"] is True
    assert out["transport"] == "binance_spot_testnet"
    assert out["order_id"] == "BN-TN-4242"
    assert get_shared_demo_router().status()["remote_testnet"] is True


def test_without_flag_stays_local(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("QUANTLAB_LIVE_USER", "op")
    monkeypatch.setenv("QUANTLAB_LIVE_PASSWORD", "secret")
    monkeypatch.setenv("BINANCE_DEMO_API_KEY", "test_key")
    monkeypatch.setenv("BINANCE_DEMO_API_SECRET", "test_secret")
    # sin QUANTLAB_DEMO_USE_TESTNET
    unlock_live_session(username="op", password="secret")
    router = LiveOrderRouter()
    assert router.status()["transport"] == "local_demo_sim"
    assert router.status()["remote_testnet"] is False
