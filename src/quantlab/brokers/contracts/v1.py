"""Versioned public contract for cooperative external broker plugins."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from quantlab.brokers.port import BrokerPort
from quantlab.core.exceptions import ValidationError

BROKER_PLUGIN_API_VERSION = "1"
BROKER_PLUGIN_CAPABILITIES = frozenset({"market_data", "account_read"})
_VENUE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")

BrokerPluginFactory = Callable[..., BrokerPort]


@dataclass(frozen=True, slots=True)
class BrokerPluginSpec:
    """Metadata and factory published by a Broker Plugin Contract v1 entry point."""

    api_version: str
    venue_id: str
    capabilities: frozenset[str]
    factory: BrokerPluginFactory

    def __post_init__(self) -> None:
        if self.api_version != BROKER_PLUGIN_API_VERSION:
            raise ValidationError(
                "broker plugin api_version inválida: "
                f"{self.api_version!r}; esperada {BROKER_PLUGIN_API_VERSION!r}"
            )
        if not isinstance(self.venue_id, str) or not _VENUE_ID_RE.fullmatch(self.venue_id):
            raise ValidationError(
                "broker plugin venue_id inválido: usar 1–64 caracteres [a-z0-9_-], "
                "iniciando con letra minúscula o dígito"
            )
        capabilities = _normalize_capabilities(self.capabilities)
        if not capabilities:
            raise ValidationError("broker plugin requiere al menos una capability read-only")
        unsupported = capabilities - BROKER_PLUGIN_CAPABILITIES
        if unsupported:
            names = ", ".join(sorted(unsupported))
            raise ValidationError(
                f"broker plugin capabilities no permitidas en v1: {names}; ejecución prohibida"
            )
        if not callable(self.factory):
            raise ValidationError("broker plugin factory debe ser callable")
        object.__setattr__(self, "capabilities", capabilities)


def _normalize_capabilities(value: Any) -> frozenset[str]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        raise ValidationError("broker plugin capabilities debe ser una colección de strings")
    try:
        capabilities = frozenset(value)
    except TypeError as exc:
        raise ValidationError(
            "broker plugin capabilities debe contener valores hashable"
        ) from exc
    if any(not isinstance(item, str) for item in capabilities):
        raise ValidationError("broker plugin capabilities debe contener sólo strings")
    return capabilities
