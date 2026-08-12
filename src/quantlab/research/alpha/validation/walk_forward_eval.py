"""Evaluación walk-forward con embargo para señales pairwise."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from quantlab.core.types.market import Bar
from quantlab.validation.splits import walk_forward


@dataclass(frozen=True, slots=True)
class PurgedWalkForwardFold:
    train: tuple[Bar, ...]
    test: tuple[Bar, ...]
    fold: int
    embargo_bars: int


def walk_forward_with_embargo(
    bars: Sequence[Bar],
    *,
    train_size: int,
    test_size: int,
    embargo_bars: int,
    step: int | None = None,
) -> tuple[PurgedWalkForwardFold, ...]:
    """Walk-forward rolling con embargo post-train."""
    base = walk_forward(bars, train_size=train_size, test_size=test_size, step=step)
    out: list[PurgedWalkForwardFold] = []
    for fold in base:
        tr = fold.train
        te = fold.test
        if embargo_bars > 0 and len(tr) > embargo_bars:
            tr = tr[:-embargo_bars]
        if not tr or not te:
            continue
        if tr[-1].timestamp_close >= te[0].timestamp_open:
            continue
        out.append(
            PurgedWalkForwardFold(
                train=tr,
                test=te,
                fold=fold.fold,
                embargo_bars=embargo_bars,
            )
        )
    return tuple(out)


def split_bars_train_test(
    bars: Sequence[Bar],
    *,
    train_fraction: float = 0.70,
    embargo_bars: int = 0,
) -> tuple[tuple[Bar, ...], tuple[Bar, ...]]:
    n = len(bars)
    cut = int(n * train_fraction)
    cut = max(1, min(cut, n - 1))
    train = tuple(bars[:cut])
    test = tuple(bars[cut + embargo_bars :])
    return train, test
