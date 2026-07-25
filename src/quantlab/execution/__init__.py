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
from quantlab.execution.live_gate import (
    LIVE_BLOCKED,
    LIVE_ROUTING_BLOCKED_MSG,
    LiveOrderRouter,
    assert_live_routing_blocked,
)
from quantlab.execution.order_router import GatedBackendRouter, NullRouter, OrderRouter
from quantlab.execution.protocols import FeeModel, LatencyModel, SlippageModel
from quantlab.execution.slippage import (
    FixedSlippageModel,
    NoSlippageModel,
    VolumeShareSlippageModel,
)

__all__ = [
    "LIVE_BLOCKED",
    "LIVE_ROUTING_BLOCKED_MSG",
    "FeeAssessment",
    "FeeModel",
    "FixedLatencyModel",
    "FixedSlippageModel",
    "GatedBackendRouter",
    "LatencyDecision",
    "LatencyModel",
    "LiveOrderRouter",
    "MakerTakerFeeModel",
    "NoSlippageModel",
    "NullRouter",
    "OrderRouter",
    "ProportionalFeeModel",
    "SlippageModel",
    "VolumeShareSlippageModel",
    "ZeroFeeModel",
    "ZeroLatencyModel",
    "assert_live_routing_blocked",
]
