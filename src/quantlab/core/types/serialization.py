"""Utilidades de serialización para tipos de dominio."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from types import MappingProxyType
from typing import Any


def to_jsonable(value: Any) -> Any:
    """Convierte valores de dominio a estructuras JSON-serializables (determinista)."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        # str(Decimal) preserva escala/notación exacta; evita ambigüedad de format(..., "f")
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: to_jsonable(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, MappingProxyType) or (
        isinstance(value, Mapping) and not isinstance(value, (str, bytes))
    ):
        return {str(k): to_jsonable(value[k]) for k in sorted(value, key=str)}
    if isinstance(value, dict):
        return {str(k): to_jsonable(value[k]) for k in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    return value


def dataclass_to_dict(instance: object) -> dict[str, Any]:
    """Serializa un dataclass a dict JSON-compatible."""
    if not is_dataclass(instance) or isinstance(instance, type):
        msg = "Se esperaba una instancia de dataclass"
        raise TypeError(msg)
    result = to_jsonable(instance)
    if not isinstance(result, dict):
        msg = "La serialización no produjo un dict"
        raise TypeError(msg)
    return result
