"""Simulador Monte Carlo con seed fija (Fase 11)."""

from __future__ import annotations

import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from statistics import mean, pstdev

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.core.types.results import SimulationResult


@dataclass(frozen=True, slots=True)
class MonteCarloResult:
    n_scenarios: int
    seed: int
    final_equities: tuple[float, ...]
    mean_equity: float
    std_equity: float
    ci_low: float
    ci_high: float
    results: tuple[SimulationResult, ...]


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
    ) -> MonteCarloResult:
        if n_scenarios < 2:
            raise ValidationError("n_scenarios >= 2")
        if not bars:
            raise ValidationError("bars vacío")
        rng = random.Random(self._seed)
        results: list[SimulationResult] = []
        finals: list[float] = []
        for _ in range(n_scenarios):
            noisy = self._perturb(bars, rng, noise_bps)
            sim = runner(noisy)
            results.append(sim)
            eq = float(sim.equity_curve[-1].equity) if sim.equity_curve else 0.0
            finals.append(eq)
        mu = mean(finals)
        sigma = pstdev(finals) if len(finals) > 1 else 0.0
        # normal approx z~1.96 for 95%
        z = 1.96 if abs(ci - 0.95) < 1e-9 else 1.64
        half = z * sigma / (len(finals) ** 0.5)
        return MonteCarloResult(
            n_scenarios=n_scenarios,
            seed=self._seed,
            final_equities=tuple(finals),
            mean_equity=mu,
            std_equity=sigma,
            ci_low=mu - half,
            ci_high=mu + half,
            results=tuple(results),
        )

    @staticmethod
    def _perturb(bars: Sequence[Bar], rng: random.Random, noise_bps: float) -> list[Bar]:
        out: list[Bar] = []
        for b in bars:
            shock = Decimal(str(1 + rng.gauss(0, noise_bps / 10000.0)))
            if shock <= 0:
                shock = Decimal("0.0001")
            o = (b.open * shock).quantize(Decimal("0.00000001"))
            c = (b.close * shock).quantize(Decimal("0.00000001"))
            h = max((b.high * shock).quantize(Decimal("0.00000001")), o, c)
            low = min((b.low * shock).quantize(Decimal("0.00000001")), o, c)
            out.append(
                Bar(
                    instrument_id=b.instrument_id,
                    open=o,
                    high=h,
                    low=low,
                    close=c,
                    volume=b.volume,
                    timestamp_open=b.timestamp_open,
                    timestamp_close=b.timestamp_close,
                    timeframe=b.timeframe,
                )
            )
        return out
