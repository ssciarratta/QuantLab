"""Hyperparameter optimizer (Fase 12)."""

from quantlab.optimizer.grid import GridSearchOptimizer, OptimizationResult, TrialResult
from quantlab.optimizer.pareto import (
    ParetoFrontResult,
    ParetoPoint,
    compute_pareto_frontier,
    pareto_from_trials,
    pareto_front,
)

__all__ = [
    "GridSearchOptimizer",
    "OptimizationResult",
    "ParetoFrontResult",
    "ParetoPoint",
    "TrialResult",
    "compute_pareto_frontier",
    "pareto_front",
    "pareto_from_trials",
]
