"""Simulación multi-venue: leverage, liquidación, funding sobre backtests lab."""

from quantlab.research.sim.benchmark import (
    BenchmarkPeriod,
    annual_rate_to_period_return,
    compute_benchmark,
)
from quantlab.research.sim.compare import run_sim_compare
from quantlab.research.sim.costs import ExtraCost, apply_extra_costs
from quantlab.research.sim.fee_schedules import (
    PRESETS,
    VenueFeeSchedule,
    get_fee_schedule,
    list_fee_schedules,
)
from quantlab.research.sim.leverage_overlay import (
    LeverageOverlayConfig,
    apply_leverage_overlay,
)
from quantlab.research.sim.models import SimCompareRow, SimOverlayResult
from quantlab.research.sim.period_bars import (
    BINANCE_INTERVALS,
    estimate_n_bars,
    interval_minutes,
)
from quantlab.research.sim.sizing import validate_trade_size
from quantlab.research.sim.symbol_map import resolve_instrument

__all__ = [
    "BINANCE_INTERVALS",
    "BenchmarkPeriod",
    "ExtraCost",
    "LeverageOverlayConfig",
    "PRESETS",
    "SimCompareRow",
    "SimOverlayResult",
    "VenueFeeSchedule",
    "annual_rate_to_period_return",
    "apply_extra_costs",
    "apply_leverage_overlay",
    "compute_benchmark",
    "estimate_n_bars",
    "get_fee_schedule",
    "interval_minutes",
    "list_fee_schedules",
    "resolve_instrument",
    "run_sim_compare",
    "validate_trade_size",
]
