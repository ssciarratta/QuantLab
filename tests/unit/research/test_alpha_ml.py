"""Tests módulo Alpha ML GBM."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.research.alpha.ml.attach import attach_ml_ranking_signals
from quantlab.research.alpha.ml.dataset import make_synthetic_dataset
from quantlab.research.alpha.ml.features import (
    FEATURE_SCHEMA_VERSION,
    feature_row_to_vector,
    signal_to_feature_row,
)
from quantlab.research.alpha.ml.model import score_candidates
from quantlab.research.alpha.ml.registry import MlModelRegistry
from quantlab.research.alpha.ml.splits import assert_no_temporal_leakage, walk_forward_tabular
from quantlab.research.alpha.ml.train import train_gbm
from quantlab.research.alpha.models import AlphaSignal, SignalDirection, SignalScope


def test_signal_to_features_no_bars() -> None:
    sig = AlphaSignal(
        signal_id="a",
        timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        signal_type="legacy_v1",
        scope=SignalScope.INDIVIDUAL,
        symbols=("BN:BTCUSDT",),
        direction=SignalDirection.LONG,
        raw_score=0.7,
        confidence=0.8,
        normalized_score=0.7,
        metadata={"components": [{"name": "momentum", "normalized": 0.6, "available": True}]},
    )
    row = signal_to_feature_row(sig)
    assert row["feature_schema_version"] == FEATURE_SCHEMA_VERSION
    assert row["norm_score"] == 0.7
    assert row["comp_momentum"] == 0.6
    vec = feature_row_to_vector(row)
    assert len(vec) > 10


def test_walk_forward_no_leakage() -> None:
    ts = [datetime(2024, 1, 1, tzinfo=UTC) + timedelta(hours=i) for i in range(60)]
    folds = walk_forward_tabular(
        ts, n_folds=2, min_train=20, min_test=5, embargo=timedelta(hours=2)
    )
    for f in folds:
        assert_no_temporal_leakage(f, ts)


def test_train_and_score(tmp_path: Path) -> None:
    ds = make_synthetic_dataset(n=60, n_pos=15, seed=3)
    result = train_gbm(ds, out_dir=tmp_path, min_pos=8, min_rows=30)
    assert (result.path / "manifest.json").is_file()
    assert result.manifest["feature_schema_version"] == FEATURE_SCHEMA_VERSION
    assert "auc" in result.metrics

    reg = MlModelRegistry(tmp_path)
    reg.set_active(result.model_id)
    model = reg.load_active()
    assert model is not None

    sigs = [
        AlphaSignal(
            signal_id=f"s{i}",
            timestamp=datetime(2024, 6, 1, tzinfo=UTC),
            signal_type="legacy_v1",
            scope=SignalScope.INDIVIDUAL,
            symbols=(f"BN:C{i}USDT",),
            direction=SignalDirection.LONG,
            raw_score=0.2 + i * 0.2,
            normalized_score=0.2 + i * 0.2,
            confidence=0.5,
        )
        for i in range(3)
    ]
    ml = score_candidates(sigs, model=model)
    assert len(ml) == 3
    assert all(s.signal_type == "ml_ranking" for s in ml)
    assert all(0.0 <= s.raw_score <= 1.0 for s in ml)


def test_attach_ml_default_off(tmp_path: Path) -> None:
    payload = {"signals": []}
    out = attach_ml_ranking_signals(payload, experiments_dir=tmp_path, enabled=False)
    assert out["ml_ranking"]["enabled"] is False


def test_train_abort_low_pos(tmp_path: Path) -> None:
    ds = make_synthetic_dataset(n=40, n_pos=2, seed=1)
    with pytest.raises(ValidationError, match="n_pos"):
        train_gbm(ds, out_dir=tmp_path, min_pos=8, min_rows=20)
