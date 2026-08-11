"""Puente estrategia → órdenes Binance testnet (espejo best-effort tras fill paper)."""

from __future__ import annotations

from typing import Any, Literal

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import IntentType
from quantlab.core.types.orders import OrderIntent
from quantlab.execution.strategy_execution.destinations import ExecutionDestination

TestnetMirrorMode = Literal["none", "spot", "futures"]


def mirror_mode_for_destination(
    destination: ExecutionDestination | str,
) -> TestnetMirrorMode:
    raw = destination.value if isinstance(destination, ExecutionDestination) else str(destination)
    if raw == ExecutionDestination.BINANCE_SPOT_TESTNET.value:
        return "spot"
    if raw == ExecutionDestination.BINANCE_FUTURES_TESTNET.value:
        return "futures"
    return "none"


def testnet_ready(*, market: TestnetMirrorMode) -> dict[str, Any]:
    """Estado de keys/flags para espejo testnet (sin unlock)."""
    from quantlab.brokers.binance.demo_transport import demo_transport_status
    from quantlab.brokers.binance.futures_testnet_client import futures_testnet_remote_enabled
    from quantlab.brokers.binance.testnet_client import testnet_remote_enabled
    from quantlab.execution.live_unlock import is_live_session_unlocked

    unlocked = is_live_session_unlocked()
    dt = demo_transport_status(unlocked=unlocked)
    transport = dt.get("transport")
    if market == "spot":
        ready = unlocked and testnet_remote_enabled() and transport == "binance_spot_testnet"
        return {
            "market": "spot",
            "ready": ready,
            "unlocked": unlocked,
            "transport": transport,
            "detail": dt.get("spot"),
            "note": "Requiere unlock demo + QUANTLAB_DEMO_USE_TESTNET=1 + BINANCE_DEMO_*",
        }
    if market == "futures":
        ready = unlocked and futures_testnet_remote_enabled() and transport == "binance_futures_testnet"
        return {
            "market": "futures",
            "ready": ready,
            "unlocked": unlocked,
            "transport": transport,
            "detail": dt.get("futures"),
            "note": "Requiere unlock demo + QUANTLAB_DEMO_USE_FUTURES_TESTNET=1 + BINANCE_FUTURES_DEMO_*",
        }
    return {"market": "none", "ready": False}


def mirror_intent_to_testnet(
    intent: OrderIntent,
    *,
    market: TestnetMirrorMode,
) -> dict[str, Any]:
    """Envía intent PLACE_ORDER al testnet remoto vía demo router (best-effort)."""
    if market == "none":
        return {"ok": False, "skipped": True, "reason": "mirror desactivado"}
    if intent.intent_type is not IntentType.PLACE_ORDER:
        return {"ok": False, "skipped": True, "reason": "solo PLACE_ORDER"}
    readiness = testnet_ready(market=market)
    if not readiness.get("ready"):
        return {
            "ok": False,
            "skipped": True,
            "reason": "testnet no listo",
            "readiness": readiness,
        }
    try:
        from quantlab.brokers.binance.demo_router import get_shared_demo_router

        router = get_shared_demo_router()
        ack = router.submit(intent)
        return {
            "ok": True,
            "order_id": ack.order_id,
            "status": ack.status,
            "message": ack.message,
            "market": market,
        }
    except ValidationError as exc:
        return {"ok": False, "error": str(exc), "market": market}
    except Exception as exc:  # noqa: BLE001 — espejo best-effort
        return {"ok": False, "error": str(exc), "market": market}
