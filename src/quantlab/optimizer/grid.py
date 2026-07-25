"""Grid / random search (Fase 12) — requiere F10 para uso científico."""

from __future__ import annotations

import itertools
import random
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from quantlab.core.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class TrialResult:
    params: dict[str, Any]
    score: float
    trial_id: int


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    best: TrialResult
    history: tuple[TrialResult, ...]
    method: str


def _pick_best(best: TrialResult | None, trial: TrialResult, *, maximize: bool) -> TrialResult:
    if best is None:
        return trial
    if maximize and trial.score > best.score:
        return trial
    if not maximize and trial.score < best.score:
        return trial
    return best


class GridSearchOptimizer:
    """Exploración de hiperparámetros con historial determinista."""

    def __init__(self, *, seed: int = 42) -> None:
        self._seed = seed

    def grid(
        self,
        space: Mapping[str, Sequence[Any]],
        objective: Callable[[dict[str, Any]], float],
        *,
        maximize: bool = True,
    ) -> OptimizationResult:
        if not space:
            raise ValidationError("space vacío")
        keys = sorted(space.keys())
        values = [list(space[k]) for k in keys]
        history: list[TrialResult] = []
        best: TrialResult | None = None
        for i, combo in enumerate(itertools.product(*values)):
            params = {k: combo[j] for j, k in enumerate(keys)}
            score = float(objective(params))
            trial = TrialResult(params=params, score=score, trial_id=i)
            history.append(trial)
            best = _pick_best(best, trial, maximize=maximize)
        assert best is not None
        return OptimizationResult(best=best, history=tuple(history), method="grid")

    def random_search(
        self,
        space: Mapping[str, Sequence[Any]],
        objective: Callable[[dict[str, Any]], float],
        *,
        n_trials: int = 20,
        maximize: bool = True,
    ) -> OptimizationResult:
        if n_trials < 1:
            raise ValidationError("n_trials >= 1")
        rng = random.Random(self._seed)
        keys = sorted(space.keys())
        history: list[TrialResult] = []
        best: TrialResult | None = None
        for i in range(n_trials):
            params = {k: rng.choice(list(space[k])) for k in keys}
            score = float(objective(params))
            trial = TrialResult(params=params, score=score, trial_id=i)
            history.append(trial)
            best = _pick_best(best, trial, maximize=maximize)
        assert best is not None
        return OptimizationResult(best=best, history=tuple(history), method="random")
