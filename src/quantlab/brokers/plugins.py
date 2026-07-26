"""Carga de brokers externos vía entry points (Fase 24 / DEC-067).

Grupo: ``quantlab.brokers``
Cada entry point: callable ``(OperatingMode) -> BrokerPort`` (opts kwargs opcionales).
"""

from __future__ import annotations

from importlib.metadata import entry_points
from typing import TYPE_CHECKING, Any

from quantlab.infra.logging import get_logger

if TYPE_CHECKING:
    from quantlab.brokers.registry import BrokerRegistry

logger = get_logger(__name__)

ENTRY_POINT_GROUP = "quantlab.brokers"


def _iter_broker_entry_points() -> list[Any]:
    """Compatible con importlib.metadata 3.10+ (select) y fallback."""
    eps: Any
    try:
        eps = entry_points(group=ENTRY_POINT_GROUP)
    except TypeError:
        # API legacy: EntryPoints dict-like / select
        all_eps = entry_points()
        select = getattr(all_eps, "select", None)
        if callable(select):
            eps = select(group=ENTRY_POINT_GROUP)
        else:
            getter = getattr(all_eps, "get", None)
            eps = getter(ENTRY_POINT_GROUP, ()) if callable(getter) else ()
    return list(eps)


def load_entry_point_brokers(registry: BrokerRegistry) -> list[str]:
    """Registra factories desde entry points ``quantlab.brokers``.

    Fallas de carga: warning structlog, **no** crash.
    Retorna lista de venue_ids cargados ok.
    """
    loaded: list[str] = []
    try:
        eps = _iter_broker_entry_points()
    except Exception as exc:  # noqa: BLE001 — frontera entry_points
        logger.warning(
            "broker_plugins_enumerate_failed",
            group=ENTRY_POINT_GROUP,
            error=str(exc),
        )
        return loaded

    for ep in eps:
        name = getattr(ep, "name", None) or ""
        try:
            factory = ep.load()
            if not callable(factory):
                logger.warning(
                    "broker_plugin_not_callable",
                    venue=name,
                    ep=str(ep),
                )
                continue
            registry.register(name, factory, from_plugin=True)
            loaded.append(name.strip().lower())
            logger.info("broker_plugin_loaded", venue=name.strip().lower())
        except Exception as exc:  # noqa: BLE001 — plugin externo
            logger.warning(
                "broker_plugin_load_failed",
                venue=name,
                error=str(exc),
                ep=str(ep),
            )
    return loaded
