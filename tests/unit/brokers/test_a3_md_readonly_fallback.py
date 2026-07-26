"""A3 MD read-only opt-in: env fallback a fake (Fase 24)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from quantlab.brokers.a3.adapter_port import A3BrokerPort
from quantlab.brokers.a3.md_backend import (
    MD_READONLY_ENV,
    MD_SOURCE_ENV,
    MD_SOURCE_FAKE,
    resolve_a3_md_backend,
)
from quantlab.brokers.mode import OperatingMode
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import IntentType, OrderSide, OrderType
from quantlab.core.types.orders import OrderIntent
from quantlab.data.exchanges.a3.fake_backend import FakeA3Backend
from quantlab.execution.live_gate import LIVE_BLOCKED


def test_default_md_source_is_fake() -> None:
    port = A3BrokerPort(mode=OperatingMode.TESTER)
    assert port.md_source == MD_SOURCE_FAKE
    assert port.md_provider == "a3-fake"
    health = port.health()
    assert health["md_provider"] == "a3-fake"
    assert health.get("md_fallback") is not True


def test_env_without_flag_falls_back_fake(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(MD_READONLY_ENV, raising=False)
    monkeypatch.setenv("QUANTLAB_A3_USER", "u")
    monkeypatch.setenv("QUANTLAB_A3_PASSWORD", "p")
    monkeypatch.setenv("QUANTLAB_A3_ACCOUNT", "a")
    backend, detail = resolve_a3_md_backend(MD_SOURCE_ENV)
    assert isinstance(backend, FakeA3Backend)
    assert detail["fallback"] is True
    assert MD_READONLY_ENV in detail["fallback_reason"]
    assert detail["md_provider"] == "a3-fake"

    port = A3BrokerPort(mode=OperatingMode.TESTER, md_source=MD_SOURCE_ENV)
    assert port.md_provider == "a3-fake"
    h = port.health()
    assert h["md_fallback"] is True


def test_env_without_creds_falls_back_fake(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(MD_READONLY_ENV, "1")
    monkeypatch.delenv("QUANTLAB_A3_USER", raising=False)
    monkeypatch.delenv("QUANTLAB_A3_PASSWORD", raising=False)
    monkeypatch.delenv("QUANTLAB_A3_ACCOUNT", raising=False)
    backend, detail = resolve_a3_md_backend(MD_SOURCE_ENV)
    assert isinstance(backend, FakeA3Backend)
    assert detail["fallback"] is True
    assert "QUANTLAB_A3" in detail["fallback_reason"]


def test_env_with_flag_and_creds_builds_pyrofex(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(MD_READONLY_ENV, "1")
    monkeypatch.setenv("QUANTLAB_A3_USER", "u")
    monkeypatch.setenv("QUANTLAB_A3_PASSWORD", "p")
    monkeypatch.setenv("QUANTLAB_A3_ACCOUNT", "a")

    fake_backend = MagicMock()
    fake_backend.health_check.return_value = {"ok": False, "provider": "pyRofex"}
    fake_backend.connect = MagicMock()
    fake_backend.close = MagicMock()
    fake_backend.get_instruments.return_value = []
    fake_backend.get_positions.return_value = []

    with patch(
        "quantlab.data.exchanges.a3.client.PyRofexBackend",
        return_value=fake_backend,
    ) as ctor:
        backend, detail = resolve_a3_md_backend(MD_SOURCE_ENV)
        assert backend is fake_backend
        assert detail["fallback"] is False
        assert detail["md_provider"] == "a3-env-readonly"
        ctor.assert_called_once()

        port = A3BrokerPort(mode=OperatingMode.PAPER, md_source=MD_SOURCE_ENV)
        assert port.md_provider == "a3-env-readonly"
        assert port.health()["md_provider"] == "a3-env-readonly"


def test_invalid_md_source_raises() -> None:
    with pytest.raises(ValidationError, match="md_source"):
        A3BrokerPort(mode=OperatingMode.TESTER, md_source="live_md")


def test_submit_cancel_always_blocked_even_with_env_meta(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert LIVE_BLOCKED is True
    monkeypatch.setenv(MD_READONLY_ENV, "1")
    # sin creds → fake fallback; submit sigue bloqueado
    port = A3BrokerPort(mode=OperatingMode.PAPER, md_source=MD_SOURCE_ENV)
    intent = OrderIntent(
        intent_id="x",
        intent_type=IntentType.PLACE_ORDER,
        instrument_id="DLR/DIC24",
        side=OrderSide.BUY,
        quantity=Decimal("1"),
        order_type=OrderType.MARKET,
    )
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        port.submit(intent)
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        port.cancel("OID-1")


def test_injected_backend_meta() -> None:
    port = A3BrokerPort(backend=FakeA3Backend(), mode=OperatingMode.TESTER, md_source="fake")
    assert port.md_provider == "a3-injected"
    port.connect()
    assert port.health()["md_provider"] == "a3-injected"


def test_connect_includes_fallback_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(MD_READONLY_ENV, raising=False)
    port = A3BrokerPort(mode=OperatingMode.TESTER, md_source="env")
    info: dict[str, Any] = port.connect()
    assert info["md_fallback"] is True
    assert "md_fallback_reason" in info
