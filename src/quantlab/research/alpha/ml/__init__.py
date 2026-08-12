"""Alpha ML ranking (GBM) — desacoplado de scanners/pairwise.

Consume señales ya normalizadas; produce ``signal_type=ml_ranking``.
"""

from __future__ import annotations

from quantlab.research.alpha.ml.attach import attach_ml_ranking_signals
from quantlab.research.alpha.ml.features import (
    FEATURE_SCHEMA_VERSION,
    feature_row_to_vector,
    signal_to_feature_row,
)
from quantlab.research.alpha.ml.feed import ensure_bootstrap_model, maybe_feed_ml
from quantlab.research.alpha.ml.model import MlRankingModel, score_candidates
from quantlab.research.alpha.ml.registry import MlModelRegistry, get_default_registry

__all__ = [
    "FEATURE_SCHEMA_VERSION",
    "MlModelRegistry",
    "MlRankingModel",
    "attach_ml_ranking_signals",
    "ensure_bootstrap_model",
    "feature_row_to_vector",
    "get_default_registry",
    "maybe_feed_ml",
    "score_candidates",
    "signal_to_feature_row",
]
