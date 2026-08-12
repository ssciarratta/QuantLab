"""Deflated Sharpe Ratio (Bailey-López de Prado simplificado)."""

from __future__ import annotations

import math


def deflated_sharpe_ratio(
    observed_sharpe: float,
    *,
    n_trials: int,
    n_observations: int,
    sharpe_benchmark: float = 0.0,
) -> float:
    """DSR aproximado: penaliza por múltiples pruebas.

    Referencia: Bailey & López de Prado (2014) — implementación conservadora
    sin momentos superiores (skew/kurtosis = normal).
    """
    if n_observations < 4 or n_trials < 1:
        return 0.0
    # Varianza esperada del máximo Sharpe bajo H0 (aprox.)
    euler = 0.5772156649
    if n_trials <= 1:
        expected_max = 0.0
    else:
        expected_max = sharpe_benchmark + math.sqrt(2.0 * math.log(n_trials)) * (
            1.0 - euler / (2.0 * math.log(max(2, n_trials)))
        )
    se = math.sqrt((1.0 + 0.5 * observed_sharpe**2) / max(1, n_observations - 1))
    if se <= 0:
        return 0.0
    z = (observed_sharpe - expected_max) / se
    # CDF normal aprox
    cdf = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
    return max(0.0, min(1.0, cdf))
