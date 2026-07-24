"""Immutable JSON-compatible types to replace Any in domain contracts.

Provides type-safe alternatives for serializable data structures
used in payloads, manifests, parameters, configuration, metadata, and results.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Union

JsonScalar = str | int | float | bool | None
"""A single JSON-compatible scalar value."""

JsonValue = Union[JsonScalar, "JsonArray", "JsonObject"]
"""Any JSON-compatible value: scalar, array, or object.

Uses Union for forward-reference compatibility with recursive types.
"""

JsonArray = tuple[JsonValue, ...]
"""An immutable sequence of JSON values (replaces list)."""

JsonObject = MappingProxyType[str, JsonValue]
"""An immutable mapping of string keys to JSON values (replaces dict)."""


def freeze_json(data: object) -> JsonValue:
    """Recursively convert mutable Python data to immutable JSON types.

    Raises TypeError for non-JSON-serializable inputs.
    """
    if data is None or isinstance(data, (str, int, float, bool)):
        return data
    if isinstance(data, (list, tuple)):
        return tuple(freeze_json(item) for item in data)
    if isinstance(data, dict):
        return MappingProxyType({str(k): freeze_json(v) for k, v in data.items()})
    raise TypeError(f"Cannot freeze non-JSON type: {type(data).__name__}")
