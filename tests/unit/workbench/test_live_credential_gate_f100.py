"""Tests LIVE credential gate + Binance public MD (F100)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from quantlab import __version__
from quantlab.brokers import ModeGuard, OperatingMode
from quantlab.brokers.binance.public_md import BinancePublicMdClient, scan_binance_usdt
from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import (
    LIVE_BLOCKED,
    LiveOrderRouter,
    assert_live_routing_blocked,
)
from quantlab.execution.live_unlock import (
    lock_live_session,
    reset_live_unlock_for_tests,
    unlock_live_session,
)
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import (
    ApiError,
    WorkbenchState,
    handle_get_live_status,
    handle_post_live_lock,
    handle_post_live_unlock,
)
from quantlab.workbench.session import WorkbenchSession


@pytest.fixture(autouse=True)
def _clean_unlock() -> None:
    reset_live_unlock_for_tests()
    yield
    reset_live_unlock_for_tests()


def test_live_blocked_constant_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "1.00.0"
    assert PHASES_SUMMARY == "F19–F110 INTERNAL"
    assert not Path("docs/audit/FASE_100_APPROVED.md").exists()


def test_without_unlock_still_blocked() -> None:
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        assert_live_routing_blocked()
    with pytest.raises(ValidationError, match="LIVE"):
        ModeGuard.validate_boot(OperatingMode.LIVE)


def test_unlock_requires_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("QUANTLAB_LIVE_USER", raising=False)
    monkeypatch.delenv("QUANTLAB_LIVE_PASSWORD", raising=False)
    with pytest.raises(ValidationError, match="no configurado"):
        unlock_live_session(username="u", password="p")


def test_unlock_with_valid_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QUANTLAB_LIVE_USER", "demo_op")
    monkeypatch.setenv("QUANTLAB_LIVE_PASSWORD", "demo_secret")
    session = unlock_live_session(username="demo_op", password="demo_secret")
    assert session.venue_scope == "binance_demo"
    assert_live_routing_blocked()  # no raise
    ModeGuard.validate_boot(OperatingMode.LIVE)  # no raise
    router = LiveOrderRouter()
    assert router.status()["transport"] == "local_demo_sim"


def test_bad_password_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QUANTLAB_LIVE_USER", "demo_op")
    monkeypatch.setenv("QUANTLAB_LIVE_PASSWORD", "demo_secret")
    with pytest.raises(ValidationError, match="inválidas"):
        unlock_live_session(username="demo_op", password="wrong")


def test_lock_revokes_unlock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QUANTLAB_LIVE_USER", "demo_op")
    monkeypatch.setenv("QUANTLAB_LIVE_PASSWORD", "demo_secret")
    unlock_live_session(username="demo_op", password="demo_secret")
    lock_live_session()
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        assert_live_routing_blocked()


def test_api_unlock_lock_roundtrip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("QUANTLAB_LIVE_USER", "demo_op")
    monkeypatch.setenv("QUANTLAB_LIVE_PASSWORD", "demo_secret")
    session = WorkbenchSession.create_or_load(tmp_path, "live")
    state = WorkbenchState(session=session, session_parent=tmp_path)

    status = handle_get_live_status(state)
    assert status["unlocked"] is False
    assert status["live_blocked"] is True

    unlocked = handle_post_live_unlock(
        state,
        {"username": "demo_op", "password": "demo_secret", "venue_scope": "binance_demo"},
    )
    assert unlocked["unlocked"] is True
    assert unlocked["username"] == "demo_op"
    assert "password" not in unlocked

    locked = handle_post_live_lock(state, {})
    assert locked["unlocked"] is False


def test_api_unlock_rejects_bad_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("QUANTLAB_LIVE_USER", "demo_op")
    monkeypatch.setenv("QUANTLAB_LIVE_PASSWORD", "demo_secret")
    session = WorkbenchSession.create_or_load(tmp_path, "live2")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    with pytest.raises(ApiError) as exc:
        handle_post_live_unlock(
            state, {"username": "demo_op", "password": "nope", "venue_scope": "binance_demo"}
        )
    assert exc.value.status == 401


def test_binance_public_scan_mocked() -> None:
    exchange = {
        "symbols": [
            {"symbol": "BTCUSDT", "status": "TRADING", "quoteAsset": "USDT"},
            {"symbol": "ETHUSDT", "status": "TRADING", "quoteAsset": "USDT"},
            {"symbol": "BTCBUSD", "status": "TRADING", "quoteAsset": "BUSD"},
        ]
    }
    ticker = {"symbol": "BTCUSDT", "bidPrice": "60000.1", "askPrice": "60001.2"}

    def fake_get(self: BinancePublicMdClient, path: str) -> object:
        if path.startswith("/api/v3/exchangeInfo"):
            return exchange
        if path.startswith("/api/v3/ticker/bookTicker"):
            return ticker
        if path.startswith("/api/v3/ping"):
            return {}
        raise AssertionError(path)

    with patch.object(BinancePublicMdClient, "_get_json", fake_get):
        payload = scan_binance_usdt(limit=10)
    assert payload["ok"] is True
    assert payload["read_only"] is True
    assert payload["live_routing"] is False
    assert "BTCUSDT" in payload["symbols"]
    assert "BTCBUSD" not in payload["symbols"]
    assert payload["tickers"][0]["symbol"] == "BTCUSDT"


def test_guided_lab_static_has_unlock_and_binance_scan() -> None:
    root = Path(__file__).resolve().parents[3] / "src" / "quantlab" / "workbench" / "static"
    js = (root / "js" / "panes" / "guided_lab.js").read_text(encoding="utf-8")
    assert "QLApi.liveUnlock" in js
    assert "QLApi.binanceScan" in js
    assert "QUANTLAB_LIVE_USER" in js
    api = (root / "js" / "api.js").read_text(encoding="utf-8")
    assert "/api/live/unlock" in api
    assert "/api/lab/binance/scan" in api
