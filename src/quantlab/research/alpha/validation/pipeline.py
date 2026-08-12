"""Pipeline: selección (scanner) separada de evaluación (backtest + DSR)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.metrics.engine import sharpe_ratio
from quantlab.research.alpha.models import AlphaSignal
from quantlab.research.alpha.validation.deflated_sharpe import deflated_sharpe_ratio
from quantlab.research.alpha.validation.trial_ledger import TrialLedger


@dataclass(frozen=True, slots=True)
class BacktestEvalResult:
    signal_id: str
    sharpe_net: float
    max_drawdown: float
    n_returns: int
    deflated_sharpe: float
    validated: bool


class ValidationPipeline:
    """Impone que Sharpe/DSR no alimenten el scanner de selección."""

    def __init__(self, ledger: TrialLedger | None = None) -> None:
        self._ledger = ledger or TrialLedger()

    @property
    def ledger(self) -> TrialLedger:
        return self._ledger

    def log_detection_trials(
        self,
        signals: tuple[AlphaSignal, ...],
        *,
        detector_id: str,
    ) -> None:
        for sig in signals:
            self._ledger.log(
                trial_id=sig.signal_id,
                detector_id=detector_id,
                signal_type=sig.signal_type,
                symbols=sig.symbols,
                lag=sig.lag,
                lookback=sig.lookback,
                metadata={"phase": "detection"},
            )

    def evaluate_backtest(
        self,
        signal: AlphaSignal,
        *,
        net_returns: tuple[float, ...],
        periods_per_year: float = 8760.0,
    ) -> BacktestEvalResult:
        """Evalúa una señal ya candidata — nunca mezclar con fase detect."""
        if not net_returns:
            raise ValidationError("net_returns vacío")
        sr = sharpe_ratio(net_returns, periods_per_year=periods_per_year)
        n_trials = max(1, self._ledger.count())
        dsr = deflated_sharpe_ratio(
            sr,
            n_trials=n_trials,
            n_observations=len(net_returns),
        )
        peak = 1.0
        eq = 1.0
        max_dd = 0.0
        for r in net_returns:
            eq *= 1.0 + r
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd
        validated = dsr >= 0.95 and sr > 0
        return BacktestEvalResult(
            signal_id=signal.signal_id,
            sharpe_net=sr,
            max_drawdown=max_dd,
            n_returns=len(net_returns),
            deflated_sharpe=dsr,
            validated=validated,
        )

    def rank_validated(
        self,
        results: tuple[BacktestEvalResult, ...],
    ) -> tuple[BacktestEvalResult, ...]:
        return tuple(sorted(results, key=lambda r: r.deflated_sharpe, reverse=True))

    def assert_no_selection_leakage(self, *, selection_scores: dict[str, Any]) -> None:
        forbidden = {"sharpe", "deflated_sharpe", "sharpe_net", "pnl", "returns"}
        for key in selection_scores:
            if key in forbidden:
                raise ValidationError(
                    f"leakage selección/evaluación: campo prohibido {key!r} en scanner"
                )
