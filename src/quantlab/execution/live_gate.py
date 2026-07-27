"""Gate irrenunciable: order routing LIVE (TD-10 / F100–F101).

``LIVE_BLOCKED=True`` significa: LIVE bloqueado **salvo** unlock explícito
con usuario/contraseña de operador (env local). El password nunca va a git.

F101: con unlock + scope ``binance_demo``, ``LiveOrderRouter`` enruta fills
simulados locales (nunca producción Binance).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from quantlab.core.exceptions import ValidationError

if TYPE_CHECKING:
    from quantlab.brokers.types import BrokerAck
    from quantlab.core.types.orders import OrderIntent

# Invariante de producto — default bloqueado. Unlock = corte humano (F100).
LIVE_BLOCKED: bool = True

LIVE_ROUTING_BLOCKED_MSG = (
    "ORDER ROUTING REAL / LIVE: BLOQUEADO. "
    "Requiere unlock con usuario/contraseña (QUANTLAB_LIVE_USER / "
    "QUANTLAB_LIVE_PASSWORD) vía /api/live/unlock. "
    "Sin unlock no hay connectores live."
)


def assert_live_routing_blocked() -> None:
    """Falla si no hay sesión LIVE desbloqueada por credenciales.

    Compat: sin unlock se comporta como el gate histórico (siempre bloqueado).
    Con unlock válido (F100) permite continuar el camino LIVE demo.
    """
    from quantlab.execution.live_unlock import is_live_session_unlocked
    from quantlab.infra.ops_metrics import get_ops_metrics

    get_ops_metrics().inc("live_gate.check")
    if is_live_session_unlocked():
        get_ops_metrics().inc("live_gate.unlocked_pass")
        return

    get_ops_metrics().inc("live_gate.blocked")
    raise ValidationError(LIVE_ROUTING_BLOCKED_MSG)


def require_live_unlock(*, venue_scope: str | None = None) -> None:
    """Exige unlock activo; opcionalmente acotado a un venue_scope."""
    from quantlab.execution.live_unlock import get_live_unlock_session

    session = get_live_unlock_session()
    if session is None:
        raise ValidationError(LIVE_ROUTING_BLOCKED_MSG)
    if venue_scope is None:
        return
    wanted = venue_scope.strip().lower()
    allowed = {session.venue_scope}
    if session.venue_scope == "binance_demo":
        allowed.update({"binance", "binance_demo"})
    if wanted not in allowed:
        raise ValidationError(
            f"LIVE unlock scope={session.venue_scope!r} no cubre {venue_scope!r}"
        )


class LiveOrderRouter:
    """Router LIVE post-unlock: solo ``binance_demo`` simulado (F101).

    No envía órdenes a producción. Testnet HMAC remoto queda fuera de este build.
    """

    LIVE_BLOCKED: bool = True

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        from quantlab.brokers.binance.demo_router import get_shared_demo_router
        from quantlab.execution.live_unlock import get_live_unlock_session

        assert_live_routing_blocked()
        require_live_unlock()
        session = get_live_unlock_session()
        assert session is not None
        scope = session.venue_scope
        if scope not in {"binance_demo", "binance"}:
            raise ValidationError(
                f"LiveOrderRouter F101 solo soporta binance_demo "
                f"(scope actual={scope!r})"
            )
        self._scope = scope
        self._demo = get_shared_demo_router()

    def submit(self, intent: OrderIntent) -> BrokerAck:
        require_live_unlock(venue_scope="binance_demo")
        return self._demo.submit(intent)

    def status(self) -> dict[str, Any]:
        payload = self._demo.status()
        payload["unlock_scope"] = self._scope
        payload["live_blocked_flag"] = LIVE_BLOCKED
        return payload

    def recent_fills(self, *, limit: int = 20) -> list[dict[str, Any]]:
        return self._demo.recent_fills(limit=limit)
