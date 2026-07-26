"""quantlab.brokers — Operating Modes + BrokerPort multiplataforma."""

from quantlab.brokers.contracts import BROKER_PLUGIN_API_VERSION, BrokerPluginSpec
from quantlab.brokers.mode import (
    REAL_ALIAS,
    ModeGuard,
    OperatingMode,
    default_mode,
    resolve_mode,
)
from quantlab.brokers.paper.book import PaperBook
from quantlab.brokers.paper.broker import PaperBroker
from quantlab.brokers.paper.journal import PaperFillJournal
from quantlab.brokers.port import BrokerPort
from quantlab.brokers.read_only import ReadOnlyBrokerPort
from quantlab.brokers.registry import (
    BrokerRegistry,
    get_default_registry,
    reset_default_registry,
)

__all__ = [
    "OperatingMode",
    "REAL_ALIAS",
    "ModeGuard",
    "resolve_mode",
    "default_mode",
    "BrokerPort",
    "ReadOnlyBrokerPort",
    "BrokerPluginSpec",
    "BROKER_PLUGIN_API_VERSION",
    "BrokerRegistry",
    "PaperBook",
    "PaperBroker",
    "PaperFillJournal",
    "get_default_registry",
    "reset_default_registry",
]
