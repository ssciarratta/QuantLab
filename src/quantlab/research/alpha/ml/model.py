"""Inferencia: candidatas → AlphaSignal signal_type=ml_ranking."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.research.alpha.ml.features import (
    FEATURE_SCHEMA_VERSION,
    feature_row_to_vector,
    signal_to_feature_row,
)
from quantlab.research.alpha.models import AlphaSignal, SignalDirection
from quantlab.research.alpha.normalization import percentile_rank_signals
from quantlab.research.alpha.signals import stable_signal_id


def _sigmoid(z: float) -> float:
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


class MlRankingModel:
    """Wrapper de inferencia (LightGBM o stub logístico)."""

    def __init__(self, model_dir: Path) -> None:
        self.model_dir = model_dir
        manifest_path = model_dir / "manifest.json"
        if not manifest_path.is_file():
            raise ValidationError(f"manifest ML ausente: {manifest_path}")
        self.manifest: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
        maps_path = model_dir / "category_maps.json"
        self.category_maps: dict[str, dict[str, int]] = (
            json.loads(maps_path.read_text(encoding="utf-8")) if maps_path.is_file() else {}
        )
        self.backend = str(self.manifest.get("backend") or "")
        artifact = str(self.manifest.get("artifact") or "")
        self._booster: Any = None
        self._weights: list[float] | None = None
        self._bias = 0.0
        art_path = model_dir / artifact
        if not art_path.is_file():
            raise ValidationError(f"artefacto ML ausente: {art_path}")
        if self.backend == "lightgbm":
            import lightgbm as lgb

            self._booster = lgb.Booster(model_file=str(art_path))
        else:
            payload = json.loads(art_path.read_text(encoding="utf-8"))
            self._weights = [float(x) for x in payload.get("weights") or []]
            self._bias = float(payload.get("bias") or 0.0)

    @property
    def model_id(self) -> str:
        return str(self.manifest.get("model_id") or self.model_dir.name)

    def predict_proba(self, signals: Sequence[AlphaSignal | Mapping[str, Any]]) -> list[float]:
        rows = [signal_to_feature_row(s) for s in signals]
        x = [feature_row_to_vector(r, category_maps=self.category_maps) for r in rows]
        if self._booster is not None:
            import numpy as np

            return [float(p) for p in self._booster.predict(np.asarray(x, dtype=float))]
        assert self._weights is not None
        out: list[float] = []
        for row in x:
            z = self._bias + sum(
                (0.0 if math.isnan(row[j]) else row[j]) * self._weights[j]
                for j in range(len(self._weights))
            )
            out.append(_sigmoid(z))
        return out


def score_candidates(
    signals: Sequence[AlphaSignal],
    *,
    model: MlRankingModel,
    timestamp: datetime | None = None,
) -> tuple[AlphaSignal, ...]:
    """Produce señales ``ml_ranking`` (complemento Ranking A, no reemplazo)."""
    if not signals:
        return ()
    ts = timestamp or datetime.now(tz=UTC)
    probs = model.predict_proba(signals)
    out: list[AlphaSignal] = []
    for sig, p in zip(signals, probs, strict=True):
        out.append(
            AlphaSignal(
                signal_id=stable_signal_id(
                    signal_type="ml_ranking",
                    scope=sig.scope,
                    symbols=sig.symbols,
                    timestamp=ts,
                    raw_score=float(p),
                    lag=sig.lag,
                    lookback=sig.lookback,
                ),
                timestamp=ts,
                signal_type="ml_ranking",
                scope=sig.scope,
                symbols=sig.symbols,
                direction=sig.direction
                if sig.direction is not SignalDirection.NEUTRAL
                else SignalDirection.LONG,
                raw_score=float(p),
                confidence=float(p),
                lookback=sig.lookback,
                lag=sig.lag,
                timeframe=sig.timeframe,
                metadata={
                    "model_id": model.model_id,
                    "feature_schema_version": FEATURE_SCHEMA_VERSION,
                    "source_signal_id": sig.signal_id,
                    "source_signal_type": sig.signal_type,
                    "backend": model.backend,
                    "market_type": (sig.metadata or {}).get("market_type"),
                },
            )
        )
    ranked = percentile_rank_signals(tuple(out), group_by=("timestamp", "timeframe", "scope"))
    return tuple(sorted(ranked, key=lambda s: s.normalized_score or 0.0, reverse=True))


__all__ = ["MlRankingModel", "score_candidates"]
