"""Simulador Monte Carlo con seed fija (Fase 11 + contratos MC v2)."""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from statistics import mean, median, pstdev

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.core.types.results import SimulationResult
from quantlab.montecarlo.models import (
    MonteCarloConfig,
    MonteCarloDistribution,
    MonteCarloMethod,
    MonteCarloMetrics,
)


@dataclass(frozen=True, slots=True)
class MonteCarloResult:
    """Resultado del motor. Campos legacy (mean/std/ci) se mantienen.

    ``metrics`` documenta si solo hay equities finales o hay paths.
    ``equity_paths`` es opcional (None si no se materializan por memoria).
    """

    n_scenarios: int
    seed: int
    final_equities: tuple[float, ...]
    mean_equity: float
    std_equity: float
    ci_low: float
    ci_high: float
    results: tuple[SimulationResult, ...]
    method: MonteCarloMethod = MonteCarloMethod.PRICE_SHOCK_RERUN
    noise_bps: float = 10.0
    ci_level: float = 0.95
    n_bars: int | None = None
    distribution: MonteCarloDistribution = MonteCarloDistribution.GAUSSIAN
    metrics: MonteCarloMetrics | None = None
    equity_paths: tuple[tuple[float, ...], ...] | None = None
    config: MonteCarloConfig | None = None


class MonteCarloSimulator:
    """Perturba closes con ruido gaussiano y re-ejecuta un runner determinista."""

    def __init__(self, *, seed: int = 42) -> None:
        self._seed = seed

    def run(
        self,
        bars: Sequence[Bar],
        runner: Callable[[Sequence[Bar]], SimulationResult],
        *,
        n_scenarios: int = 50,
        noise_bps: float = 10.0,
        ci: float = 0.95,
        config: MonteCarloConfig | None = None,
        store_paths: bool = False,
        max_paths_stored: int = 32,
        initial_equity: float | None = None,
    ) -> MonteCarloResult:
        cfg = config
        if cfg is None:
            cfg = MonteCarloConfig(
                n_scenarios=n_scenarios,
                n_bars=len(bars) if bars else 1,
                seed=self._seed,
                ci_level=ci,
                noise_bps=noise_bps,
            )
        else:
            # Semilla del simulador manda si se construyó con seed explícito
            # distinto; preferimos config.seed cuando se pasa config.
            self._seed = cfg.seed
            n_scenarios = cfg.n_scenarios
            noise_bps = cfg.noise_bps
            ci = cfg.ci_level

        if n_scenarios < 2:
            raise ValidationError("n_scenarios >= 2")
        if not bars:
            raise ValidationError("bars vacío")
        if cfg.as_of_time is not None:
            for b in bars:
                if b.timestamp_close > cfg.as_of_time:
                    raise ValidationError(
                        "look-ahead: barra con timestamp_close > as_of_time"
                    )

        rng = random.Random(self._seed)
        results: list[SimulationResult] = []
        finals: list[float] = []
        paths: list[tuple[float, ...]] = []
        for _ in range(n_scenarios):
            noisy = self._perturb(bars, rng, noise_bps, cfg)
            sim = runner(noisy)
            results.append(sim)
            eq = float(sim.equity_curve[-1].equity) if sim.equity_curve else 0.0
            finals.append(eq)
            if store_paths and len(paths) < max_paths_stored and sim.equity_curve:
                paths.append(tuple(float(p.equity) for p in sim.equity_curve))

        mu = mean(finals)
        sigma = pstdev(finals) if len(finals) > 1 else 0.0
        z = _z_for_ci(ci)
        half = z * sigma / (len(finals) ** 0.5)
        ci_low = mu - half
        ci_high = mu + half

        sorted_finals = sorted(finals)
        probs = _outcome_probs(finals, initial_equity)
        metrics = MonteCarloMetrics(
            mean_equity=mu,
            std_equity=sigma,
            ci_low=ci_low,
            ci_high=ci_high,
            ci_level=ci,
            ci_kind="wald_mean",
            median_equity=float(median(finals)),
            p05_equity=_percentile(sorted_finals, 0.05),
            p95_equity=_percentile(sorted_finals, 0.95),
            mean_return_pct=_mean_return_pct(finals, initial_equity),
            prob_profit=probs[0],
            prob_loss=probs[1],
            prob_above_initial=probs[2],
            max_drawdown_mean=_mean_max_dd(paths) if paths else None,
            max_drawdown_p95=_p95_max_dd(paths) if paths else None,
            paths_available=bool(paths),
            finals_only=not bool(paths),
            notes=(
                ("solo equities finales; drawdown no calculado",)
                if not paths
                else ("trayectorias parciales almacenadas (límite memoria)",)
            ),
        )

        return MonteCarloResult(
            n_scenarios=n_scenarios,
            seed=self._seed,
            final_equities=tuple(finals),
            mean_equity=mu,
            std_equity=sigma,
            ci_low=ci_low,
            ci_high=ci_high,
            results=tuple(results),
            method=cfg.method,
            noise_bps=float(noise_bps),
            ci_level=float(ci),
            n_bars=len(bars),
            distribution=cfg.distribution,
            metrics=metrics,
            equity_paths=tuple(paths) if paths else None,
            config=cfg,
        )

    @staticmethod
    def _perturb(
        bars: Sequence[Bar],
        rng: random.Random,
        noise_bps: float,
        cfg: MonteCarloConfig,
    ) -> list[Bar]:
        out: list[Bar] = []
        for b in bars:
            if cfg.perturb_ohlc:
                shock = Decimal(str(1 + rng.gauss(0, noise_bps / 10000.0)))
                if shock <= 0:
                    shock = Decimal("0.0001")
                o = (b.open * shock).quantize(Decimal("0.00000001"))
                c = (b.close * shock).quantize(Decimal("0.00000001"))
                h = max((b.high * shock).quantize(Decimal("0.00000001")), o, c)
                low = min((b.low * shock).quantize(Decimal("0.00000001")), o, c)
            else:
                o, h, low, c = b.open, b.high, b.low, b.close
            vol = b.volume
            if cfg.perturb_volume:
                vshock = Decimal(str(max(0.0001, 1 + rng.gauss(0, noise_bps / 10000.0))))
                vol = (b.volume * vshock).quantize(Decimal("0.00000001"))
            # preserve_instrument_id reservado; hoy siempre se conserva el id.
            out.append(
                Bar(
                    instrument_id=b.instrument_id,
                    open=o,
                    high=h,
                    low=low,
                    close=c,
                    volume=vol,
                    timestamp_open=b.timestamp_open,
                    timestamp_close=b.timestamp_close,
                    timeframe=b.timeframe,
                )
            )
        return out


