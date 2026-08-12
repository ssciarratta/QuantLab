"""Adjunta señales ml_ranking al payload del scanner (Ranking A complemento)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quantlab.research.alpha.models import AlphaSignal


def attach_ml_ranking_signals(
    payload: dict[str, Any],
    *,
    experiments_dir: Path | None,
    enabled: bool = False,
) -> dict[str, Any]:
    """Si ``enabled`` y hay modelo activo, append ``ml_signals`` / merge en signals.

    Default off — no cambia comportamiento del scanner.
    """
    if not enabled or experiments_dir is None:
        payload["ml_ranking"] = {"enabled": False, "active": False}
        return payload
    from quantlab.research.alpha.ml.model import score_candidates
    from quantlab.research.alpha.ml.registry import MlModelRegistry

    reg = MlModelRegistry(experiments_dir / "alpha_ml")
    model = reg.load_active()
    if model is None:
        payload["ml_ranking"] = {
            "enabled": True,
            "active": False,
            "note": "include_ml=true pero no hay active_model_id",
        }
        return payload

    raw_sigs = payload.get("signals") or []
    parsed: list[AlphaSignal] = []
    for s in raw_sigs:
        if isinstance(s, dict) and s.get("signal_type") == "ml_ranking":
            continue
        try:
            if isinstance(s, dict):
                parsed.append(AlphaSignal.from_dict(s))
        except (KeyError, TypeError, ValueError):
            continue
    if not parsed:
        payload["ml_ranking"] = {
            "enabled": True,
            "active": True,
            "model_id": model.model_id,
            "n": 0,
            "note": "sin signals base para scorear",
        }
        return payload

    ml_sigs = score_candidates(parsed, model=model)
    ml_dicts = [s.to_dict() for s in ml_sigs]
    payload["ml_signals"] = ml_dicts
    # Complemento: no reemplaza signals originales
    merged = list(raw_sigs) + ml_dicts
    payload["signals"] = merged
    payload["ml_ranking"] = {
        "enabled": True,
        "active": True,
        "model_id": model.model_id,
        "backend": model.backend,
        "n": len(ml_dicts),
        "note": "ml_ranking complementa Ranking A; no sustituye scanner ni DSR.",
    }
    return payload


__all__ = ["attach_ml_ranking_signals"]
