"""Tests FeaturePipeline — Fase 5 Oficial Módulo 2."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.features import (
    ClosePriceTransformer,
    SimpleReturnTransformer,
    VolumeSMATransformer,
)
from quantlab.features.pipeline import FeaturePipeline, build_pipeline


def _bars(n: int) -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 5, 1, tzinfo=UTC)
    for i in range(n):
        c = Decimal(100 + i)
        t0 = base + timedelta(minutes=i)
        out.append(
            Bar(
                instrument_id="FEAT:PIPE",
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


def test_build_and_run_pipeline() -> None:
    pipe = build_pipeline(
        ClosePriceTransformer(),
        SimpleReturnTransformer(),
        VolumeSMATransformer(window=3),
        name="demo",
    )
    frame = pipe.run(_bars(5))
    assert frame.pipeline_name == "demo"
    assert frame.bar_count == 5
    assert frame.min_lookback == 3
    assert set(frame.series) == {"close_price", "simple_return", "volume_sma_3"}
    assert len(frame.series["close_price"].points) == 5
    assert len(frame.series["simple_return"].points) == 4


def test_then_composes_immutably() -> None:
    base = FeaturePipeline(steps=(ClosePriceTransformer(),))
    extended = base.then(SimpleReturnTransformer())
    assert len(base.steps) == 1
    assert len(extended.steps) == 2
    frame = extended.run(_bars(3))
    assert "simple_return" in frame.series


def test_pipeline_rejects_duplicate_step_names() -> None:
    with pytest.raises(ValidationError):
        FeaturePipeline(
            steps=(ClosePriceTransformer(), ClosePriceTransformer()),
        )


def test_pipeline_no_lookahead_prefix_stable() -> None:
    pipe = build_pipeline(ClosePriceTransformer(), SimpleReturnTransformer())
    bars5 = _bars(5)
    bars3 = bars5[:3]
    f3 = pipe.run(bars3)
    f5 = pipe.run(bars5)
    assert f3.series["close_price"].points == f5.series["close_price"].points[:3]
    assert (
        f3.series["simple_return"].points
        == f5.series["simple_return"].points[: len(f3.series["simple_return"].points)]
    )


def test_empty_pipeline_rejected() -> None:
    with pytest.raises(ValidationError):
        FeaturePipeline(steps=())


def test_frame_series_mapping_frozen() -> None:
    frame = build_pipeline(ClosePriceTransformer()).run(_bars(2))
    with pytest.raises(TypeError):
        frame.series["x"] = frame.series["close_price"]  # type: ignore[index]
