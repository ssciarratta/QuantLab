"""Facade Backtester microestructura 5B."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from quantlab.backtester.accounting import AccountingReport, assert_accounting_balanced
from quantlab.backtester.market_replay import MarketReplay
from quantlab.backtester.micro_engine import MicroSimulationConfig, MicroSimulationEngine
from quantlab.backtester.partial_fill import PartialFillModel
from quantlab.core.contracts.strategy import Strategy
from quantlab.core.types.market import OrderBookSnapshot, Trade
from quantlab.core.types.results import MetricsResult, SimulationResult
from quantlab.execution.protocols import FeeModel
from quantlab.metrics import MetricsEngine


@dataclass(frozen=True, slots=True)
class MicroBacktestResult:
    simulation: SimulationResult
    metrics: MetricsResult
    accounting: AccountingReport


@dataclass(frozen=True, slots=True)
class MicroBacktestConfig:
    experiment_id: str
    initial_cash: Decimal = Decimal("100000")
    cash_asset: str = "USDT"
    max_abs_inventory: Decimal = Decimal("100")
    enforce_accounting: bool = True


class MicroBacktester:
    """Facade 5B: trades/book replay → partial fills → metrics + accounting."""

    def __init__(
        self,
        config: MicroBacktestConfig,
        *,
        fill_model: PartialFillModel | None = None,
        fee_model: FeeModel | None = None,
        metrics_engine: MetricsEngine | None = None,
    ) -> None:
        self._config = config
        self._engine = MicroSimulationEngine(
            MicroSimulationConfig(
                experiment_id=config.experiment_id,
                initial_cash=config.initial_cash,
                cash_asset=config.cash_asset,
                max_abs_inventory=config.max_abs_inventory,
            ),
            fill_model=fill_model or PartialFillModel(),
            fee_model=fee_model,
        )
        self._metrics = metrics_engine or MetricsEngine()

    def run(
        self,
        strategy: Strategy,
        *,
        trades: Sequence[Trade],
        books: Sequence[OrderBookSnapshot] = (),
    ) -> MicroBacktestResult:
        replay = MarketReplay(trades=trades, books=books)
        simulation = self._engine.run(strategy, replay)
        metrics = self._metrics.compute(simulation)
        if self._config.enforce_accounting and simulation.portfolio_snapshots:
            accounting = assert_accounting_balanced(
                simulation, initial_cash=self._config.initial_cash
            )
        else:
            accounting = AccountingReport(
                ok=True,
                issues=(),
                reconstructed_cash=self._config.initial_cash,
                reported_cash=self._config.initial_cash,
                reported_equity=self._config.initial_cash,
                total_fees=Decimal("0"),
            )
        return MicroBacktestResult(simulation=simulation, metrics=metrics, accounting=accounting)
