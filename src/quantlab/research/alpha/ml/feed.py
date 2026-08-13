"""Alimenta el GBM con cada trial de validación; promociona solo si mejora."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.research.alpha.ml.dataset import (
    build_dataset_from_trials,
    make_synthetic_dataset,
)
from quantlab.research.alpha.ml.registry import MlModelRegistry
from quantlab.research.alpha.ml.train import MIN_POS_DEFAULT, MIN_ROWS_DEFAULT, train_gbm
from quantlab.research.alpha.validation.trial_ledger import TrialLedger

RETRAIN_EVERY = 5


def experiments_dir_from_ledger(ledger_path: Path) -> Path:
    """``experiments/alpha_trials/trials.jsonl`` → ``experiments/``."""
    parent = ledger_path.parent
    if parent.name == "alpha_trials":
        return parent.parent
    return parent


def _auc_value(raw: Any) -> float | None:
    try:
        v = float(raw)
    except (TypeError, ValueError):
        return None
    if math.isnan(v):
        return None
    return v


def _should_promote(
    *,
    is_bootstrap: bool,
    candidate_auc: float | None,
    active_auc: float | None,
) -> bool:
    if is_bootstrap:
        return candidate_auc is not None
    if candidate_auc is None:
        return False
    if active_auc is None:
        return True
    return candidate_auc + 1e-9 >= active_auc


def ensure_bootstrap_model(experiments_dir: Path) -> dict[str, Any]:
    """Si no hay modelo activo, entrena uno sintético (marcado bootstrap)."""
    reg = MlModelRegistry(experiments_dir / "alpha_ml")
    if reg.get_active_id():
        st = reg.read_state()
        return {
            "bootstrapped": False,
            "active_model_id": reg.get_active_id(),
            "bootstrap": bool(st.get("bootstrap")),
        }
    ds = make_synthetic_dataset(n=60, n_pos=15, seed=11)
    result = train_gbm(ds, out_dir=reg.root, min_pos=8, min_rows=30)
    st = reg.read_state()
    st["active_model_id"] = result.model_id
    st["last_train_n"] = 0
    st["bootstrap"] = True
    st["active_auc"] = _auc_value((result.metrics or {}).get("auc"))
    reg.write_state(st)
    return {
        "bootstrapped": True,
        "active_model_id": result.model_id,
        "backend": result.backend,
        "bootstrap": True,
        "note": "modelo sintético de arranque; no es aprendizaje real",
    }


def maybe_feed_ml(*, ledger_path: Path | None) -> dict[str, Any]:
    """Tras un trial: entrena candidato; promociona solo si AUC no empeora."""
    if ledger_path is None:
        return {"fed": False, "reason": "sin ledger persistente"}
    try:
        exp = experiments_dir_from_ledger(ledger_path)
        reg = MlModelRegistry(exp / "alpha_ml")
        led = TrialLedger(path=ledger_path)
        n = led.count()
        try:
            ds = build_dataset_from_trials(led, min_rows=1)
        except ValidationError as exc:
            return {"fed": True, "retrained": False, "n_trials": n, "reason": str(exc)}

        if len(ds.labels) < MIN_ROWS_DEFAULT or ds.n_pos() < MIN_POS_DEFAULT:
            return {
                "fed": True,
                "retrained": False,
                "n_trials": n,
                "n_rows": len(ds.labels),
                "n_pos": ds.n_pos(),
                "reason": (
                    f"esperando datos (min {MIN_ROWS_DEFAULT} filas / "
                    f"{MIN_POS_DEFAULT} positivas)"
                ),
            }

        st = reg.read_state()
        last_n = int(st.get("last_train_n") or 0)
        has_model = bool(reg.get_active_id())
        if has_model and (n - last_n) < RETRAIN_EVERY:
            return {
                "fed": True,
                "retrained": False,
                "promoted": False,
                "n_trials": n,
                "last_train_n": last_n,
                "reason": f"retrain cada {RETRAIN_EVERY} trials",
            }

        result = train_gbm(
            ds,
            out_dir=reg.root,
            min_pos=MIN_POS_DEFAULT,
            min_rows=MIN_ROWS_DEFAULT,
        )
        cand_auc = _auc_value((result.metrics or {}).get("auc"))
        is_bootstrap = bool(st.get("bootstrap"))
        active_auc = _auc_value(st.get("active_auc"))
        promote = _should_promote(
            is_bootstrap=is_bootstrap or not has_model,
            candidate_auc=cand_auc,
            active_auc=active_auc,
        )
        st["candidate_model_id"] = result.model_id
        st["candidate_auc"] = cand_auc
        st["last_train_n"] = n
        if promote:
            st["active_model_id"] = result.model_id
            st["active_auc"] = cand_auc
            st["bootstrap"] = False
        reg.write_state(st)
        return {
            "fed": True,
            "retrained": True,
            "promoted": promote,
            "n_trials": n,
            "model_id": result.model_id if promote else st.get("active_model_id"),
            "candidate_model_id": result.model_id,
            "backend": result.backend,
            "auc": cand_auc,
            "reason": None if promote else "candidato no supera AUC del activo",
        }
    except (ValidationError, OSError, ValueError, TypeError, KeyError) as exc:
        return {"fed": False, "retrained": False, "promoted": False, "error": str(exc)}


__all__ = [
    "RETRAIN_EVERY",
    "ensure_bootstrap_model",
    "experiments_dir_from_ledger",
    "maybe_feed_ml",
]
