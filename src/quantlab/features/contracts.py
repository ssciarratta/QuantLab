"""Contratos inmutables de features e indicadores (Fase 5 Oficial — M1)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol, runtime_checkable

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.core.types.validation import (
    freeze_mapping,
    require_aware,
    require_non_empty_str,
)

FEATURES_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True, slots=True)
class FeaturePoint:
    """Valor de una feature en un timestamp (sin lookahead)."""

    timestamp: datetime
    instrument_id: str
    name: str
    value: Decimal
    lookback_used: int
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        require_aware(self.timestamp, "timestamp")
        require_non_empty_str(self.instrument_id, "instrument_id")
        require_non_empty_str(self.name, "name")
        if self.lookback_used < 1:
            raise ValidationError("lookback_used debe ser >= 1")
        if self.value.is_nan() or self.value.is_infinite():
            raise ValidationError("FeaturePoint value no puede ser NaN ni infinito")
        if self.metadata is not None:
            object.__setattr__(self, "metadata", freeze_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class FeatureSeries:
    """Serie inmutable de puntos de una feature."""

    name: str
    schema_version: str
    points: tuple[FeaturePoint, ...]
    min_lookback: int

    def __post_init__(self) -> None:
        require_non_empty_str(self.name, "name")
        require_non_empty_str(self.schema_version, "schema_version")
        if self.min_lookback < 1:
            raise ValidationError("min_lookback debe ser >= 1")
        for point in self.points:
            if point.name != self.name:
                raise ValidationError("FeaturePoint.name debe coincidir con FeatureSeries.name")


@runtime_checkable
class FeatureTransformer(Protocol):
    """Transforma barras en una FeatureSeries sin usar información futura."""

    @property
    def name(self) -> str:
        """Identificador estable de la feature."""
        ...

    @property
    def min_lookback(self) -> int:
        """Barras mínimas (pasado + presente) requeridas para el primer valor."""
        ...

    def transform(self, bars: Sequence[Bar], *, skip_causal_check: bool = False) -> FeatureSeries:
        """Calcula la serie. En el índice i solo puede leer bars[0..i]."""
        ...


@runtime_checkable
class Indicator(Protocol):
    """Indicador técnico: especialización semántica de FeatureTransformer."""

    @property
    def name(self) -> str: ...

    @property
    def min_lookback(self) -> int: ...

    @property
    def indicator_family(self) -> str:
        """Familia (p.ej. momentum, volume, price)."""
        ...

    def transform(
        self, bars: Sequence[Bar], *, skip_causal_check: bool = False
    ) -> FeatureSeries: ...


@dataclass(frozen=True, slots=True)
class FeatureFrame:
    """Salida inmutable de un pipeline: varias series alineadas a un instrumento."""

    instrument_id: str
    schema_version: str
    series: Mapping[str, FeatureSeries]
    min_lookback: int
    bar_count: int
    pipeline_name: str

    def __post_init__(self) -> None:
        require_non_empty_str(self.instrument_id, "instrument_id")
        require_non_empty_str(self.schema_version, "schema_version")
        require_non_empty_str(self.pipeline_name, "pipeline_name")
        if self.min_lookback < 1:
            raise ValidationError("min_lookback debe ser >= 1")
        if self.bar_count < 0:
            raise ValidationError("bar_count no puede ser negativo")
        object.__setattr__(self, "series", freeze_mapping(dict(self.series)))
        for name, feat in self.series.items():
            if name != feat.name:
                raise ValidationError("clave de series debe coincidir con FeatureSeries.name")
            if feat.schema_version != self.schema_version:
                raise ValidationError("schema_version inconsistente en Frame vs Series")
