"""Registry multiplataforma de brokers (Fase 19)."""

from __future__ import annotations

from collections.abc import Callable

from quantlab.brokers.a3.adapter_port import A3BrokerPort
from quantlab.brokers.binance.fake import FakeBinanceBroker
from quantlab.brokers.mode import ModeGuard, OperatingMode
from quantlab.brokers.paper.broker import PaperBroker
from quantlab.brokers.port import BrokerPort
from quantlab.core.exceptions import ValidationError

BrokerFactory = Callable[[OperatingMode], BrokerPort]


class BrokerRegistry:
    """Factories por ``venue_id`` → ``BrokerPort`` tipado."""

    def __init__(self) -> None:
        self._factories: dict[str, BrokerFactory] = {}

    def register(self, venue_id: str, factory: BrokerFactory) -> None:
        key = venue_id.strip().lower()
        if not key:
            raise ValidationError("venue_id vacío")
        self._factories[key] = factory

    def create(self, venue_id: str, mode: OperatingMode) -> BrokerPort:
        ModeGuard.validate_boot(mode)
        key = venue_id.strip().lower()
        factory = self._factories.get(key)
        if factory is None:
            known = ", ".join(sorted(self._factories)) or "(ninguno)"
            raise ValidationError(f"venue desconocido: {venue_id!r}; registrados: {known}")
        return factory(mode)

    def list_venues(self) -> list[str]:
        return sorted(self._factories)


def _a3_factory(mode: OperatingMode) -> BrokerPort:
    md = A3BrokerPort(mode=mode)
    if mode is OperatingMode.PAPER:
        return PaperBroker(md)
    return md


def _binance_factory(mode: OperatingMode) -> BrokerPort:
    fake = FakeBinanceBroker(mode=mode)
    if mode is OperatingMode.PAPER:
        return PaperBroker(fake)
    return fake


def _paper_factory(mode: OperatingMode) -> BrokerPort:
    """Venue explícito ``paper``: siempre PaperBroker sobre A3 MD fake."""
    return PaperBroker(A3BrokerPort(mode=mode))


def register_builtin_brokers(registry: BrokerRegistry) -> BrokerRegistry:
    """Registra factories built-in (a3, binance, paper)."""
    registry.register("a3", _a3_factory)
    registry.register("binance", _binance_factory)
    registry.register("paper", _paper_factory)
    return registry


_DEFAULT: BrokerRegistry | None = None


def get_default_registry() -> BrokerRegistry:
    """Singleton con builtins registrados."""
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = register_builtin_brokers(BrokerRegistry())
    return _DEFAULT
