"""Destinos de ejecución estrategia (paper / testnet). Producción bloqueada."""

from __future__ import annotations

from enum import StrEnum


class ExecutionDestination(StrEnum):
    PAPER = "PAPER"
    BINANCE_SPOT_TESTNET = "BINANCE_SPOT_TESTNET"
    BINANCE_FUTURES_TESTNET = "BINANCE_FUTURES_TESTNET"


class MarketDataSource(StrEnum):
    """Fuente MD — separada del destino de órdenes."""

    BINANCE_PUBLIC_MD = "BINANCE_PUBLIC_MD"
    TESTNET_MD = "TESTNET_MD"


class ExecutionSessionState(StrEnum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    PREFLIGHT_OK = "PREFLIGHT_OK"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    UPDATING = "UPDATING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"
    KILLED = "KILLED"


class CertificationStatus(StrEnum):
    RESEARCH_ONLY = "RESEARCH_ONLY"
    ADAPTER_REQUIRED = "ADAPTER_REQUIRED"
    PAPER_READY = "PAPER_READY"
    SPOT_TESTNET_READY = "SPOT_TESTNET_READY"
    FUTURES_TESTNET_READY = "FUTURES_TESTNET_READY"
    CERTIFIED = "CERTIFIED"


MAX_ACTIVE_STRATEGIES = 1

__all__ = [
    "CertificationStatus",
    "ExecutionDestination",
    "ExecutionSessionState",
    "MarketDataSource",
    "MAX_ACTIVE_STRATEGIES",
]
