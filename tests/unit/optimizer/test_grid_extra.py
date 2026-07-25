"""Cobertura extra: bordes de GridSearchOptimizer."""

from __future__ import annotations

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.optimizer.grid import GridSearchOptimizer


def test_grid_empty_space_raises() -> None:
    opt = GridSearchOptimizer(seed=1)
    with pytest.raises(ValidationError, match="space vacío"):
        opt.grid({}, objective=lambda p: 0.0)


def test_random_search_invalid_n_trials() -> None:
    opt = GridSearchOptimizer(seed=1)
    with pytest.raises(ValidationError, match="n_trials"):
        opt.random_search({"x": [1, 2]}, objective=lambda p: float(p["x"]), n_trials=0)
    with pytest.raises(ValidationError, match="n_trials"):
        opt.random_search({"x": [1]}, objective=lambda p: 1.0, n_trials=-3)


def test_grid_minimize_happy_path() -> None:
    opt = GridSearchOptimizer(seed=7)
    result = opt.grid(
        {"x": [1, 2, 3], "y": [10, 20]},
        objective=lambda p: float(p["x"]) + float(p["y"]),
        maximize=False,
    )
    assert result.method == "grid"
    assert result.best.params == {"x": 1, "y": 10}
    assert result.best.score == 11.0
    assert len(result.history) == 6


def test_random_search_happy_path() -> None:
    opt = GridSearchOptimizer(seed=42)
    result = opt.random_search(
        {"a": [1, 2, 3], "b": [0.5, 1.5]},
        objective=lambda p: float(p["a"]) * float(p["b"]),
        n_trials=5,
        maximize=True,
    )
    assert result.method == "random"
    assert len(result.history) == 5
    assert result.best.trial_id in {t.trial_id for t in result.history}
    assert result.best.score == max(t.score for t in result.history)
