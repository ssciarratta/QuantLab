"""quantlab.brokers — Operating Modes + BrokerPort multiplataforma (Fase 19)."""

from quantlab.brokers.mode import (
    REAL_ALIAS,
    ModeGuard,
    OperatingMode,
    default_mode,
    resolve_mode,
)
from quantlab.brokers.paper.broker import PaperBroker
from quantlab.brokers.paper.journal import PaperFillJournal
from quantlab.brokers.port import BrokerPort
from quantlab.brokers.registry import BrokerRegistry, get_default_registry

__all__ = [
    "OperatingMode",
    "REAL_ALIAS",
    "ModeGuard",
    "resolve_mode",
    "default_mode",
    "BrokerPort",
    "BrokerRegistry",
    "PaperBroker",
    "PaperFillJournal",
    "get_default_registry",
]
