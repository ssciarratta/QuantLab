"""Registry multiplataforma de brokers (Fase 19 + plugins F24)."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from quantlab.brokers.a3.adapter_port import A3BrokerPort
from quantlab.brokers.binance.fake import FakeBinanceBroker
from quantlab.brokers.generic.csv_md import GenericCsvMdBroker
from quantlab.brokers.generic.rest_skeleton import FakeRestMdBroker
from quantlab.brokers.mode import ModeGuard, OperatingMode
from quantlab.brokers.paper.broker import PaperBroker
from quantlab.brokers.plugins import load_entry_point_brokers
from quantlab.brokers.port import BrokerPort
from quantlab.core.exceptions import ValidationError

BrokerFactory = Callable[..., BrokerPort]


class BrokerRegistry:
    """Factories por ``venue_id`` → ``BrokerPort`` tipado."""

    def __init__(self) -> None:
        self._factories: dict[str, BrokerFactory] = {}
        self._plugin_venues: set[str] = set()

    def has_venue(self, venue_id: str) -> bool:
        return venue_id.strip().lower() in self._factories

    def register(
        self,
        venue_id: str,
        factory: BrokerFactory,
        *,
        from_plugin: bool = False,
    ) -> None:
        key = venue_id.strip().lower()
        if not key:
            raise ValidationError("venue_id vacío")
        # Plugins no pueden sombrear builtins / venues ya registrados (Zero-Trust F24).
        if from_plugin and key in self._factories:
            raise ValidationError(
                f"plugin venue rechazado: '{key}' ya registrado (no shadow)"
            )
        self._factories[key] = factory
        if from_plugin:
            self._plugin_venues.add(key)
        else:
            self._plugin_venues.discard(key)

    def create(self, venue_id: str, mode: OperatingMode, **opts: Any) -> BrokerPort:
        ModeGuard.validate_boot(mode)
        key = venue_id.strip().lower()
        factory = self._factories.get(key)
        if factory is None:
            known = ", ".join(sorted(self._factories)) or "(ninguno)"
            raise ValidationError(f"venue desconocido: {venue_id!r}; registrados: {known}")
        if opts:
            try:
                return factory(mode, **opts)
            except TypeError:
                return factory(mode)
        return factory(mode)

    def list_venues(self) -> list[str]:
        return sorted(self._factories)

    def list_plugin_venues(self) -> list[str]:
        return sorted(self._plugin_venues)


def _a3_factory(
    mode: OperatingMode,
    *,
    md_source: str = "fake",
    **_: Any,
) -> BrokerPort:
    md = A3BrokerPort(mode=mode, md_source=md_source)
    if mode is OperatingMode.PAPER:
        return PaperBroker(md)
    return md


def _binance_factory(mode: OperatingMode, **_: Any) -> BrokerPort:
    fake = FakeBinanceBroker(mode=mode)
    if mode is OperatingMode.PAPER:
        return PaperBroker(fake)
    return fake


def _paper_factory(
    mode: OperatingMode,
    *,
    md_source: str = "fake",
    **_: Any,
) -> BrokerPort:
    """Venue explícito ``paper``: siempre PaperBroker sobre A3 MD."""
    return PaperBroker(A3BrokerPort(mode=mode, md_source=md_source))


def _generic_csv_factory(
    mode: OperatingMode,
    *,
    csv_path: str | None = None,
    **_: Any,
) -> BrokerPort:
    path = (csv_path or os.environ.get("QUANTLAB_GENERIC_CSV_PATH") or "").strip() or None
    md = GenericCsvMdBroker(csv_path=path, mode=mode)
    if mode is OperatingMode.PAPER:
        return PaperBroker(md)
    return md


def _generic_rest_factory(mode: OperatingMode, **_: Any) -> BrokerPort:
    md = FakeRestMdBroker(mode=mode)
    if mode is OperatingMode.PAPER:
        return PaperBroker(md)
    return md


def register_builtin_brokers(registry: BrokerRegistry) -> BrokerRegistry:
    """Registra factories built-in (a3, binance, paper, generic_csv, generic_rest)."""
    registry.register("a3", _a3_factory)
    registry.register("binance", _binance_factory)
    registry.register("paper", _paper_factory)
    registry.register("generic_csv", _generic_csv_factory)
    registry.register("generic_rest", _generic_rest_factory)
    return registry


_DEFAULT: BrokerRegistry | None = None


def get_default_registry() -> BrokerRegistry:
    """Singleton con builtins + entry-point plugins."""
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = register_builtin_brokers(BrokerRegistry())
        load_entry_point_brokers(_DEFAULT)
    return _DEFAULT


def reset_default_registry() -> None:
    """Limpia singleton (tests / reload plugins)."""
    global _DEFAULT
    _DEFAULT = None
