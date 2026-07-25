"""Capa de ejecución simulada — políticas de mercado (Fase 5).

Separada de `core/` (dominio) y de `data/` (adapters externos).
"""

from quantlab.execution.fees import (
    FeeAssessment,
    MakerTakerFeeModel,
    ProportionalFeeModel,
    ZeroFeeModel,
)
from quantlab.execution.latency import FixedLatencyModel, LatencyDecision, ZeroLatencyModel
from quantlab.execution.protocols import FeeModel, LatencyModel, SlippageModel
from quantlab.execution.slippage import (
    FixedSlippageModel,
    NoSlippageModel,
    VolumeShareSlippageModel,
)

__all__ = [
    "FeeAssessment",
    "FeeModel",
    "FixedLatencyModel",
    "FixedSlippageModel",
    "LatencyDecision",
    "LatencyModel",
    "MakerTakerFeeModel",
    "NoSlippageModel",
    "ProportionalFeeModel",
    "SlippageModel",
    "VolumeShareSlippageModel",
    "ZeroFeeModel",
    "ZeroLatencyModel",
]
