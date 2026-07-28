"""Límites y presets Monte Carlo (corrección post-mini-lab)."""

from __future__ import annotations

from typing import Final

MIN_SCENARIOS: Final[int] = 2
MAX_SCENARIOS: Final[int] = 1_000_000
DEFAULT_SCENARIOS: Final[int] = 1_000
# Preset de desarrollo / demos cortas (NO es tope técnico).
MINI_LAB_SCENARIOS: Final[int] = 20

MIN_BARS: Final[int] = 8
MAX_BARS: Final[int] = 500  # lab: horizonte de velas por escenario
DEFAULT_BARS: Final[int] = 60

DEFAULT_BATCH_SIZE: Final[int] = 1_000
DEFAULT_MAX_PERSISTED_TRAJECTORIES: Final[int] = 16
DEFAULT_MAX_DISPLAYED_TRAJECTORIES: Final[int] = 16

# Por debajo: se guardan todos los final_equities (+ results opcionales).
KEEP_ALL_EQUITIES_THRESHOLD: Final[int] = 10_000

# Confirmación UI / API flag required.
CONFIRM_LARGE_THRESHOLD: Final[int] = 100_000
CONFIRM_EXTREME_THRESHOLD: Final[int] = 1_000_000

# Sync HTTP: por encima → job async.
ASYNC_JOB_THRESHOLD: Final[int] = 5_000

SCENARIO_PRESETS: Final[dict[str, int]] = {
    "rapido": 100,
    "exploratorio": 1_000,
    "estandar": 10_000,
    "profundo": 100_000,
    "extremo": 1_000_000,
}

HISTOGRAM_BINS: Final[int] = 40
RESERVOIR_SAMPLE_SIZE: Final[int] = 2_000


def validate_n_scenarios(n: int) -> None:
    from quantlab.core.exceptions import ValidationError

    if not isinstance(n, int) or isinstance(n, bool):
        raise ValidationError("n_scenarios debe ser int")
    if n < MIN_SCENARIOS:
        raise ValidationError(f"n_scenarios >= {MIN_SCENARIOS}")
    if n > MAX_SCENARIOS:
        raise ValidationError(f"n_scenarios <= {MAX_SCENARIOS}")


def validate_n_bars(n: int) -> None:
    from quantlab.core.exceptions import ValidationError

    if not isinstance(n, int) or isinstance(n, bool):
        raise ValidationError("n_bars debe ser int")
    if n < MIN_BARS:
        raise ValidationError(f"n_bars >= {MIN_BARS} (velas por escenario)")
    if n > MAX_BARS:
        raise ValidationError(f"n_bars <= {MAX_BARS}")


def storage_mode_for(n_scenarios: int) -> str:
    if n_scenarios <= KEEP_ALL_EQUITIES_THRESHOLD:
        return "full_equities"
    return "summary_and_sample"


def estimate_cost(
    *,
    n_scenarios: int,
    n_bars: int,
    store_paths: bool,
    max_persisted_trajectories: int = DEFAULT_MAX_PERSISTED_TRAJECTORIES,
    scenarios_per_second: float | None = None,
) -> dict[str, object]:
    """Estimación aproximada (no contractual)."""
    ops = int(n_scenarios) * int(n_bars)
    if scenarios_per_second and scenarios_per_second > 0:
        sps = float(scenarios_per_second)
    else:
        sps = 800.0
    seconds = n_scenarios / sps
    traj = min(max_persisted_trajectories, n_scenarios) if store_paths else 0
    mode = storage_mode_for(n_scenarios)
    return {
        "n_scenarios": n_scenarios,
        "n_bars": n_bars,
        "approx_bar_operations": ops,
        "storage_mode": mode,
        "trajectories_persisted": traj,
        "final_equities_policy": (
            "full" if mode == "full_equities" else "histogram+reservoir_sample"
        ),
        "estimated_seconds": round(seconds, 2),
        "estimated_seconds_range": [
            round(seconds * 0.5, 2),
            round(seconds * 2.5, 2),
        ],
        "scenarios_per_second_assumed": sps,
        "approximation": True,
        "note": "Estimación heurística; el throughput real se mide en ejecución.",
    }
