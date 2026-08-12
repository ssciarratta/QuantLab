"""Monte Carlo ligero sobre hedge ratio (pairwise robustez)."""

from __future__ import annotations

import random


def stress_hedge_ratio(
    beta: float,
    *,
    n_shocks: int = 100,
    shock_std: float = 0.05,
    seed: int = 42,
) -> dict[str, float]:
    """Simula variación del hedge ratio; retorna percentiles de |delta|."""
    rng = random.Random(seed)
    deltas = [abs(rng.gauss(beta, shock_std) - beta) for _ in range(n_shocks)]
    deltas.sort()
    n = len(deltas)
    return {
        "p50": deltas[n // 2],
        "p95": deltas[int(n * 0.95)],
        "max": deltas[-1],
    }
