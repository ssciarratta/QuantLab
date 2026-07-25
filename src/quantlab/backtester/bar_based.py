"""Facade Backtester bar-based 5A (Fase 6)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from quantlab.backtester.accounting import AccountingReport, assert_accounting_balanced
from quantlab.core.contracts.strategy import Strategy
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.core.types.results import MetricsResult, SimulationResult
from quantlab.execution.protocols import FeeModel, LatencyModel, SlippageModel
from quantlab.metrics import MetricsEngine
from quantlab.simulation.engine import BarSimulationEngine, SimulationConfig
from quantlab.simulation.fill_model import ImmediateBarFillModel


@dataclass(frozen=True, slots=True)
class BarBacktestResult:
    """Salida del backtester 5A: simulación + métricas + contabilidad."""

    simulation: SimulationResult
    metrics: MetricsResult
    accounting: AccountingReport


@dataclass(frozen=True, slots=True)
class BarBacktestConfig:
    """Configuración del facade 5A."""

    experiment_id: str
    initial_cash: Decimal = Decimal("100000")
    cash_asset: str = "USDT"
    fee_rate: Decimal = Decimal("0")
    schema_version: str = "1.0"
    min_timeframe_minutes: int = 1
    enforce_accounting: bool = True


class BarBacktester:
    """Facade 5A sobre `BarSimulationEngine` + Metrics + contabilidad cuadrada.

    Operación principal: `run(strategy, bars) → BarBacktestResult`.
    No valida market-making ni microestructura (eso es Fase 7 / 5B).
    """

    def __init__(
        self,
        config: BarBacktestConfig,
        *,
        fill_model: ImmediateBarFillModel | None = None,
        slippage_model: SlippageModel | None = None,
        latency_model: LatencyModel | None = None,
        fee_model: FeeModel | None = None,
        metrics_engine: MetricsEngine | None = None,
    ) -> None:
        self._config = config
        self._engine = BarSimulationEngine(
            SimulationConfig(
                experiment_id=config.experiment_id,
                initial_cash=config.initial_cash,
                cash_asset=config.cash_asset,
                fee_rate=config.fee_rate,
                schema_version=config.schema_version,
            ),
            fill_model=fill_model,
            slippage_model=slippage_model,
            latency_model=latency_model,
            fee_model=fee_model,
        )
        self._metrics = metrics_engine or MetricsEngine()

    def run(self, strategy: Strategy, bars: Sequence[Bar]) -> BarBacktestResult:
        self._validate_bars_5a(bars)
        simulation = self._engine.run(strategy, bars)
        metrics = self._metrics.compute(simulation)
        if self._config.enforce_accounting:
            accounting = assert_accounting_balanced(
                simulation, initial_cash=self._config.initial_cash
            )
        else:
            accounting = AccountingReport(
                ok=True,
                issues=(),
                reconstructed_cash=self._config.initial_cash,
                reported_cash=self._config.initial_cash,
                reported_equity=(
                    simulation.equity_curve[-1].equity
                    if simulation.equity_curve
                    else self._config.initial_cash
                ),
                total_fees=Decimal("0"),
            )
        return BarBacktestResult(
            simulation=simulation,
            metrics=metrics,
            accounting=accounting,
        )

    def _validate_bars_5a(self, bars: Sequence[Bar]) -> None:
        if not bars:
            raise ValidationError("backtester 5A requiere al menos una barra")
        instrument = bars[0].instrument_id
        prev_close = None
        min_seconds = self._config.min_timeframe_minutes * 60
        for bar in bars:
            if bar.instrument_id != instrument:
                raise ValidationError("5A: un solo instrument_id por corrida")
            duration = (bar.timestamp_close - bar.timestamp_open).total_seconds()
            if duration < min_seconds - 1e-9:
                raise ValidationError(
                    f"5A: timeframe de barra < {self._config.min_timeframe_minutes}m"
                )
            if prev_close is not None and bar.timestamp_close <= prev_close:
                raise ValidationError("5A: barras deben ser estrictamente ascendentes")
            prev_close = bar.timestamp_close
