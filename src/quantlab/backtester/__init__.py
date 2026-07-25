"""Backtester QuantLab — facade 5A/5B."""

from quantlab.backtester.accounting import AccountingReport, assert_accounting_balanced
from quantlab.backtester.bar_based import BarBacktestConfig, BarBacktester, BarBacktestResult
from quantlab.backtester.book_slippage import BookSlippageModel
from quantlab.backtester.golden import (
    GoldenRunSpec,
    assert_matches_golden,
    build_golden,
    load_golden,
    save_golden,
)
from quantlab.backtester.inventory import InventoryTracker
from quantlab.backtester.market_replay import MarketReplay, ReplayEvent
from quantlab.backtester.micro import MicroBacktestConfig, MicroBacktester, MicroBacktestResult
from quantlab.backtester.micro_engine import MicroSimulationConfig, MicroSimulationEngine
from quantlab.backtester.partial_fill import PartialFillDecision, PartialFillModel, RestingOrder

__all__ = [
    "AccountingReport",
    "BarBacktestConfig",
    "BarBacktestResult",
    "BarBacktester",
    "BookSlippageModel",
    "GoldenRunSpec",
    "InventoryTracker",
    "MarketReplay",
    "MicroBacktestConfig",
    "MicroBacktestResult",
    "MicroBacktester",
    "MicroSimulationConfig",
    "MicroSimulationEngine",
    "PartialFillDecision",
    "PartialFillModel",
    "ReplayEvent",
    "RestingOrder",
    "assert_accounting_balanced",
    "assert_matches_golden",
    "build_golden",
    "load_golden",
    "save_golden",
]
