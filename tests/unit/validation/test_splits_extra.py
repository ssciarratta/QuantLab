"""Cobertura extra: bordes de train_val_oos_split, walk_forward y overlap."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.validation.splits import (
    assert_no_future_overlap,
    train_val_oos_split,
    walk_forward,
)


def _bars(n: int) -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 9, 1, tzinfo=UTC)
    for i in range(n):
        c = Decimal(50 + i)
        t0 = base + timedelta(minutes=i)
        out.append(
            Bar(
                instrument_id="SPLIT:X",
                open=c,
                high=c + Decimal("1"),
                low=c - Decimal("1"),
                close=c,
                volume=Decimal("10"),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(minutes=1),
                timeframe="1m",
            )
        )
    return out


def test_train_val_oos_rejects_empty() -> None:
    with pytest.raises(ValidationError, match="bars vacío"):
        train_val_oos_split([])


def test_train_val_oos_rejects_non_positive_train_frac() -> None:
    with pytest.raises(ValidationError, match="fracciones inválidas"):
        train_val_oos_split(_bars(20), train_frac=0.0, val_frac=0.2)


def test_train_val_oos_rejects_non_positive_val_frac() -> None:
    with pytest.raises(ValidationError, match="fracciones inválidas"):
        train_val_oos_split(_bars(20), train_frac=0.6, val_frac=0.0)


def test_train_val_oos_rejects_fracs_sum_ge_one() -> None:
    with pytest.raises(ValidationError, match="fracciones inválidas"):
        train_val_oos_split(_bars(20), train_frac=0.7, val_frac=0.3)


def test_train_val_oos_rejects_too_short_for_oos() -> None:
    # n=2 → i_train=1, i_val=max(2, 1)=2 → i_val >= n
    with pytest.raises(ValidationError, match="serie demasiado corta"):
        train_val_oos_split(_bars(2), train_frac=0.6, val_frac=0.2)


def test_train_val_oos_partitions_cover_all_and_order() -> None:
    bars = _bars(10)
    split = train_val_oos_split(bars, train_frac=0.5, val_frac=0.2)
    assert len(split.train) + len(split.validation) + len(split.oos) == 10
    assert split.train == tuple(bars[: len(split.train)])
    assert split.validation[0] is bars[len(split.train)]
    assert split.oos[-1] is bars[-1]
    assert split.train[-1].timestamp_close < split.validation[0].timestamp_close
    assert split.validation[-1].timestamp_close < split.oos[0].timestamp_close


def test_train_val_oos_ensures_min_one_per_segment() -> None:
    # Con n=5 y fracciones chicas, max(1,...) fuerza al menos 1 train y 1 val
    split = train_val_oos_split(_bars(5), train_frac=0.1, val_frac=0.1)
    assert len(split.train) >= 1
    assert len(split.validation) >= 1
    assert len(split.oos) >= 1


def test_walk_forward_rejects_invalid_sizes() -> None:
    bars = _bars(20)
    with pytest.raises(ValidationError, match="train_size/test_size inválidos"):
        walk_forward(bars, train_size=0, test_size=5)
    with pytest.raises(ValidationError, match="train_size/test_size inválidos"):
        walk_forward(bars, train_size=5, test_size=0)


def test_walk_forward_rejects_no_folds() -> None:
    with pytest.raises(ValidationError, match="no hay folds"):
        walk_forward(_bars(5), train_size=4, test_size=2)


def test_walk_forward_default_step_equals_test_size() -> None:
    bars = _bars(30)
    folds = walk_forward(bars, train_size=10, test_size=5)
    assert len(folds) >= 2
    assert folds[0].fold == 0
    assert folds[1].fold == 1
    # step por defecto = test_size → segundo fold arranca en start=5
    assert folds[1].train[0] is bars[5]
    assert len(folds[0].train) == 10
    assert len(folds[0].test) == 5


def test_walk_forward_custom_step_and_no_overlap_inside_fold() -> None:
    bars = _bars(40)
    folds = walk_forward(bars, train_size=10, test_size=5, step=10)
    assert len(folds) >= 2
    for f in folds:
        assert f.train[-1].timestamp_close < f.test[0].timestamp_close
        assert_no_future_overlap(f.train, f.test)


def test_assert_no_future_overlap_rejects_empty_sides() -> None:
    bars = _bars(3)
    with pytest.raises(ValidationError, match="train/test vacíos"):
        assert_no_future_overlap([], bars)
    with pytest.raises(ValidationError, match="train/test vacíos"):
        assert_no_future_overlap(bars, [])


def test_assert_no_future_overlap_detects_leakage() -> None:
    bars = _bars(4)
    # test que empieza antes del close del último train
    with pytest.raises(ValidationError, match="leakage temporal"):
        assert_no_future_overlap(bars[:3], bars[1:3])


def test_assert_no_future_overlap_allows_touching_boundary() -> None:
    bars = _bars(4)
    # first_test.timestamp_open == last_train.timestamp_close → no leakage (<)
    train = bars[:2]
    test = bars[2:]
    assert test[0].timestamp_open == train[-1].timestamp_close
    assert_no_future_overlap(train, test)
