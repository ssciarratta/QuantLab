"""Modelos de latencia bar-based."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from quantlab.core.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class LatencyDecision:
    """Resultado de resolver latencia contra una serie de barras."""

    executable: bool
    effective_index: int | None
    reason: str


@dataclass(frozen=True, slots=True)
class ZeroLatencyModel:
    """Sin demora — misma barra (compat Fase 4)."""

    model_id: str = "latency.zero.v1"

    def resolve(
        self,
        *,
        submit_index: int,
        submit_time: datetime,
        series_length: int,
    ) -> LatencyDecision:
        _ = submit_time
        if submit_index < 0 or submit_index >= series_length:
            return LatencyDecision(False, None, "submit_out_of_range")
        return LatencyDecision(True, submit_index, "same_bar")


@dataclass(frozen=True, slots=True)
class FixedLatencyModel:
    """Latencia fija en número de barras y/o timedelta mínimo.

    La barra efectiva es submit_index + bars_delay.
    Si además se define `min_delay`, se exige que el wall-clock de la barra
    efectiva (aproximado por índice) respete el delay — en series regulares
    de 1 barra de barra, `bars_delay` es la fuente primaria.
    """

    bars_delay: int = 0
    min_delay: timedelta = timedelta(0)
    model_id: str = "latency.fixed.v1"

    def __post_init__(self) -> None:
        if self.bars_delay < 0:
            raise ValidationError("bars_delay no puede ser negativo")
        if self.min_delay.total_seconds() < 0:
            raise ValidationError("min_delay no puede ser negativo")
        # Wall-clock min_delay no está implementado (resolve no recibe timestamps de barra).
        if self.min_delay.total_seconds() > 0:
            raise ValidationError("min_delay wall-clock no implementado; usar solo bars_delay")

    def resolve(
        self,
        *,
        submit_index: int,
        submit_time: datetime,
        series_length: int,
    ) -> LatencyDecision:
        _ = submit_time
        if submit_index < 0 or submit_index >= series_length:
            return LatencyDecision(False, None, "submit_out_of_range")
        effective = submit_index + self.bars_delay
        if effective >= series_length:
            return LatencyDecision(False, None, "latency_beyond_series")
        return LatencyDecision(True, effective, f"delayed_{self.bars_delay}_bars")
