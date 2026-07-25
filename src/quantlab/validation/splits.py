"""Train / validation / OOS y walk-forward (Fase 10)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar


@dataclass(frozen=True, slots=True)
class SplitResult:
    train: tuple[Bar, ...]
    validation: tuple[Bar, ...]
    oos: tuple[Bar, ...]


@dataclass(frozen=True, slots=True)
class WalkForwardSplit:
    train: tuple[Bar, ...]
    test: tuple[Bar, ...]
    fold: int


def train_val_oos_split(
    bars: Sequence[Bar],
    *,
    train_frac: float = 0.6,
    val_frac: float = 0.2,
) -> SplitResult:
    """Split temporal estricto (sin shuffle). OOS = resto."""
    if not bars:
        raise ValidationError("bars vacío")
    if train_frac <= 0 or val_frac <= 0 or train_frac + val_frac >= 1:
        raise ValidationError("fracciones inválidas")
    n = len(bars)
    i_train = max(1, int(n * train_frac))
    i_val = max(i_train + 1, int(n * (train_frac + val_frac)))
    if i_val >= n:
        raise ValidationError("serie demasiado corta para OOS")
    return SplitResult(
        train=tuple(bars[:i_train]),
        validation=tuple(bars[i_train:i_val]),
        oos=tuple(bars[i_val:]),
    )


def walk_forward(
    bars: Sequence[Bar],
    *,
    train_size: int,
    test_size: int,
    step: int | None = None,
) -> tuple[WalkForwardSplit, ...]:
    if train_size < 1 or test_size < 1:
        raise ValidationError("train_size/test_size inválidos")
    step = step or test_size
    folds: list[WalkForwardSplit] = []
    start = 0
    fold = 0
    while start + train_size + test_size <= len(bars):
        tr = bars[start : start + train_size]
        te = bars[start + train_size : start + train_size + test_size]
        folds.append(WalkForwardSplit(train=tuple(tr), test=tuple(te), fold=fold))
        fold += 1
        start += step
    if not folds:
        raise ValidationError("no hay folds walk-forward")
    return tuple(folds)


def assert_no_future_overlap(train: Sequence[Bar], test: Sequence[Bar]) -> None:
    if not train or not test:
        raise ValidationError("train/test vacíos")
    last_train: datetime = train[-1].timestamp_close
    first_test: datetime = test[0].timestamp_open
    if first_test < last_train:
        raise ValidationError("leakage temporal: test solapa train")
