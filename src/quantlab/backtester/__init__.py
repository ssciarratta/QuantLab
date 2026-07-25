"""Backtester QuantLab — facade 5A (Fase 6)."""

from quantlab.backtester.accounting import AccountingReport, assert_accounting_balanced
from quantlab.backtester.bar_based import BarBacktestConfig, BarBacktester, BarBacktestResult
from quantlab.backtester.golden import (
    GoldenRunSpec,
    assert_matches_golden,
    build_golden,
    load_golden,
    save_golden,
)

__all__ = [
    "AccountingReport",
    "BarBacktestConfig",
    "BarBacktestResult",
    "BarBacktester",
    "GoldenRunSpec",
    "assert_accounting_balanced",
    "assert_matches_golden",
    "build_golden",
    "load_golden",
    "save_golden",
]
