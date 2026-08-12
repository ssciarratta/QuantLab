"""Adjunta señales ml_ranking al payload del scanner (Ranking A complemento)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quantlab.research.alpha.models import AlphaSignal


def attach_ml_ranking_signals(
    payload: dict[str, Any],
    *,
    experiments_dir: Path | None,
    enabled: bool = True,
) -> dict[str, Any]:
    """Adjunta ``ml_ranking`` si hay modelo (bootstrap sintético si aún no existe)."""
    if not enabled or experiments_dir is None:
        payload["ml_ranking"] = {"enabled": False, "active": False}
        return payload
    from quantlab.core.exceptions import ValidationError
    from quantlab.research.alpha.ml.feed import ensure_bootstrap_model
    from quantlab.research.alpha.ml.model import score_candidates
    from quantlab.research.alpha.ml.registry import MlModelRegistry

    try:
        boot = ensure_bootstrap_model(experiments_dir)
        reg = MlModelRegistry(experiments_dir / "alpha_ml")
        model = reg.load_active()
        if model is None:
            payload["ml_ranking"] = {
                "enabled": True,
                "active": False,
                "bootstrap": boot,
                "note": "include_ml=true pero no hay modelo activo",
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
        merged = list(raw_sigs) + ml_dicts
        payload["signals"] = merged
        payload["ml_ranking"] = {
            "enabled": True,
            "active": True,
            "model_id": model.model_id,
            "backend": model.backend,
            "n": len(ml_dicts),
            "bootstrap": boot,
            "note": "ml_ranking complementa Ranking A; no sustituye scanner ni DSR.",
        }
        return payload
    except (ValidationError, OSError, ValueError, TypeError, KeyError) as exc:
        payload["ml_ranking"] = {
            "enabled": True,
            "active": False,
            "error": str(exc),
            "note": "ML no adjuntado; Ranking A intacto",
        }
        return payload


__all__ = ["attach_ml_ranking_signals"]
