"""Carga de brokers externos vía entry points (Fase 24 / Fase 87).

Grupo: ``quantlab.brokers``
Contrato v1: entry point sin argumentos que retorna ``BrokerPluginSpec``.
Legacy v0: factory callable ``(OperatingMode) -> BrokerPort`` (deprecada).
"""

from __future__ import annotations

import inspect
import warnings
from importlib.metadata import entry_points
from typing import TYPE_CHECKING, Any

from quantlab.brokers.contracts.v1 import BrokerPluginSpec
from quantlab.core.exceptions import ValidationError
from quantlab.infra.logging import get_logger

if TYPE_CHECKING:
    from quantlab.brokers.registry import BrokerRegistry

logger = get_logger(__name__)

ENTRY_POINT_GROUP = "quantlab.brokers"


class LegacyBrokerPluginWarning(UserWarning):
    """A v0 naked factory was loaded through the compatibility path."""


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
    """Registra specs v1 o factories legacy desde ``quantlab.brokers``.

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
            published = ep.load()
            spec = _load_v1_spec(published)
            if spec is not None:
                key = spec.venue_id
                factory = spec.factory
            else:
                if not callable(published):
                    logger.warning(
                        "broker_plugin_not_callable",
                        venue=name,
                        ep=str(ep),
                    )
                    continue
                key = name.strip().lower()
                if not key:
                    raise ValidationError("entry point broker legacy sin nombre de venue")
                warnings.warn(
                    f"broker plugin {key!r} usa factory legacy v0; migrar a "
                    "BrokerPluginSpec API v1",
                    LegacyBrokerPluginWarning,
                    stacklevel=2,
                )
                logger.warning(
                    "broker_plugin_legacy_v0",
                    venue=key,
                    ep=str(ep),
                )
                factory = published
            if key and registry.has_venue(key):
                logger.warning(
                    "broker_plugin_shadow_refused",
                    venue=key,
                    ep=str(ep),
                    reason="venue already registered",
                )
                continue
            registry.register(key, factory, from_plugin=True)
            loaded.append(key)
            logger.info("broker_plugin_loaded", venue=key)
        except Exception as exc:  # noqa: BLE001 — plugin externo
            logger.warning(
                "broker_plugin_load_failed",
                venue=name,
                error=str(exc),
                ep=str(ep),
            )
    return loaded


def _load_v1_spec(published: Any) -> BrokerPluginSpec | None:
    """Resolve a direct spec/provider; return ``None`` for a v0-style factory."""
    if isinstance(published, BrokerPluginSpec):
        return published
    if not callable(published):
        return None
    try:
        signature = inspect.signature(published)
    except (TypeError, ValueError):
        return None
    try:
        signature.bind()
    except TypeError:
        return None
    candidate = published()
    if not isinstance(candidate, BrokerPluginSpec):
        raise ValidationError(
            "entry point broker invocable sin argumentos debe retornar BrokerPluginSpec v1"
        )
    return candidate
