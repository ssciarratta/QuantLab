"""Simulación multi-venue: leverage, liquidación, funding sobre backtests lab."""

from quantlab.research.sim.leverage_overlay import (
    LeverageOverlayConfig,
    apply_leverage_overlay,
)
from quantlab.research.sim.models import SimCompareRow, SimOverlayResult
from quantlab.research.sim.symbol_map import resolve_instrument

__all__ = [
    "LeverageOverlayConfig",
    "SimCompareRow",
    "SimOverlayResult",
    "apply_leverage_overlay",
    "resolve_instrument",
]
