"""Adversarial coverage for Broker Plugin Contract v1 (F87)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast
from unittest.mock import patch

import pytest

from quantlab.brokers.contracts.v1 import (
    BROKER_PLUGIN_API_VERSION,
    BrokerPluginSpec,
)
from quantlab.brokers.mode import OperatingMode
from quantlab.brokers.plugins import LegacyBrokerPluginWarning, load_entry_point_brokers
from quantlab.brokers.port import BrokerPort
from quantlab.brokers.read_only import ReadOnlyBrokerPort
from quantlab.brokers.registry import BrokerRegistry, register_builtin_brokers
from quantlab.brokers.testing.contract_v1 import run_broker_contract
from quantlab.brokers.types import (
    BrokerAccount,
    BrokerAck,
    BrokerInstrument,
    BrokerPosition,
    BrokerSnapshot,
)
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.orders import OrderIntent


class _Plugin:
    def __init__(self, venue: str = "fixture") -> None:
        self._venue = venue
        self.submit_calls = 0
        self.cancel_calls = 0

    @property
    def venue_id(self) -> str:
        return self._venue

    def connect(self) -> dict[str, object]:
        return {"ok": True}

    def close(self) -> dict[str, object]:
        return {"ok": True}

    def health(self) -> dict[str, object]:
        return {"ok": True}

    def list_instruments(self) -> list[BrokerInstrument]:
        return [BrokerInstrument("TEST", "Offline fixture", "USD", "OPEN")]

    def get_snapshot(self, symbol: str) -> BrokerSnapshot:
        return BrokerSnapshot(
            symbol=symbol,
            bid=Decimal("10"),
            ask=Decimal("11"),
            last=Decimal("10.5"),
            ts=datetime(2026, 7, 26, tzinfo=UTC),
        )

    def get_account(self) -> BrokerAccount:
        return BrokerAccount(cash=Decimal("1000"), currency="USD", equity=Decimal("1001"))

    def get_positions(self) -> list[BrokerPosition]:
        return [BrokerPosition(symbol="TEST", quantity=Decimal("1"), avg_price=Decimal("10"))]

    def submit(self, intent: OrderIntent) -> BrokerAck:
        del intent
        self.submit_calls += 1
        return BrokerAck("unsafe", "", "NEW")

    def cancel(self, order_id: str) -> BrokerAck:
        del order_id
        self.cancel_calls += 1
        return BrokerAck("unsafe", "", "CANCELED")


class _BadSnapshotPlugin(_Plugin):
    def get_snapshot(self, symbol: str) -> BrokerSnapshot:
        return BrokerSnapshot(
            symbol=symbol,
            bid=Decimal("NaN"),
            ask=Decimal("11"),
            last=Decimal("10.5"),
            ts=datetime(2026, 7, 26),
        )


class _BadDtoPlugin(_Plugin):
    def list_instruments(self) -> list[BrokerInstrument]:
        return cast(list[BrokerInstrument], [{"symbol": "wrong"}])


class _EntryPoint:
    def __init__(self, name: str, published: object) -> None:
        self.name = name
        self._published = published

    def load(self) -> object:
        return self._published


def _factory(mode: OperatingMode) -> BrokerPort:
    del mode
    return _Plugin()


def test_valid_spec_is_frozen_and_has_v1_capabilities() -> None:
    spec = BrokerPluginSpec(
        api_version=BROKER_PLUGIN_API_VERSION,
        venue_id="fixture_1",
        capabilities=frozenset({"market_data", "account_read"}),
        factory=_factory,
    )
    assert spec.api_version == "1"
    assert spec.capabilities == frozenset({"market_data", "account_read"})
    with pytest.raises(FrozenInstanceError):
        spec.venue_id = "other"  # type: ignore[misc]


@pytest.mark.parametrize("venue", ["", "UPPER", "space venue", ".hidden", "x" * 65])
def test_spec_rejects_invalid_venue_id(venue: str) -> None:
    with pytest.raises(ValidationError, match="venue_id"):
        BrokerPluginSpec("1", venue, frozenset({"market_data"}), _factory)


def test_spec_rejects_wrong_version_execution_and_empty_capabilities() -> None:
    with pytest.raises(ValidationError, match="api_version"):
        BrokerPluginSpec("2", "fixture", frozenset({"market_data"}), _factory)
    with pytest.raises(ValidationError, match="ejecución prohibida"):
        BrokerPluginSpec("1", "fixture", frozenset({"execution"}), _factory)
    with pytest.raises(ValidationError, match="al menos una"):
        BrokerPluginSpec("1", "fixture", frozenset(), _factory)


def test_registry_does_not_retry_internal_type_error() -> None:
    calls = 0

    def broken(mode: OperatingMode, **opts: Any) -> BrokerPort:
        nonlocal calls
        del mode, opts
        calls += 1
        raise TypeError("plugin implementation bug")

    registry = BrokerRegistry()
    registry.register("broken", broken, from_plugin=True)
    with pytest.raises(TypeError, match="implementation bug"):
        registry.create("broken", OperatingMode.TESTER, fixture=True)
    assert calls == 1


def test_registry_rejects_unsupported_options_before_factory() -> None:
    calls = 0

    def no_options(mode: OperatingMode) -> BrokerPort:
        nonlocal calls
        del mode
        calls += 1
        return _Plugin()

    registry = BrokerRegistry()
    registry.register("fixture", no_options, from_plugin=True)
    with pytest.raises(ValidationError, match=r"no acepta.*unsupported"):
        registry.create("fixture", OperatingMode.TESTER, unsupported=True)
    assert calls == 0


def test_live_is_rejected_before_plugin_factory() -> None:
    calls = 0

    def counted(mode: OperatingMode) -> BrokerPort:
        nonlocal calls
        del mode
        calls += 1
        return _Plugin()

    registry = BrokerRegistry()
    registry.register("fixture", counted, from_plugin=True)
    with pytest.raises(ValidationError, match="LIVE_BLOCKED"):
        registry.create("fixture", OperatingMode.LIVE)
    assert calls == 0


def test_registry_wraps_plugin_and_never_calls_malicious_execution() -> None:
    plugin = _Plugin()
    registry = BrokerRegistry()
    registry.register("fixture", lambda mode: plugin, from_plugin=True)

    broker = registry.create("fixture", OperatingMode.TESTER)
    assert isinstance(broker, ReadOnlyBrokerPort)
    assert broker.get_account().currency == "USD"
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        broker.submit(cast(OrderIntent, object()))
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        broker.cancel("unsafe")
    assert plugin.submit_calls == 0
    assert plugin.cancel_calls == 0


def test_contract_passes_calls_factory_once_and_does_not_probe_plugin_execution() -> None:
    calls = 0
    plugin = _Plugin()

    def counted(mode: OperatingMode) -> BrokerPort:
        nonlocal calls
        del mode
        calls += 1
        return plugin

    spec = BrokerPluginSpec(
        "1",
        "fixture",
        frozenset({"market_data", "account_read"}),
        counted,
    )
    report = run_broker_contract(spec)

    assert report.passed is True
    assert report.issues == ()
    assert "registry.execution_blocked" in report.checks
    assert calls == 1
    assert plugin.submit_calls == 0
    assert plugin.cancel_calls == 0


def test_contract_reports_bad_decimal_and_naive_snapshot_timestamp() -> None:
    spec = BrokerPluginSpec(
        "1",
        "fixture",
        frozenset({"market_data"}),
        lambda mode: _BadSnapshotPlugin(),
    )
    report = run_broker_contract(spec)
    assert report.passed is False
    assert any("finite Decimal" in issue for issue in report.issues)
    assert any("timezone-aware" in issue for issue in report.issues)


def test_contract_reports_bad_dto_without_raising() -> None:
    spec = BrokerPluginSpec(
        "1",
        "fixture",
        frozenset({"market_data"}),
        lambda mode: _BadDtoPlugin(),
    )
    report = run_broker_contract(spec)
    assert report.passed is False
    assert any("list[BrokerInstrument]" in issue for issue in report.issues)


def test_v1_entry_point_provider_uses_spec_venue_and_read_only_wrapper() -> None:
    spec = BrokerPluginSpec("1", "fixture", frozenset({"market_data"}), _factory)
    provider_calls = 0

    def provider() -> BrokerPluginSpec:
        nonlocal provider_calls
        provider_calls += 1
        return spec

    registry = BrokerRegistry()
    with patch(
        "quantlab.brokers.plugins._iter_broker_entry_points",
        return_value=[_EntryPoint("distribution_alias", provider)],
    ):
        loaded = load_entry_point_brokers(registry)
    assert loaded == ["fixture"]
    assert provider_calls == 1
    assert isinstance(registry.create("fixture", OperatingMode.TESTER), ReadOnlyBrokerPort)


def test_legacy_factory_warns_and_is_always_read_only() -> None:
    registry = BrokerRegistry()
    with patch(
        "quantlab.brokers.plugins._iter_broker_entry_points",
        return_value=[_EntryPoint("fixture", _factory)],
    ), pytest.warns(LegacyBrokerPluginWarning, match="legacy v0"):
        loaded = load_entry_point_brokers(registry)
    assert loaded == ["fixture"]
    assert isinstance(registry.create("fixture", OperatingMode.TESTER), ReadOnlyBrokerPort)


def test_v1_spec_cannot_shadow_builtin_even_with_different_ep_name() -> None:
    spec = BrokerPluginSpec(
        "1",
        "a3",
        frozenset({"market_data"}),
        lambda mode: _Plugin("a3"),
    )
    registry = register_builtin_brokers(BrokerRegistry())
    with patch(
        "quantlab.brokers.plugins._iter_broker_entry_points",
        return_value=[_EntryPoint("harmless_alias", lambda: spec)],
    ):
        assert load_entry_point_brokers(registry) == []
    assert "a3" not in registry.list_plugin_venues()
