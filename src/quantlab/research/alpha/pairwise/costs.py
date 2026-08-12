"""Costo estimado round-trip para pares (2 piernas)."""

from __future__ import annotations

from quantlab.core.exceptions import ValidationError
from quantlab.research.sim.fee_schedules import get_fee_schedule


def estimate_pair_cost_bps(*, venue: str, market_type: str) -> float:
    """Fee taker ambas piernas (conservador) en bps."""
    try:
        sched = get_fee_schedule(venue, market_type)
    except ValidationError:
        # Lab/synthetic: usar Binance spot VIP0 como proxy conservador
        sched = get_fee_schedule("binance", "spot")
    return float(sched.taker_bps) * 2.0
