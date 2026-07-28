"""Simulador Monte Carlo con seed fija, batching y memoria acotada."""

from __future__ import annotations

import math
import random
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from statistics import mean
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.core.types.results import SimulationResult
from quantlab.montecarlo.cancel import CancellationToken
from quantlab.montecarlo.limits import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_MAX_PERSISTED_TRAJECTORIES,
    HISTOGRAM_BINS,
    KEEP_ALL_EQUITIES_THRESHOLD,
    MAX_SCENARIOS,
    MIN_SCENARIOS,
    RESERVOIR_SAMPLE_SIZE,
    storage_mode_for,
    validate_n_scenarios,
)
from quantlab.montecarlo.models import (
    MonteCarloConfig,
    MonteCarloDistribution,
    MonteCarloMethod,
    MonteCarloMetrics,
)
from quantlab.montecarlo.stats import IncrementalMonteCarloStats


@dataclass(frozen=True, slots=True)
class MonteCarloResult:
    """Resultado del motor. Campos legacy (mean/std/ci) se mantienen.

    ``results`` puede estar vacío en corridas grandes (memoria acotada).
    ``final_equities`` puede ser muestra o vacío si ``storage_mode=summary_and_sample``.
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
    storage_mode: str = "full_equities"
    n_scenarios_completed: int | None = None
    n_scenarios_failed: int = 0
    n_scenarios_cancelled: int = 0
    partial: bool = False
    status: str = "completed"
    histogram: dict[str, Any] | None = None
    sample_final_equities: tuple[float, ...] | None = None
    percentiles_approximate: bool = False
    elapsed_seconds: float | None = None
    scenarios_per_second: float | None = None


ProgressCallback = Callable[[dict[str, Any]], None]


class MonteCarloSimulator:
    """Perturba OHLC con ruido gaussiano y re-ejecuta un runner determinista."""

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
        max_paths_stored: int = DEFAULT_MAX_PERSISTED_TRAJECTORIES,
        initial_equity: float | None = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
        retain_results: bool | None = None,
        cancellation: CancellationToken | None = None,
        on_progress: ProgressCallback | None = None,
        progress_interval: int = 100,
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
            self._seed = cfg.seed
            n_scenarios = cfg.n_scenarios
            noise_bps = cfg.noise_bps
            ci = cfg.ci_level

        validate_n_scenarios(n_scenarios)
        if not bars:
            raise ValidationError("bars vacío")
        if batch_size < 1:
            raise ValidationError("batch_size >= 1")
        if cfg.as_of_time is not None:
            for b in bars:
                if b.timestamp_close > cfg.as_of_time:
                    raise ValidationError(
                        "look-ahead: barra con timestamp_close > as_of_time"
                    )

        mode = storage_mode_for(n_scenarios)
        keep_all = mode == "full_equities"
        if retain_results is None:
            retain_results = keep_all and n_scenarios <= KEEP_ALL_EQUITIES_THRESHOLD

        stats = IncrementalMonteCarloStats(
            initial_equity=initial_equity,
            seed=self._seed,
            histogram_bins=HISTOGRAM_BINS,
            reservoir_size=RESERVOIR_SAMPLE_SIZE,
            keep_all=keep_all,
        )
        rng = random.Random(self._seed)
        results: list[SimulationResult] = []
        paths: list[tuple[float, ...]] = []
        cancelled = 0
        t0 = time.perf_counter()
        completed = 0

        remaining = n_scenarios
        while remaining > 0:
            if cancellation is not None and cancellation.is_cancelled:
                cancelled = remaining
                break
            chunk = min(batch_size, remaining)
            for _ in range(chunk):
                if cancellation is not None and cancellation.is_cancelled:
                    cancelled = remaining
                    remaining = 0
                    break
                try:
                    noisy = self._perturb(bars, rng, noise_bps, cfg)
                    sim = runner(noisy)
                    eq = (
                        float(sim.equity_curve[-1].equity)
                        if sim.equity_curve
                        else 0.0
                    )
                    stats.add_equity(eq)
                    if retain_results:
                        results.append(sim)
                    if (
                        store_paths
                        and len(paths) < max_paths_stored
                        and sim.equity_curve
                    ):
                        paths.append(
                            tuple(float(p.equity) for p in sim.equity_curve)
                        )
                except Exception:  # noqa: BLE001 — escenario fallido, no aborta todo
                    stats.add_failure()
                completed += 1
                remaining -= 1
                if on_progress and (
                    completed % progress_interval == 0 or remaining == 0
                ):
                    elapsed = time.perf_counter() - t0
                    sps = completed / elapsed if elapsed > 0 else 0.0
                    eta = (remaining / sps) if sps > 0 else None
                    on_progress(
                        {
                            "status": "running",
                            "completed": completed,
                            "total": n_scenarios,
                            "failed": stats.failed,
                            "pct": round(100.0 * completed / n_scenarios, 2),
                            "elapsed_seconds": round(elapsed, 3),
                            "scenarios_per_second": round(sps, 1),
                            "eta_seconds": round(eta, 2) if eta is not None else None,
                            "batches_hint": math.ceil(n_scenarios / batch_size),
                        }
                    )
            if cancelled:
                break

        elapsed = time.perf_counter() - t0
        snap = stats.snapshot()
        n_done = int(snap["n"] or 0)
        if n_done < 1 and cancelled:
            raise ValidationError("montecarlo cancelado antes de completar escenarios")
        if n_done < 1:
            raise ValidationError("montecarlo sin escenarios válidos")

        mu = float(snap["mean"] or 0.0)
        sigma = float(snap["std"] or 0.0)
        z = _z_for_ci(ci)
        half = z * sigma / (n_done**0.5)
        ci_low = mu - half
        ci_high = mu + half

        finals_tuple: tuple[float, ...]
        if keep_all and snap["final_equities"] is not None:
            finals_tuple = tuple(snap["final_equities"])
        else:
            finals_tuple = tuple(snap["sample_final_equities"] or ())

        notes: list[str] = []
        if not paths:
            notes.append("solo equities finales; drawdown no calculado")
        else:
            notes.append("trayectorias parciales almacenadas (límite memoria)")
        if snap["percentiles_approximate"]:
            notes.append("percentiles aproximados (reservoir sample)")
        if cancelled:
            notes.append("corrida parcial: cancelada por el usuario")

        metrics = MonteCarloMetrics(
            mean_equity=mu,
            std_equity=sigma,
            ci_low=ci_low,
            ci_high=ci_high,
            ci_level=ci,
            ci_kind="wald_mean",
            median_equity=snap["median"],
            p05_equity=snap["p05"],
            p95_equity=snap["p95"],
            mean_return_pct=_mean_return_pct(
                list(finals_tuple) if keep_all else list(snap["sample_final_equities"] or []),
                initial_equity,
            ),
            prob_profit=snap["prob_profit"],
            prob_loss=snap["prob_loss"],
            prob_above_initial=snap["prob_above_initial"],
            max_drawdown_mean=_mean_max_dd(paths) if paths else None,
            max_drawdown_p95=_p95_max_dd(paths) if paths else None,
            paths_available=bool(paths),
            finals_only=not bool(paths),
            notes=tuple(notes),
        )

        status = "cancelled" if cancelled else "completed"
        sps_out: float | None = (completed / elapsed) if elapsed > 0 else None
        return MonteCarloResult(
            n_scenarios=n_scenarios,
            seed=self._seed,
            final_equities=finals_tuple,
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
            storage_mode=mode,
            n_scenarios_completed=n_done,
            n_scenarios_failed=stats.failed,
            n_scenarios_cancelled=cancelled,
            partial=bool(cancelled),
            status=status,
            histogram=snap["histogram"],
            sample_final_equities=tuple(snap["sample_final_equities"] or ()),
            percentiles_approximate=bool(snap["percentiles_approximate"]),
            elapsed_seconds=round(elapsed, 4),
            scenarios_per_second=round(sps_out, 2) if sps_out is not None else None,
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
                vshock = Decimal(
                    str(max(0.0001, 1 + rng.gauss(0, noise_bps / 10000.0)))
                )
                vol = (b.volume * vshock).quantize(Decimal("0.00000001"))
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
    return 1.64


def _mean_return_pct(
    finals: Sequence[float], initial_equity: float | None
) -> float | None:
    if initial_equity is None or initial_equity == 0 or not finals:
        return None
    rets = [(f / initial_equity - 1.0) * 100.0 for f in finals]
    return float(mean(rets))


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
    if not dds:
        return None
    # reuse percentile from stats via simple copy
    from quantlab.montecarlo.stats import _percentile

    return _percentile(list(dds), 0.95)


__all__ = [
    "MAX_SCENARIOS",
    "MIN_SCENARIOS",
    "MonteCarloResult",
    "MonteCarloSimulator",
]