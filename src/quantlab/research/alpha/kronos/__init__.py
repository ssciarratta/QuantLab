"""Capa Kronos dentro del Alpha Scanner (forecast de horizonte, no panel nuevo)."""

from __future__ import annotations

from quantlab.research.alpha.kronos.config import (
    DEFAULT_KRONOS_WEIGHT_BY_PROFILE,
    KRONOS_MAX_CONTEXT,
    KRONOS_TOP_N_DEFAULT,
    KRONOS_TOP_N_MAX,
    KronosConfig,
    kronos_config_from_mapping,
)
from quantlab.research.alpha.kronos.errors import KronosError, KronosSkipReason, KronosStatus
from quantlab.research.alpha.kronos.integrate import apply_kronos_to_scan
from quantlab.research.alpha.kronos.loader import (
    deps_health,
    get_forecast_engine,
    reset_engine_for_tests,
)
from quantlab.research.alpha.kronos.metrics import (
    KronosMetrics,
    compute_kronos_metrics,
    profile_kronos_score,
)
from quantlab.research.alpha.kronos.protocol import (
    ForecastEngine,
    ForecastRequest,
    ForecastResult,
    NullForecastEngine,
    TrajectoryBatch,
)
from quantlab.research.alpha.kronos.scoring_bridge import (
    blend_scores,
    brief_explanation,
    build_score_fields,
)

__all__ = [
    "DEFAULT_KRONOS_WEIGHT_BY_PROFILE",
    "KRONOS_MAX_CONTEXT",
    "KRONOS_TOP_N_DEFAULT",
    "KRONOS_TOP_N_MAX",
    "ForecastEngine",
    "ForecastRequest",
    "ForecastResult",
    "KronosConfig",
    "KronosError",
    "KronosMetrics",
    "KronosSkipReason",
    "KronosStatus",
    "NullForecastEngine",
    "TrajectoryBatch",
    "apply_kronos_to_scan",
    "blend_scores",
    "brief_explanation",
    "build_score_fields",
    "compute_kronos_metrics",
    "deps_health",
    "get_forecast_engine",
    "kronos_config_from_mapping",
    "profile_kronos_score",
    "reset_engine_for_tests",
]
