"""Protocolo desacoplado: el dominio Alpha no importa torch/HF/numpy directamente."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from quantlab.research.alpha.kronos.errors import KronosSkipReason


@dataclass(frozen=True, slots=True)
class TrajectoryBatch:
    """Trayectorias OHLCV. Cada serie: K listas de longitud H."""

    opens: tuple[tuple[float, ...], ...]
    highs: tuple[tuple[float, ...], ...]
    lows: tuple[tuple[float, ...], ...]
    closes: tuple[tuple[float, ...], ...]
    volumes: tuple[tuple[float, ...], ...] | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def n_samples(self) -> int:
        return len(self.closes)

    @property
    def horizon(self) -> int:
        return len(self.closes[0]) if self.closes else 0


@dataclass(frozen=True, slots=True)
class ForecastRequest:
    instrument_id: str
    lookback_opens: tuple[float, ...]
    lookback_highs: tuple[float, ...]
    lookback_lows: tuple[float, ...]
    lookback_closes: tuple[float, ...]
    lookback_volumes: tuple[float, ...]
    lookback_amounts: tuple[float, ...]
    timestamps_ns: tuple[int, ...]
    pred_len: int
    sample_count: int
    temperature: float
    top_p: float
    seed: int


@dataclass(frozen=True, slots=True)
class ForecastResult:
    ok: bool
    trajectories: TrajectoryBatch | None
    reason: KronosSkipReason | None = None
    detail: str = ""
    inference_ms: float = 0.0
    device: str = ""
    model_revision: str = ""


@runtime_checkable
class ForecastEngine(Protocol):
    def forecast(self, request: ForecastRequest) -> ForecastResult: ...

    def health(self) -> dict[str, Any]: ...


class NullForecastEngine:
    """Motor nulo: Kronos no instalado / deshabilitado. Nunca inventa números."""

    def __init__(self, reason: KronosSkipReason = KronosSkipReason.DEPS_MISSING) -> None:
        self._reason = reason

    def forecast(self, request: ForecastRequest) -> ForecastResult:
        _ = request
        return ForecastResult(
            ok=False,
            trajectories=None,
            reason=self._reason,
            detail="Kronos no disponible; ranking tradicional intacto",
        )

    def health(self) -> dict[str, Any]:
        return {"ok": False, "reason": self._reason.value, "engine": "null"}


__all__ = [
    "ForecastEngine",
    "ForecastRequest",
    "ForecastResult",
    "NullForecastEngine",
    "TrajectoryBatch",
]
