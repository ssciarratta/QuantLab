"""Gate irrenunciable: order routing LIVE (TD-10 / F100 credential gate).

``LIVE_BLOCKED=True`` significa: LIVE bloqueado **salvo** unlock explícito
con usuario/contraseña de operador (env local). El password nunca va a git.
"""

from __future__ import annotations

from quantlab.core.exceptions import ValidationError

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
    """Stub: construcción solo tras unlock; aún sin routing venue real (F100)."""

    LIVE_BLOCKED: bool = True

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        assert_live_routing_blocked()
        require_live_unlock()
        raise ValidationError(
            "LiveOrderRouter: unlock OK, pero el routing venue real aún no está "
            "habilitado en este build (siguiente fase Binance demo). "
            "No hay envío de órdenes."
        )
