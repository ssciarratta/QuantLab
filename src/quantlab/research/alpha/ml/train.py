"""Entrenamiento GBM (LightGBM si disponible; stub logístico si no)."""

from __future__ import annotations

import json
import math
import platform
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from quantlab.core.exceptions import ValidationError
from quantlab.research.alpha.ml.dataset import MlDataset, dataset_to_matrix
from quantlab.research.alpha.ml.features import FEATURE_SCHEMA_VERSION
from quantlab.research.alpha.ml.splits import (
    assert_no_temporal_leakage,
    walk_forward_tabular,
)

MIN_POS_DEFAULT = 8
MIN_ROWS_DEFAULT = 30


def lightgbm_available() -> bool:
    try:
        import lightgbm  # noqa: F401

        return True
    except ImportError:
        return False


@dataclass(frozen=True, slots=True)
class TrainResult:
    model_id: str
    path: Path
    metrics: dict[str, Any]
    backend: str
    manifest: dict[str, Any]


def _auc(y_true: list[int], scores: list[float]) -> float:
    """AUC Wilcoxon-Mann-Whitney (sin sklearn)."""
    pairs = sorted(zip(scores, y_true, strict=True), key=lambda t: t[0])
    n_pos = sum(y_true)
    n_neg = len(y_true) - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    rank_sum = 0.0
    for i, (_s, y) in enumerate(pairs, start=1):
        if y == 1:
            rank_sum += i
    return (rank_sum - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def _sigmoid(z: float) -> float:
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


def _fit_logistic(
    x: list[list[float]],
    y: list[int],
    *,
    lr: float = 0.15,
    epochs: int = 200,
) -> tuple[list[float], float]:
    """Stub auditable si no hay LightGBM — no es producción preferida."""
    dim = len(x[0]) if x else 0
    w = [0.0] * dim
    b = 0.0
    n = max(1, len(x))
    for _ in range(epochs):
        gw = [0.0] * dim
        gb = 0.0
        for row, yi in zip(x, y, strict=True):
            z = b + sum(
                (0.0 if math.isnan(row[j]) else row[j]) * w[j] for j in range(dim)
            )
            p = _sigmoid(z)
            err = p - yi
            for j in range(dim):
                v = 0.0 if math.isnan(row[j]) else row[j]
                gw[j] += err * v
            gb += err
        for j in range(dim):
            w[j] -= lr * gw[j] / n
        b -= lr * gb / n
    return w, b


def _predict_logistic(x: list[list[float]], w: list[float], b: float) -> list[float]:
    out: list[float] = []
    for row in x:
        z = b + sum((0.0 if math.isnan(row[j]) else row[j]) * w[j] for j in range(len(w)))
        out.append(_sigmoid(z))
    return out


def _git_commit() -> str:
    try:
        import subprocess

        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()[:40]
    except Exception:
        pass
    return "unknown"


def train_gbm(
    ds: MlDataset,
    *,
    out_dir: Path,
    model_id: str | None = None,
    min_pos: int = MIN_POS_DEFAULT,
    min_rows: int = MIN_ROWS_DEFAULT,
    hyperparams: dict[str, Any] | None = None,
    seed: int = 42,
) -> TrainResult:
    """Entrena y persiste artefacto + manifest bajo ``out_dir/{model_id}/``."""
    if len(ds.labels) < min_rows:
        raise ValidationError(f"n_rows={len(ds.labels)} < min_rows={min_rows}")
    if ds.n_pos() < min_pos:
        raise ValidationError(
            f"n_pos={ds.n_pos()} < min_pos={min_pos} — abort train (fail-closed)"
        )

    mid = model_id or f"mlgbm_{uuid4().hex[:10]}"
    dest = out_dir / mid
    dest.mkdir(parents=True, exist_ok=True)

    folds = walk_forward_tabular(ds.timestamps, n_folds=2, min_train=max(15, min_rows // 3))
    fold = folds[-1]
    assert_no_temporal_leakage(fold, ds.timestamps)

    x_all, y_all, cat_maps = dataset_to_matrix(ds)
    x_tr = [x_all[i] for i in fold.train_idx]
    y_tr = [y_all[i] for i in fold.train_idx]
    x_te = [x_all[i] for i in fold.test_idx]
    y_te = [y_all[i] for i in fold.test_idx]

    hp = {
        "num_leaves": 15,
        "learning_rate": 0.08,
        "n_estimators": 80,
        "min_data_in_leaf": 5,
        **(hyperparams or {}),
    }

    backend: str
    artifact_name: str
    importance: dict[str, float]

    if lightgbm_available():
        import lightgbm as lgb
        import numpy as np

        dtrain = lgb.Dataset(np.asarray(x_tr, dtype=float), label=np.asarray(y_tr))
        params = {
            "objective": "binary",
            "metric": "auc",
            "verbosity": -1,
            "seed": seed,
            "learning_rate": float(hp["learning_rate"]),
            "num_leaves": int(hp["num_leaves"]),
            "min_data_in_leaf": int(hp["min_data_in_leaf"]),
        }
        booster = lgb.train(
            params,
            dtrain,
            num_boost_round=int(hp["n_estimators"]),
        )
        scores = booster.predict(np.asarray(x_te, dtype=float)).tolist()
        artifact_name = "model.txt"
        booster.save_model(str(dest / artifact_name))
        gain = booster.feature_importance(importance_type="gain")
        importance = {f"f{i}": float(g) for i, g in enumerate(gain)}
        backend = "lightgbm"
        weights_payload: dict[str, Any] = {"backend": backend}
    else:
        w, b = _fit_logistic(x_tr, y_tr, lr=0.12, epochs=250)
        scores = _predict_logistic(x_te, w, b)
        artifact_name = "model_stub.json"
        weights_payload = {"backend": "logistic_stub", "weights": w, "bias": b}
        (dest / artifact_name).write_text(
            json.dumps(weights_payload, sort_keys=True), encoding="utf-8"
        )
        importance = {f"f{i}": abs(w[i]) for i in range(len(w))}
        backend = "logistic_stub"

    auc = _auc(y_te, scores)
    # precision@k
    k = min(5, len(scores))
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
    prec_at_k = sum(y_te[i] for i in order) / max(1, k)

    metrics = {
        "auc": auc,
        "precision_at_k": prec_at_k,
        "k": k,
        "n_train": len(y_tr),
        "n_test": len(y_te),
        "n_pos_train": sum(y_tr),
        "n_pos_test": sum(y_te),
        "feature_importance": importance,
        "fold": fold.fold,
    }

    (dest / "category_maps.json").write_text(
        json.dumps(cat_maps, sort_keys=True), encoding="utf-8"
    )
    (dest / "metrics.json").write_text(json.dumps(metrics, sort_keys=True), encoding="utf-8")

    manifest = {
        "model_id": mid,
        "kind": "alpha_ml_gbm",
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "target_name": ds.target_name,
        "default_strategy_id": ds.default_strategy_id,
        "backend": backend,
        "artifact": artifact_name,
        "hyperparams": hp,
        "seed": seed,
        "git_commit": _git_commit(),
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "n_rows": len(ds.labels),
        "n_pos": ds.n_pos(),
        "n_neg": ds.n_neg(),
        "metrics": {"auc": auc, "precision_at_k": prec_at_k},
        "created_at": datetime.now(tz=UTC).isoformat(),
        "live_blocked": True,
        "note": (
            "Modelo research para signal_type=ml_ranking. "
            "No exime validate_candidate/DSR. No LIVE."
        ),
    }
    (dest / "manifest.json").write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")

    return TrainResult(
        model_id=mid,
        path=dest,
        metrics=metrics,
        backend=backend,
        manifest=manifest,
    )


__all__ = [
    "MIN_POS_DEFAULT",
    "MIN_ROWS_DEFAULT",
    "TrainResult",
    "lightgbm_available",
    "train_gbm",
]
