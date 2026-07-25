"""Frente de Pareto multi-objetivo (Fase 12 residual)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.results import MetricsResult
from quantlab.optimizer.grid import TrialResult


@dataclass(frozen=True, slots=True)
class ParetoPoint:
    trial_id: int
    params: dict[str, Any]
    objectives: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class ParetoFrontResult:
    front: tuple[ParetoPoint, ...]
    dominated: tuple[ParetoPoint, ...]
    n_objectives: int


def _dominates(
    a: Sequence[float],
    b: Sequence[float],
    *,
    maximize: Sequence[bool],
) -> bool:
    """True si a domina a b (al menos mejor en uno, no peor en ninguno)."""
    better = False
    for ai, bi, mx in zip(a, b, maximize, strict=True):
        if mx:
            if ai < bi:
                return False
            if ai > bi:
                better = True
        else:
            if ai > bi:
                return False
            if ai < bi:
                better = True
    return better


def pareto_front(
    points: Sequence[ParetoPoint],
    *,
    maximize: Sequence[bool],
) -> ParetoFrontResult:
    """Calcula el frente de Pareto no dominado."""
    if not points:
        raise ValidationError("points vacío")
    n_obj = len(points[0].objectives)
    if n_obj < 2:
        raise ValidationError("Pareto requiere >= 2 objetivos")
    if len(maximize) != n_obj:
        raise ValidationError("maximize debe coincidir con n objetivos")
    for p in points:
        if len(p.objectives) != n_obj:
            raise ValidationError("objetivos inconsistentes entre puntos")

    front: list[ParetoPoint] = []
    dominated: list[ParetoPoint] = []
    for i, p in enumerate(points):
        is_dom = False
        for j, q in enumerate(points):
            if i == j:
                continue
            if _dominates(q.objectives, p.objectives, maximize=maximize):
                is_dom = True
                break
        if is_dom:
            dominated.append(p)
        else:
            front.append(p)
    return ParetoFrontResult(
        front=tuple(front),
        dominated=tuple(dominated),
        n_objectives=n_obj,
    )


def pareto_from_trials(
    trials: Sequence[TrialResult],
    *,
    score_as_first: bool = True,
    second_objective: Sequence[float],
    maximize: tuple[bool, bool] = (True, False),
) -> ParetoFrontResult:
    """Atajo: score del trial + segundo objetivo externo (ej. max_drawdown)."""
    if len(trials) != len(second_objective):
        raise ValidationError("trials y second_objective deben tener igual longitud")
    points = [
        ParetoPoint(
            trial_id=t.trial_id,
            params=dict(t.params),
            objectives=(
                (float(t.score), float(second_objective[i]))
                if score_as_first
                else (float(second_objective[i]), float(t.score))
            ),
        )
        for i, t in enumerate(trials)
    ]
    return pareto_front(points, maximize=maximize)


def compute_pareto_frontier(
    results: Sequence[MetricsResult],
    objectives: tuple[tuple[str, str], ...],
) -> tuple[MetricsResult, ...]:
    """Frente de Pareto sobre ``MetricsResult``.

    ``objectives``: pares ``(metric_key, "max"|"min")``,
    ej. ``(("sharpe", "max"), ("max_drawdown", "min"))``.
    """
    if not results:
        raise ValidationError("results vacío")
    if len(objectives) < 2:
        raise ValidationError("objectives requiere >= 2 métricas")
    maximize: list[bool] = []
    keys: list[str] = []
    for key, direction in objectives:
        d = direction.lower().strip()
        if d not in ("max", "min", "maximize", "minimize"):
            raise ValidationError("direction debe ser 'max' o 'min'")
        keys.append(key)
        maximize.append(d in ("max", "maximize"))

    points: list[ParetoPoint] = []
    for i, res in enumerate(results):
        vals: list[float] = []
        for key in keys:
            if key not in res.metrics:
                raise ValidationError(f"métrica ausente: {key} en {res.experiment_id}")
            raw = res.metrics[key]
            if isinstance(raw, str):
                raise ValidationError(f"métrica no numérica: {key}")
            vals.append(float(raw))
        points.append(
            ParetoPoint(
                trial_id=i,
                params={"experiment_id": res.experiment_id},
                objectives=tuple(vals),
            )
        )
    front = pareto_front(points, maximize=tuple(maximize))
    keep = {p.trial_id for p in front.front}
    return tuple(results[i] for i in sorted(keep))
