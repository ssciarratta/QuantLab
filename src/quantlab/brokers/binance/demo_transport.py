"""Resolución de transport demo Binance (local / spot testnet / futures testnet)."""

from __future__ import annotations

from typing import Any, Literal

from quantlab.brokers.binance.futures_testnet_client import (
    futures_testnet_remote_enabled,
    futures_testnet_status,
)
from quantlab.brokers.binance.testnet_client import (
    testnet_remote_enabled,
    testnet_status,
)
from quantlab.core.exceptions import ValidationError

DemoTransport = Literal[
    "local_demo_sim",
    "binance_spot_testnet",
    "binance_futures_testnet",
]


def remote_testnet_conflict() -> bool:
    return testnet_remote_enabled() and futures_testnet_remote_enabled()


def resolve_demo_transport(*, unlocked: bool = True) -> DemoTransport:
    """Transport efectivo. Spot y Futures remoto son mutuamente excluyentes."""
    if not unlocked:
        return "local_demo_sim"
    if remote_testnet_conflict():
        raise ValidationError(
            "Spot y Futures testnet remoto están activos a la vez. "
            "Desactive QUANTLAB_DEMO_USE_TESTNET o "
            "QUANTLAB_DEMO_USE_FUTURES_TESTNET (solo uno)."
        )
    if futures_testnet_remote_enabled():
        return "binance_futures_testnet"
    if testnet_remote_enabled():
        return "binance_spot_testnet"
    return "local_demo_sim"


def demo_transport_status(*, unlocked: bool) -> dict[str, Any]:
    conflict = remote_testnet_conflict()
    transport: str | None
    error: str | None = None
    try:
        transport = resolve_demo_transport(unlocked=unlocked)
    except ValidationError as exc:
        transport = None
        error = str(exc)
    return {
        "unlocked": unlocked,
        "transport": transport,
        "conflict": conflict,
        "error": error,
        "spot": testnet_status(),
        "futures": futures_testnet_status(),
        "note": (
            "Default post-unlock: local_demo_sim. "
            "Spot: QUANTLAB_DEMO_USE_TESTNET=1 + BINANCE_DEMO_*. "
            "Futures: QUANTLAB_DEMO_USE_FUTURES_TESTNET=1 + BINANCE_FUTURES_DEMO_*. "
            "Solo un remoto a la vez."
        ),
    }
