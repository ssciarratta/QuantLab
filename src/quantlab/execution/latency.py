"""Modelos de latencia bar-based."""

from __future__ import annotations

from collections.abc import Sequence
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
        bar_times: Sequence[datetime] | None = None,
    ) -> LatencyDecision:
        _ = submit_time
        _ = bar_times
        if submit_index < 0 or submit_index >= series_length:
            return LatencyDecision(False, None, "submit_out_of_range")
        return LatencyDecision(True, submit_index, "same_bar")


@dataclass(frozen=True, slots=True)
class FixedLatencyModel:
    """Latencia fija en número de barras y/o timedelta mínimo (wall-clock).

    La barra efectiva es al menos ``submit_index + bars_delay``.
    Si ``min_delay > 0``, se avanza hasta la primera barra cuyo
    ``bar_times[i] - submit_time >= min_delay`` (requiere ``bar_times``).
    """

    bars_delay: int = 0
    min_delay: timedelta = timedelta(0)
    model_id: str = "latency.fixed.v1"

    def __post_init__(self) -> None:
        if self.bars_delay < 0:
            raise ValidationError("bars_delay no puede ser negativo")
        if self.min_delay.total_seconds() < 0:
            raise ValidationError("min_delay no puede ser negativo")

    def resolve(
        self,
        *,
        submit_index: int,
        submit_time: datetime,
        series_length: int,
        bar_times: Sequence[datetime] | None = None,
    ) -> LatencyDecision:
        if submit_index < 0 or submit_index >= series_length:
            return LatencyDecision(False, None, "submit_out_of_range")

        effective = submit_index + self.bars_delay
        if effective >= series_length:
            return LatencyDecision(False, None, "latency_beyond_series")

        if self.min_delay.total_seconds() <= 0:
            return LatencyDecision(True, effective, f"delayed_{self.bars_delay}_bars")

        if bar_times is None:
            raise ValidationError(
                "min_delay wall-clock requiere bar_times (timestamps de cierre por step)"
            )
        if len(bar_times) < series_length:
            raise ValidationError(
                f"bar_times insuficiente: len={len(bar_times)} < series_length={series_length}"
            )

        for idx in range(effective, series_length):
            if bar_times[idx] - submit_time >= self.min_delay:
                return LatencyDecision(
                    True,
                    idx,
                    f"min_delay_{int(self.min_delay.total_seconds())}s_at_{idx}",
                )

        return LatencyDecision(False, None, "min_delay_beyond_series")
