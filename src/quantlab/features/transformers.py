"""Feature transformers de precio, retornos y volumen (sin lookahead)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from math import log

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.core.types.validation import require_non_negative
from quantlab.features.causal import assert_bars_causal_ready
from quantlab.features.contracts import FEATURES_SCHEMA_VERSION, FeaturePoint, FeatureSeries


def _series(name: str, min_lookback: int, points: list[FeaturePoint]) -> FeatureSeries:
    return FeatureSeries(
        name=name,
        schema_version=FEATURES_SCHEMA_VERSION,
        points=tuple(points),
        min_lookback=min_lookback,
    )


def _ensure_causal(bars: Sequence[Bar], *, min_lookback: int, skip_causal_check: bool) -> None:
    if not skip_causal_check:
        assert_bars_causal_ready(bars, min_lookback=min_lookback)


@dataclass(frozen=True, slots=True)
class ClosePriceTransformer:
    """Precio de cierre en cada barra (lookback=1)."""

    name: str = "close_price"
    min_lookback: int = 1

    def transform(self, bars: Sequence[Bar], *, skip_causal_check: bool = False) -> FeatureSeries:
        _ensure_causal(bars, min_lookback=self.min_lookback, skip_causal_check=skip_causal_check)
        points = [
            FeaturePoint(
                timestamp=bar.timestamp_close,
                instrument_id=bar.instrument_id,
                name=self.name,
                value=bar.close,
                lookback_used=1,
            )
            for bar in bars
        ]
        return _series(self.name, self.min_lookback, points)


@dataclass(frozen=True, slots=True)
class SimpleReturnTransformer:
    """Retorno simple r_t = close_t / close_{t-1} - 1."""

    name: str = "simple_return"
    min_lookback: int = 2

    def transform(self, bars: Sequence[Bar], *, skip_causal_check: bool = False) -> FeatureSeries:
        _ensure_causal(bars, min_lookback=self.min_lookback, skip_causal_check=skip_causal_check)
        points: list[FeaturePoint] = []
        for i in range(1, len(bars)):
            prev = bars[i - 1].close
            cur = bars[i].close
            if prev <= 0:
                raise ValidationError("close previo debe ser > 0")
            value = (cur / prev) - Decimal("1")
            points.append(
                FeaturePoint(
                    timestamp=bars[i].timestamp_close,
                    instrument_id=bars[i].instrument_id,
                    name=self.name,
                    value=value,
                    lookback_used=2,
                )
            )
        return _series(self.name, self.min_lookback, points)


@dataclass(frozen=True, slots=True)
class LogReturnTransformer:
    """Retorno logarítmico ln(close_t / close_{t-1})."""

    name: str = "log_return"
    min_lookback: int = 2

    def transform(self, bars: Sequence[Bar], *, skip_causal_check: bool = False) -> FeatureSeries:
        _ensure_causal(bars, min_lookback=self.min_lookback, skip_causal_check=skip_causal_check)
        points: list[FeaturePoint] = []
        for i in range(1, len(bars)):
            prev = bars[i - 1].close
            cur = bars[i].close
            if prev <= 0 or cur <= 0:
                raise ValidationError("closes deben ser > 0 para log-return")
            ratio = float(cur / prev)
            value = Decimal(str(log(ratio)))
            points.append(
                FeaturePoint(
                    timestamp=bars[i].timestamp_close,
                    instrument_id=bars[i].instrument_id,
                    name=self.name,
                    value=value,
                    lookback_used=2,
                    metadata={"method": "math.log"},
                )
            )
        return _series(self.name, self.min_lookback, points)


@dataclass(frozen=True, slots=True)
class VolumeChangeTransformer:
    """Cambio relativo de volumen v_t / v_{t-1} - 1."""

    name: str = "volume_change"
    min_lookback: int = 2

    def transform(self, bars: Sequence[Bar], *, skip_causal_check: bool = False) -> FeatureSeries:
        _ensure_causal(bars, min_lookback=self.min_lookback, skip_causal_check=skip_causal_check)
        points: list[FeaturePoint] = []
        for i in range(1, len(bars)):
            prev = bars[i - 1].volume
            cur = bars[i].volume
            if prev <= 0:
                continue
            value = (cur / prev) - Decimal("1")
            points.append(
                FeaturePoint(
                    timestamp=bars[i].timestamp_close,
                    instrument_id=bars[i].instrument_id,
                    name=self.name,
                    value=value,
                    lookback_used=2,
                )
            )
        return _series(self.name, self.min_lookback, points)


@dataclass(frozen=True, slots=True)
class VolumeSMATransformer:
    """SMA causal de volumen — acumulador deslizante O(1) por barra."""

    window: int = 3
    name: str = "volume_sma"
    indicator_family: str = "volume"

    def __post_init__(self) -> None:
        if self.window < 1:
            raise ValidationError("window debe ser >= 1")
        object.__setattr__(self, "name", f"volume_sma_{self.window}")

    @property
    def min_lookback(self) -> int:
        return self.window

    def transform(self, bars: Sequence[Bar], *, skip_causal_check: bool = False) -> FeatureSeries:
        _ensure_causal(bars, min_lookback=self.min_lookback, skip_causal_check=skip_causal_check)
        points: list[FeaturePoint] = []
        w = self.window
        running = sum((bars[i].volume for i in range(w)), Decimal("0"))
        for i in range(w - 1, len(bars)):
            if i > w - 1:
                running += bars[i].volume - bars[i - w].volume
            avg = running / Decimal(w)
            require_non_negative(avg, "volume_sma")
            points.append(
                FeaturePoint(
                    timestamp=bars[i].timestamp_close,
                    instrument_id=bars[i].instrument_id,
                    name=self.name,
                    value=avg,
                    lookback_used=w,
                    metadata={"window": w, "algo": "sliding_sum_o1"},
                )
            )
        return _series(self.name, self.min_lookback, points)
