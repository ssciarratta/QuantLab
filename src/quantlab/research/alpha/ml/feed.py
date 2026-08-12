"""Alimenta el GBM con cada trial de validación y reentrena cuando hay datos."""

from __future__ import annotations

import json
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


def _state(reg: MlModelRegistry) -> dict[str, Any]:
    path = reg.root / "active.json"
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return dict(raw) if isinstance(raw, dict) else {}
    except (OSError, json.JSONDecodeError, TypeError):
        return {}


def _write_state(reg: MlModelRegistry, payload: dict[str, Any]) -> None:
    path = reg.root / "active.json"
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def ensure_bootstrap_model(experiments_dir: Path) -> dict[str, Any]:
    """Si no hay modelo activo, entrena uno sintético para que el ranking ML arranque."""
    reg = MlModelRegistry(experiments_dir / "alpha_ml")
    if reg.get_active_id():
        return {"bootstrapped": False, "active_model_id": reg.get_active_id()}
    ds = make_synthetic_dataset(n=60, n_pos=15, seed=11)
    result = train_gbm(ds, out_dir=reg.root, min_pos=8, min_rows=30)
    st = _state(reg)
    st["active_model_id"] = result.model_id
    st["last_train_n"] = 0
    st["bootstrap"] = True
    _write_state(reg, st)
    return {
        "bootstrapped": True,
        "active_model_id": result.model_id,
        "backend": result.backend,
        "note": "modelo sintético inicial; se reemplaza al acumular trials reales",
    }


def maybe_feed_ml(*, ledger_path: Path | None) -> dict[str, Any]:
    """Tras un trial: reentrena si hay N suficiente. Nunca tumba la validación."""
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

        st = _state(reg)
        last_n = int(st.get("last_train_n") or 0)
        has_model = bool(reg.get_active_id())
        if has_model and (n - last_n) < RETRAIN_EVERY:
            return {
                "fed": True,
                "retrained": False,
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
        st["active_model_id"] = result.model_id
        st["last_train_n"] = n
        st["bootstrap"] = False
        _write_state(reg, st)
        return {
            "fed": True,
            "retrained": True,
            "n_trials": n,
            "model_id": result.model_id,
            "backend": result.backend,
            "auc": (result.metrics or {}).get("auc"),
        }
    except (ValidationError, OSError, ValueError, TypeError, KeyError) as exc:
        return {"fed": False, "retrained": False, "error": str(exc)}


__all__ = [
    "RETRAIN_EVERY",
    "ensure_bootstrap_model",
    "experiments_dir_from_ledger",
    "maybe_feed_ml",
]
