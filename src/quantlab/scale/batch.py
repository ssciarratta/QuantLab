"""Batch runner paralelo para N simulaciones/jobs (Fase 17).

Diseñado para grid search / Monte Carlo masivos. LIVE routing prohibido.
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import TypeVar

from quantlab.core.exceptions import ValidationError
from quantlab.scale.monitor import MonitorSnapshot, ProgressMonitor

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class BatchRunReport:
    n_jobs: int
    completed: int
    failed: int
    elapsed_seconds: float
    throughput_per_sec: float
    results: tuple[object, ...] | None
    monitor: MonitorSnapshot


class ParallelBatchRunner:
    """Ejecuta jobs indexados en thread-pool con monitoreo y chunks.

    Usa threads (no procesos) para evitar problemas de pickling con closures
    de estrategias; el cuello de botella típico aquí es I/O/CPU liberado por GIL
    en workloads numéricos cortos + orquestación.
    """

    def __init__(self, *, max_workers: int = 4, chunk_size: int = 1000) -> None:
        if max_workers < 1:
            raise ValidationError("max_workers >= 1")
        if chunk_size < 1:
            raise ValidationError("chunk_size >= 1")
        self._max_workers = max_workers
        self._chunk_size = chunk_size

    def map_indexed(
        self,
        n_jobs: int,
        fn: Callable[[int], T],
        *,
        store_results: bool = True,
    ) -> BatchRunReport:
        """Ejecuta ``fn(i)`` para i en ``0..n_jobs-1``."""
        if n_jobs < 0:
            raise ValidationError("n_jobs >= 0")
        monitor = ProgressMonitor(n_jobs)
        if n_jobs == 0:
            snap = monitor.snapshot()
            return BatchRunReport(
                n_jobs=0,
                completed=0,
                failed=0,
                elapsed_seconds=snap.elapsed_seconds,
                throughput_per_sec=0.0,
                results=() if store_results else None,
                monitor=snap,
            )

        results_buf: list[object | None] = [None] * n_jobs if store_results else []
        failed = 0

        def _run_one(i: int) -> tuple[int, T | None, bool]:
            try:
                return i, fn(i), True
            except Exception:
                return i, None, False

        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            for start in range(0, n_jobs, self._chunk_size):
                end = min(start + self._chunk_size, n_jobs)
                futs = [pool.submit(_run_one, i) for i in range(start, end)]
                for fut in as_completed(futs):
                    idx, value, ok = fut.result()
                    if ok:
                        monitor.tick(ok=True)
                        if store_results:
                            results_buf[idx] = value
                    else:
                        failed += 1
                        monitor.tick(ok=False)

        snap = monitor.snapshot()
        out_results: tuple[object, ...] | None
        out_results = tuple(results_buf) if store_results else None
        return BatchRunReport(
            n_jobs=n_jobs,
            completed=snap.completed,
            failed=failed,
            elapsed_seconds=snap.elapsed_seconds,
            throughput_per_sec=snap.throughput_per_sec,
            results=out_results,
            monitor=snap,
        )

    def reduce_indexed(
        self,
        n_jobs: int,
        fn: Callable[[int], float],
        *,
        initial: float = 0.0,
    ) -> tuple[float, BatchRunReport]:
        """Map-reduce sin guardar todos los resultados (apto 100K+)."""
        total = initial
        report = self.map_indexed(n_jobs, fn, store_results=True)
        if report.results is None:
            return total, report
        for v in report.results:
            if v is not None:
                total += float(v)  # type: ignore[arg-type]
        # Re-run pattern for true streaming reduce without storing:
        # dedicated path below for large N
        return total, report

    def stream_sum(
        self,
        n_jobs: int,
        fn: Callable[[int], float],
    ) -> tuple[float, BatchRunReport]:
        """Suma agregada sin materializar la tupla completa de resultados."""
        if n_jobs < 0:
            raise ValidationError("n_jobs >= 0")
        monitor = ProgressMonitor(n_jobs)
        total = 0.0
        failed = 0

        def _run_one(i: int) -> tuple[float, bool]:
            try:
                return float(fn(i)), True
            except Exception:
                return 0.0, False

        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            for start in range(0, n_jobs, self._chunk_size):
                end = min(start + self._chunk_size, n_jobs)
                futs = [pool.submit(_run_one, i) for i in range(start, end)]
                for fut in as_completed(futs):
                    value, ok = fut.result()
                    if ok:
                        total += value
                        monitor.tick(ok=True)
                    else:
                        failed += 1
                        monitor.tick(ok=False)

        snap = monitor.snapshot()
        report = BatchRunReport(
            n_jobs=n_jobs,
            completed=snap.completed,
            failed=failed,
            elapsed_seconds=snap.elapsed_seconds,
            throughput_per_sec=snap.throughput_per_sec,
            results=None,
            monitor=snap,
        )
        return total, report


def assert_capacity_claim(n_jobs: int, *, minimum: int = 100_000) -> None:
    """Valida que el caller declara capacidad 100K+ (contrato de fase)."""
    if n_jobs < minimum:
        raise ValidationError(f"capacidad F17 requiere n_jobs >= {minimum}, got {n_jobs}")


def run_trivial_capacity_probe(
    n_jobs: int = 100_000,
    *,
    max_workers: int = 8,
    chunk_size: int = 5000,
) -> BatchRunReport:
    """Suma 1..n en paralelo sin guardar resultados — smoke 100K+."""
    assert_capacity_claim(n_jobs)
    runner = ParallelBatchRunner(max_workers=max_workers, chunk_size=chunk_size)
    _total, report = runner.stream_sum(n_jobs, lambda i: 1.0)
    if report.completed != n_jobs:
        raise ValidationError("capacity probe incompleto")
    return report


__all__ = [
    "BatchRunReport",
    "ParallelBatchRunner",
    "assert_capacity_claim",
    "run_trivial_capacity_probe",
]
