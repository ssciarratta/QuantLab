"""Tests Feature Store — Fase 5 Oficial M3."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.features import (
    ClosePriceTransformer,
    SimpleReturnTransformer,
    build_pipeline,
)
from quantlab.features.store import FeatureStore


def _bars(n: int) -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 7, 1, tzinfo=UTC)
    for i in range(n):
        c = Decimal(100 + i)
        t0 = base + timedelta(minutes=i)
        out.append(
            Bar(
                instrument_id="FEAT:STORE",
                open=c,
                high=c + Decimal("1"),
                low=c - Decimal("1"),
                close=c,
                volume=Decimal(20 + i),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(minutes=1),
                timeframe="1m",
            )
        )
    return out


def test_feature_store_put_get_roundtrip(tmp_path: Path) -> None:
    frame = build_pipeline(
        ClosePriceTransformer(),
        SimpleReturnTransformer(),
        name="pipe_v1",
    ).run(_bars(4))
    store = FeatureStore(tmp_path / "fstore")
    ref = store.put(frame, version="v1")
    assert ref.checksum
    assert Path(ref.path).exists()
    loaded = store.get("FEAT:STORE", "pipe_v1", "v1")
    assert loaded.instrument_id == frame.instrument_id
    assert loaded.series["close_price"].points == frame.series["close_price"].points
    assert store.list_versions("FEAT:STORE", "pipe_v1") == ("v1",)


def test_feature_store_missing_raises(tmp_path: Path) -> None:
    store = FeatureStore(tmp_path / "fstore")
    with pytest.raises(ValidationError):
        store.get("X", "Y", "v9")


def test_feature_store_versions_sorted(tmp_path: Path) -> None:
    frame = build_pipeline(ClosePriceTransformer(), name="p").run(_bars(2))
    store = FeatureStore(tmp_path / "fstore")
    store.put(frame, version="v2")
    store.put(frame, version="v1")
    assert store.list_versions("FEAT:STORE", "p") == ("v1", "v2")
