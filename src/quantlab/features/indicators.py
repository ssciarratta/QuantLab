"""Indicadores técnicos básicos causales (Fase 5 Oficial — Módulo 3)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
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
class SMACloseIndicator:
    """SMA causal del close — acumulador deslizante O(1) por barra."""

    window: int = 5
    name: str = "sma_close"
    indicator_family: str = "trend"

    def __post_init__(self) -> None:
        if self.window < 1:
            raise ValidationError("window debe ser >= 1")
        object.__setattr__(self, "name", f"sma_close_{self.window}")

    @property
    def min_lookback(self) -> int:
        return self.window

    def transform(self, bars: Sequence[Bar], *, skip_causal_check: bool = False) -> FeatureSeries:
        _ensure_causal(bars, min_lookback=self.min_lookback, skip_causal_check=skip_causal_check)
        points: list[FeaturePoint] = []
        w = self.window
        running = sum((bars[i].close for i in range(w)), Decimal("0"))
        for i in range(w - 1, len(bars)):
            if i > w - 1:
                running += bars[i].close - bars[i - w].close
            avg = running / Decimal(w)
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


@dataclass(frozen=True, slots=True)
class EMACloseIndicator:
    """EMA causal del close (semilla = primer close)."""

    window: int = 5
    name: str = "ema_close"
    indicator_family: str = "trend"

    def __post_init__(self) -> None:
        if self.window < 1:
            raise ValidationError("window debe ser >= 1")
        object.__setattr__(self, "name", f"ema_close_{self.window}")

    @property
    def min_lookback(self) -> int:
        return 1

    def transform(self, bars: Sequence[Bar], *, skip_causal_check: bool = False) -> FeatureSeries:
        _ensure_causal(bars, min_lookback=self.min_lookback, skip_causal_check=skip_causal_check)
        alpha = Decimal("2") / (Decimal(self.window) + Decimal("1"))
        points: list[FeaturePoint] = []
        ema = bars[0].close
        points.append(
            FeaturePoint(
                timestamp=bars[0].timestamp_close,
                instrument_id=bars[0].instrument_id,
                name=self.name,
                value=ema,
                lookback_used=1,
                metadata={"window": self.window, "seed": "first_close"},
            )
        )
        for i in range(1, len(bars)):
            ema = alpha * bars[i].close + (Decimal("1") - alpha) * ema
            points.append(
                FeaturePoint(
                    timestamp=bars[i].timestamp_close,
                    instrument_id=bars[i].instrument_id,
                    name=self.name,
                    value=ema,
                    lookback_used=i + 1,
                    metadata={"window": self.window},
                )
            )
        return _series(self.name, self.min_lookback, points)


@dataclass(frozen=True, slots=True)
class RSIWilderIndicator:
    """RSI estilo Wilder, causal, período `period`."""

    period: int = 14
    name: str = "rsi"
    indicator_family: str = "momentum"

    def __post_init__(self) -> None:
        if self.period < 2:
            raise ValidationError("period debe ser >= 2")
        object.__setattr__(self, "name", f"rsi_{self.period}")

    @property
    def min_lookback(self) -> int:
        return self.period + 1

    def transform(self, bars: Sequence[Bar], *, skip_causal_check: bool = False) -> FeatureSeries:
        _ensure_causal(bars, min_lookback=self.min_lookback, skip_causal_check=skip_causal_check)
        gains: list[Decimal] = []
        losses: list[Decimal] = []
        for i in range(1, len(bars)):
            delta = bars[i].close - bars[i - 1].close
            gains.append(delta if delta > 0 else Decimal("0"))
            losses.append(-delta if delta < 0 else Decimal("0"))

        avg_gain = sum(gains[: self.period], Decimal("0")) / Decimal(self.period)
        avg_loss = sum(losses[: self.period], Decimal("0")) / Decimal(self.period)
        points: list[FeaturePoint] = []

        def _rsi(ag: Decimal, al: Decimal) -> Decimal:
            if al == 0 and ag == 0:
                return Decimal("50")
            if al == 0:
                return Decimal("100")
            rs = ag / al
            return Decimal("100") - (Decimal("100") / (Decimal("1") + rs))

        first_idx = self.period
        points.append(
            FeaturePoint(
                timestamp=bars[first_idx].timestamp_close,
                instrument_id=bars[first_idx].instrument_id,
                name=self.name,
                value=_rsi(avg_gain, avg_loss),
                lookback_used=self.period + 1,
                metadata={"period": self.period, "method": "wilder"},
            )
        )
        for i in range(self.period, len(gains)):
            avg_gain = (avg_gain * (Decimal(self.period) - Decimal("1")) + gains[i]) / Decimal(
                self.period
            )
            avg_loss = (avg_loss * (Decimal(self.period) - Decimal("1")) + losses[i]) / Decimal(
                self.period
            )
            bar_idx = i + 1
            points.append(
                FeaturePoint(
                    timestamp=bars[bar_idx].timestamp_close,
                    instrument_id=bars[bar_idx].instrument_id,
                    name=self.name,
                    value=_rsi(avg_gain, avg_loss),
                    lookback_used=bar_idx + 1,
                    metadata={"period": self.period, "method": "wilder"},
                )
            )
        return _series(self.name, self.min_lookback, points)


@dataclass(frozen=True, slots=True)
class ATRIndicator:
    """Average True Range causal — SMA de True Range (no Wilder).

    Convención QuantLab (R3): ``method=sma_tr``. RSI usa Wilder; ATR usa SMA
    deslizante O(1) sobre TR. No confundir con ATR Wilder clásico.
    """

    period: int = 14
    name: str = "atr"
    indicator_family: str = "volatility"

    def __post_init__(self) -> None:
        if self.period < 1:
            raise ValidationError("period debe ser >= 1")
        object.__setattr__(self, "name", f"atr_{self.period}")

    @property
    def min_lookback(self) -> int:
        return self.period + 1

    def transform(self, bars: Sequence[Bar], *, skip_causal_check: bool = False) -> FeatureSeries:
        _ensure_causal(bars, min_lookback=self.min_lookback, skip_causal_check=skip_causal_check)
        true_ranges: list[Decimal] = []
        for i in range(1, len(bars)):
            high = bars[i].high
            low = bars[i].low
            prev_close = bars[i - 1].close
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            true_ranges.append(tr)

        points: list[FeaturePoint] = []
        p = self.period
        running = sum((true_ranges[i] for i in range(p)), Decimal("0"))
        for i in range(p - 1, len(true_ranges)):
            if i > p - 1:
                running += true_ranges[i] - true_ranges[i - p]
            atr = running / Decimal(p)
            bar_idx = i + 1
            points.append(
                FeaturePoint(
                    timestamp=bars[bar_idx].timestamp_close,
                    instrument_id=bars[bar_idx].instrument_id,
                    name=self.name,
                    value=atr,
                    lookback_used=p + 1,
                    metadata={
                        "period": p,
                        "algo": "sliding_sum_o1",
                        "method": "sma_tr",
                    },
                )
            )
        return _series(self.name, self.min_lookback, points)
