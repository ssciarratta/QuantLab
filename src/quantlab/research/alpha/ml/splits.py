"""Walk-forward tabular con purge/embargo por horizonte."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from quantlab.core.exceptions import ValidationError
from quantlab.research.alpha.ml.dataset import MlDataset


@dataclass(frozen=True, slots=True)
class TabularFold:
    train_idx: tuple[int, ...]
    test_idx: tuple[int, ...]
    fold: int
    embargo: timedelta


def walk_forward_tabular(
    timestamps: Sequence[datetime],
    *,
    n_folds: int = 3,
    train_ratio: float = 0.6,
    embargo: timedelta | None = None,
    min_train: int = 20,
    min_test: int = 5,
) -> tuple[TabularFold, ...]:
    """Splits temporales ordenados; purge = embargo entre fin train y start test."""
    n = len(timestamps)
    if n < min_train + min_test:
        raise ValidationError(f"filas insuficientes para WF tabular: {n}")
    if n_folds < 1:
        raise ValidationError("n_folds >= 1")
    emb = embargo if embargo is not None else timedelta(hours=24)

    def _make_fold(cut: int, fold_id: int) -> TabularFold | None:
        cut = max(min_train, min(cut, n - min_test))
        train_end_ts = timestamps[cut - 1]
        test_start_bound = train_end_ts + emb
        test_idx_list = [i for i in range(cut, n) if timestamps[i] >= test_start_bound]
        if len(test_idx_list) < min_test:
            return None
        return TabularFold(
            train_idx=tuple(range(0, cut)),
            test_idx=tuple(test_idx_list),
            fold=fold_id,
            embargo=emb,
        )

    folds: list[TabularFold] = []
    for f in range(n_folds):
        frac = train_ratio + (1.0 - train_ratio) * (f / max(1, n_folds))
        cut = int(n * min(0.75, frac))
        fold = _make_fold(cut, f)
        if fold is not None:
            folds.append(fold)

    if not folds:
        # Relajar embargo a 1 hora si el default no deja test
        emb = timedelta(hours=1)
        cut = max(min_train, int(n * train_ratio))
        train_end_ts = timestamps[cut - 1]
        test_idx = tuple(i for i in range(cut, n) if timestamps[i] >= train_end_ts + emb)
        if len(test_idx) < min_test:
            # último recurso: corte duro + embargo 0 documentado en fold
            emb = timedelta(0)
            test_idx = tuple(range(cut, n))
        folds.append(
            TabularFold(
                train_idx=tuple(range(0, cut)),
                test_idx=test_idx,
                fold=0,
                embargo=emb,
            )
        )
    return tuple(folds)


def assert_no_temporal_leakage(fold: TabularFold, timestamps: Sequence[datetime]) -> None:
    train_max = max(timestamps[i] for i in fold.train_idx)
    test_min = min(timestamps[i] for i in fold.test_idx)
    if fold.embargo > timedelta(0) and test_min < train_max + fold.embargo:
        raise ValidationError(
            f"leakage temporal: test_min={test_min} < train_max+embargo={train_max + fold.embargo}"
        )
    if test_min < train_max:
        raise ValidationError(f"leakage temporal: test_min={test_min} < train_max={train_max}")


def slice_dataset(ds: MlDataset, idx: Sequence[int]) -> MlDataset:
    return MlDataset(
        feature_rows=tuple(ds.feature_rows[i] for i in idx),
        labels=tuple(ds.labels[i] for i in idx),
        timestamps=tuple(ds.timestamps[i] for i in idx),
        feature_schema_version=ds.feature_schema_version,
        target_name=ds.target_name,
        default_strategy_id=ds.default_strategy_id,
    )


__all__ = [
    "TabularFold",
    "assert_no_temporal_leakage",
    "slice_dataset",
    "walk_forward_tabular",
]
