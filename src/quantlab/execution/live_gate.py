"""Gate irrenunciable: order routing LIVE bloqueado (TD-10)."""

from __future__ import annotations

from quantlab.core.exceptions import ValidationError

# Invariante de producto — no cambiar a False sin decisión explícita.
LIVE_BLOCKED: bool = True

LIVE_ROUTING_BLOCKED_MSG = (
    "ORDER ROUTING REAL / LIVE A3: BLOQUEADO por diseño. No implementar ni invocar conectores live."
)


def assert_live_routing_blocked() -> None:
    """Siempre falla — contrato de producto hasta decisión explícita."""
    from quantlab.infra.ops_metrics import get_ops_metrics

    get_ops_metrics().inc("live_gate.blocked")
    if LIVE_BLOCKED:
        raise ValidationError(LIVE_ROUTING_BLOCKED_MSG)
    raise ValidationError(LIVE_ROUTING_BLOCKED_MSG)


class LiveOrderRouter:
    """Stub intencional: cualquier construcción es error."""

    LIVE_BLOCKED: bool = True

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        assert_live_routing_blocked()