def _z_for_ci(ci: float) -> float:
    if abs(ci - 0.95) < 1e-9:
        return 1.96
    if abs(ci - 0.90) < 1e-9:
        return 1.64
    # aproximación normal estándar vía erfinv no disponible en stdlib limpia;
    # fallback conservador al z de 90% si no es 95%.
    return 1.64


def _percentile(sorted_vals: Sequence[float], q: float) -> float:
    if not sorted_vals:
        return float("nan")
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    pos = q * (len(sorted_vals) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return float(sorted_vals[lo])
    w = pos - lo
    return float(sorted_vals[lo] * (1 - w) + sorted_vals[hi] * w)


def _mean_return_pct(finals: Sequence[float], initial_equity: float | None) -> float | None:
    if initial_equity is None or initial_equity == 0:
        return None
    rets = [(f / initial_equity - 1.0) * 100.0 for f in finals]
    return float(mean(rets))


def _outcome_probs(
    finals: Sequence[float], initial_equity: float | None
) -> tuple[float | None, float | None, float | None]:
    """(prob_profit, prob_loss, prob_above_initial) en [0,1], o Nones si no aplica."""
    if initial_equity is None or not finals:
        return None, None, None
    n = len(finals)
    profit = sum(1 for f in finals if f > initial_equity)
    loss = sum(1 for f in finals if f < initial_equity)
    above = sum(1 for f in finals if f >= initial_equity)
    return profit / n, loss / n, above / n


def _path_max_drawdown(path: Sequence[float]) -> float | None:
    if len(path) < 2:
        return None
    peak = path[0]
    max_dd = 0.0
    for v in path:
        if v > peak:
            peak = v
        if peak > 0:
            dd = (peak - v) / peak
            if dd > max_dd:
                max_dd = dd
    return max_dd


def _mean_max_dd(paths: Sequence[Sequence[float]]) -> float | None:
    dds = [d for p in paths if (d := _path_max_drawdown(p)) is not None]
    return float(mean(dds)) if dds else None


def _p95_max_dd(paths: Sequence[Sequence[float]]) -> float | None:
    dds = sorted(d for p in paths if (d := _path_max_drawdown(p)) is not None)
    return _percentile(dds, 0.95) if dds else None
