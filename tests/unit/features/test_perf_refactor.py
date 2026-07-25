"""Tests de optimizaciones F5 Oficial (sliding O(1), universe, store cache)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.features import (
    ATRIndicator,
    ClosePriceTransformer,
    SimpleReturnTransformer,
    SMACloseIndicator,
    VolumeSMATransformer,
    build_pipeline,
)
from quantlab.features.contracts import FeaturePoint
from quantlab.features.serialization import feature_point_to_dict
from quantlab.features.store import FeatureStore


def _bars(n: int, instrument_id: str = "FEAT:OPT") -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 8, 1, tzinfo=UTC)
    for i in range(n):
        c = Decimal(100 + i)
        t0 = base + timedelta(minutes=i)
        out.append(
            Bar(
                instrument_id=instrument_id,
                open=c,
                high=c + Decimal("1"),
                low=c - Decimal("1"),
                close=c,
                volume=Decimal(10 + i * 2),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(minutes=1),
                timeframe="1m",
            )
        )
    return out


def test_sliding_sma_matches_naive_values() -> None:
    bars = _bars(8)
    series = SMACloseIndicator(window=3).transform(bars)
    # valores esperados por media simple
    expected = [
        (Decimal("100") + Decimal("101") + Decimal("102")) / 3,
        (Decimal("101") + Decimal("102") + Decimal("103")) / 3,
        (Decimal("102") + Decimal("103") + Decimal("104")) / 3,
    ]
    assert series.points[0].value == expected[0]
    assert series.points[1].value == expected[1]
    assert series.points[2].value == expected[2]
    assert series.points[0].metadata is not None
    assert series.points[0].metadata.get("algo") == "sliding_sum_o1"


def test_volume_sma_sliding_and_atr_algo_tag() -> None:
    bars = _bars(6)
    vol = VolumeSMATransformer(window=3).transform(bars)
    assert vol.points[0].value == (Decimal("10") + Decimal("12") + Decimal("14")) / 3
    atr = ATRIndicator(period=3).transform(bars)
    assert atr.points
    assert atr.points[0].metadata is not None
    assert atr.points[0].metadata.get("algo") == "sliding_sum_o1"


def test_run_universe_multi_instrument() -> None:
    pipe = build_pipeline(ClosePriceTransformer(), SimpleReturnTransformer(), name="uni")
    universe = {
        "A": _bars(4, "A"),
        "B": _bars(4, "B"),
    }
    frames = pipe.run_universe(universe)
    assert set(frames) == {"A", "B"}
    assert frames["A"].instrument_id == "A"
    assert frames["B"].series["close_price"].points[0].value == Decimal("100")


def test_run_universe_key_mismatch() -> None:
    pipe = build_pipeline(ClosePriceTransformer())
    with pytest.raises(ValidationError):
        pipe.run_universe({"WRONG": _bars(2, "A")})


def test_feature_store_cache_hits(tmp_path: Path) -> None:
    frame = build_pipeline(ClosePriceTransformer(), name="c").run(_bars(3))
    store = FeatureStore(tmp_path / "fs")
    ref = store.put(frame, version="v1")
    store.clear_cache()
    first = store.get(frame.instrument_id, "c", "v1")
    Path(ref.path).unlink()
    second = store.get(frame.instrument_id, "c", "v1")
    assert first.series["close_price"].points == second.series["close_price"].points


def test_feature_point_to_dict_uses_str_decimal() -> None:
    ts = datetime(2024, 1, 1, tzinfo=UTC)
    point = FeaturePoint(
        timestamp=ts,
        instrument_id="X",
        name="n",
        value=Decimal("1.100"),
        lookback_used=1,
    )
    assert feature_point_to_dict(point)["value"] == "1.100"
