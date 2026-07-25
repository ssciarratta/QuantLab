"""Motor de simulación bar-based (Fase 4 MVP)."""

from __future__ import annotations

from quantlab.simulation.engine import BarSimulationEngine, SimulationConfig
from quantlab.simulation.fill_model import ImmediateBarFillModel

__all__ = [
    "BarSimulationEngine",
    "ImmediateBarFillModel",
    "SimulationConfig",
]
