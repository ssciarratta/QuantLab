"""Tests Feature Transformers — Fase 5 Oficial Módulo 1."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.features import (
    ClosePriceTransformer,
    FeatureTransformer,
    Indicator,
    LogReturnTransformer,
    SimpleReturnTransformer,
    VolumeChangeTransformer,
    VolumeSMATransformer,
)
from quantlab.features.causal import causal_window


def _bars(n: int, *, start_close: int = 100) -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 5, 1, tzinfo=UTC)
    for i in range(n):
        c = Decimal(start_close + i)
        t0 = base + timedelta(minutes=i)
        out.append(
            Bar(
                instrument_id="FEAT:TEST",
                open=c,
                high=c + Decimal("1"),
                low=c - Decimal("1"),
                close=c,
                volume=Decimal(10 + i),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(minutes=1),
                timeframe="1m",
            )
        )
    return out


def test_close_price_transformer() -> None:
    bars = _bars(3)
    series = ClosePriceTransformer().transform(bars)
    assert len(series.points) == 3
    assert series.points[0].value == Decimal("100")
    assert series.points[-1].value == Decimal("102")


def test_simple_return_no_lookahead_prefix_stable() -> None:
    bars5 = _bars(5)
    bars3 = bars5[:3]
    t = SimpleReturnTransformer()
    s3 = t.transform(bars3)
    s5 = t.transform(bars5)
    assert s3.points == s5.points[: len(s3.points)]
    # r1 = 101/100 - 1 = 0.01
    assert s3.points[0].value == Decimal("0.01")


def test_log_return_positive() -> None:
    series = LogReturnTransformer().transform(_bars(3))
    assert len(series.points) == 2
    assert series.points[0].value > 0


def test_volume_change_skips_zero_prev() -> None:
    bars = _bars(3)
    # forzar volumen 0 en la primera
    b0 = bars[0]
    bars[0] = Bar(
        instrument_id=b0.instrument_id,
        open=b0.open,
        high=b0.high,
        low=b0.low,
        close=b0.close,
        volume=Decimal("0"),
        timestamp_open=b0.timestamp_open,
        timestamp_close=b0.timestamp_close,
        timeframe=b0.timeframe,
    )
    series = VolumeChangeTransformer().transform(bars)
    # primer cambio (i=1) omitido por prev=0; queda i=2
    assert len(series.points) == 1


def test_volume_sma_causal() -> None:
    bars = _bars(5)
    ind = VolumeSMATransformer(window=3)
    assert isinstance(ind, Indicator)
    assert isinstance(ind, FeatureTransformer)
    series = ind.transform(bars)
    assert series.min_lookback == 3
    assert len(series.points) == 3
    # SMA de vol 10,11,12 = 11
    assert series.points[0].value == Decimal("11")


def test_causal_window_rejects_incomplete() -> None:
    bars = _bars(2)
    with pytest.raises(ValidationError):
        causal_window(bars, 0, 2)


def test_insufficient_bars() -> None:
    with pytest.raises(ValidationError):
        SimpleReturnTransformer().transform(_bars(1))


def test_feature_point_frozen_metadata() -> None:
    series = ClosePriceTransformer().transform(_bars(1))
    with pytest.raises(AttributeError):
        series.points[0].value = Decimal("0")  # type: ignore[misc]


def test_feature_point_rejects_nan_and_infinity() -> None:
    from quantlab.features.contracts import FeaturePoint

    ts = datetime(2024, 5, 1, tzinfo=UTC)
    base = {
        "timestamp": ts,
        "instrument_id": "FEAT:TEST",
        "name": "x",
        "lookback_used": 1,
    }
    with pytest.raises(ValidationError, match="NaN ni infinito"):
        FeaturePoint(**base, value=Decimal("NaN"))
    with pytest.raises(ValidationError, match="NaN ni infinito"):
        FeaturePoint(**base, value=Decimal("Infinity"))
    with pytest.raises(ValidationError, match="NaN ni infinito"):
        FeaturePoint(**base, value=Decimal("-Infinity"))
