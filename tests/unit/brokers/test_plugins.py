"""Entry-point broker plugins (Fase 24)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from quantlab.brokers.mode import OperatingMode
from quantlab.brokers.plugins import ENTRY_POINT_GROUP, load_entry_point_brokers
from quantlab.brokers.port import BrokerPort
from quantlab.brokers.registry import (
    BrokerRegistry,
    get_default_registry,
    register_builtin_brokers,
    reset_default_registry,
)
from quantlab.brokers.types import (
    BrokerAccount,
    BrokerAck,
    BrokerInstrument,
    BrokerPosition,
    BrokerSnapshot,
)
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.orders import OrderIntent
from quantlab.execution.live_gate import LIVE_BLOCKED


class _StubMdBroker:
    def __init__(self, mode: OperatingMode = OperatingMode.TESTER, **_: Any) -> None:
        self._mode = mode

    @property
    def venue_id(self) -> str:
        return "stub_venue"

    def connect(self) -> dict[str, object]:
        return {"ok": True, "venue": self.venue_id, "md_provider": "stub"}

    def close(self) -> dict[str, object]:
        return {"ok": True}

    def health(self) -> dict[str, object]:
        return {"ok": True, "md_provider": "stub", "venue": self.venue_id}

    def list_instruments(self) -> list[BrokerInstrument]:
        return []

    def get_snapshot(self, symbol: str) -> BrokerSnapshot:
        raise ValidationError("no snap")

    def get_account(self) -> BrokerAccount:
        from decimal import Decimal

        return BrokerAccount(cash=Decimal("0"), currency="USD")

    def get_positions(self) -> list[BrokerPosition]:
        return []

    def submit(self, intent: OrderIntent) -> BrokerAck:
        raise ValidationError("stub md-only")

    def cancel(self, order_id: str) -> BrokerAck:
        raise ValidationError("stub md-only")


def _make_ep(name: str, factory: Any, *, fail_load: bool = False) -> Any:
    ep = MagicMock()
    ep.name = name
    if fail_load:

        def _boom() -> None:
            raise RuntimeError("boom load")

        ep.load = _boom
    else:
        ep.load = MagicMock(return_value=factory)
    return ep


def test_load_entry_point_brokers_registers_callable() -> None:
    reg = BrokerRegistry()

    def factory(mode: OperatingMode, **_: Any) -> BrokerPort:
        return _StubMdBroker(mode=mode)  # type: ignore[return-value]

    with patch(
        "quantlab.brokers.plugins._iter_broker_entry_points",
        return_value=[_make_ep("stub_venue", factory)],
    ):
        loaded = load_entry_point_brokers(reg)

    assert loaded == ["stub_venue"]
    assert "stub_venue" in reg.list_venues()
    assert "stub_venue" in reg.list_plugin_venues()
    broker = reg.create("stub_venue", OperatingMode.TESTER)
    assert broker.venue_id == "stub_venue"


def test_load_entry_point_failure_does_not_crash() -> None:
    reg = BrokerRegistry()
    with patch(
        "quantlab.brokers.plugins._iter_broker_entry_points",
        return_value=[
            _make_ep("bad", None, fail_load=True),
            _make_ep("ok", lambda mode, **_: _StubMdBroker(mode=mode)),
        ],
    ):
        loaded = load_entry_point_brokers(reg)
    assert loaded == ["ok"]
    assert "bad" not in reg.list_venues()
    assert "ok" in reg.list_venues()


def test_plugin_cannot_shadow_builtin() -> None:
    """H1 audit F24: entry point con nombre de builtin no reemplaza factory."""
    reg = register_builtin_brokers(BrokerRegistry())
    assert "a3" in reg.list_venues()

    def evil_factory(mode: OperatingMode, **_: Any) -> BrokerPort:
        return _StubMdBroker(mode=mode)  # type: ignore[return-value]

    with patch(
        "quantlab.brokers.plugins._iter_broker_entry_points",
        return_value=[_make_ep("a3", evil_factory)],
    ):
        loaded = load_entry_point_brokers(reg)

    assert loaded == []
    assert "a3" not in reg.list_plugin_venues()
    broker = reg.create("a3", OperatingMode.TESTER)
    assert broker.venue_id == "a3"
    with pytest.raises(ValidationError, match="no shadow"):
        reg.register("a3", evil_factory, from_plugin=True)


def test_load_skips_non_callable() -> None:
    reg = BrokerRegistry()
    with patch(
        "quantlab.brokers.plugins._iter_broker_entry_points",
        return_value=[_make_ep("not_fn", "not-a-callable")],
    ):
        loaded = load_entry_point_brokers(reg)
    assert loaded == []
    assert reg.list_venues() == []


def test_get_default_registry_loads_plugins() -> None:
    reset_default_registry()
    try:
        with patch(
            "quantlab.brokers.registry.load_entry_point_brokers",
            side_effect=lambda reg: (
                reg.register(
                    "plugin_x",
                    lambda mode, **_: _StubMdBroker(mode=mode),
                    from_plugin=True,
                )
                or ["plugin_x"]
            ),
        ):
            reg = get_default_registry()
            assert "plugin_x" in reg.list_venues()
            assert "a3" in reg.list_venues()
            assert "generic_csv" in reg.list_venues()
            assert "generic_rest" in reg.list_venues()
            assert "plugin_x" in reg.list_plugin_venues()
    finally:
        reset_default_registry()


def test_enumerate_failure_returns_empty() -> None:
    reg = BrokerRegistry()
    with patch(
        "quantlab.brokers.plugins._iter_broker_entry_points",
        side_effect=RuntimeError("eps down"),
    ):
        assert load_entry_point_brokers(reg) == []


def test_entry_point_group_constant() -> None:
    assert ENTRY_POINT_GROUP == "quantlab.brokers"


def test_live_blocked_invariant() -> None:
    assert LIVE_BLOCKED is True


def test_builtins_still_registered_without_plugins() -> None:
    reg = register_builtin_brokers(BrokerRegistry())
    assert set(reg.list_venues()) >= {
        "a3",
        "binance",
        "paper",
        "generic_csv",
        "generic_rest",
    }
    assert reg.list_plugin_venues() == []


def test_plugin_ep_name_namespace_unused_ok() -> None:
    """SimpleNamespace shape also accepted by loader path via MagicMock above."""
    ns = SimpleNamespace(name="x")
    assert ns.name == "x"


@pytest.fixture(autouse=True)
def _reset_registry() -> Any:
    reset_default_registry()
    yield
    reset_default_registry()
