"""Helpers de validación compartidos para tipos de dominio."""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType
from typing import Any

from quantlab.core.exceptions import ManifestError, ValidationError

_SHA256_HEX_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_SEMVER_LIKE_RE = re.compile(r"^\d+\.\d+(\.\d+)?([+-][0-9A-Za-z.-]+)?$")


def require_non_empty_str(
    value: str | None,
    field: str,
    *,
    error_cls: type[Exception] = ValidationError,
) -> None:
    if value is None or not value.strip():
        raise error_cls(f"{field} no puede estar vacío")


def require_aware(dt: datetime, field: str) -> None:
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValidationError(f"{field} debe ser timezone-aware")


def require_positive(value: Decimal, field: str) -> None:
    if value.is_nan() or value.is_infinite():
        raise ValidationError(f"{field} no puede ser NaN ni Infinity")
    if value <= 0:
        raise ValidationError(f"{field} debe ser > 0")


def require_non_negative(value: Decimal, field: str) -> None:
    if value.is_nan() or value.is_infinite():
        raise ValidationError(f"{field} no puede ser NaN ni Infinity")
    if value < 0:
        raise ValidationError(f"{field} no puede ser negativo")


def _freeze_value(value: Any) -> Any:
    """Congela mappings anidados y convierte list/set mutables a tuplas/frozenset."""
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze_value(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_value(v) for v in value)
    if isinstance(value, tuple):
        return tuple(_freeze_value(v) for v in value)
    if isinstance(value, set):
        return frozenset(_freeze_value(v) for v in value)
    return value


def freeze_mapping(data: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    """Copia profunda inmutable de un mapping (R9: nested dict/list no mutables)."""
    return MappingProxyType({str(k): _freeze_value(v) for k, v in data.items()})


def require_checksum(value: str, field: str = "checksum") -> None:
    """Exige checksum SHA-256 (exactamente 64 caracteres hexadecimales)."""
    require_non_empty_str(value, field, error_cls=ManifestError)
    if not _SHA256_HEX_RE.fullmatch(value.strip()):
        raise ManifestError(f"{field} debe ser SHA-256 (64 caracteres hexadecimales)")


def require_schema_version(value: str, field: str = "schema_version") -> None:
    require_non_empty_str(value, field, error_cls=ManifestError)
    if not _SEMVER_LIKE_RE.fullmatch(value.strip()):
        raise ManifestError(f"{field} debe ser semver-like (ej. 1.0 o 1.0.0)")
