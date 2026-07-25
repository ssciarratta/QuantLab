"""ParallelBacktester — ProcessPoolExecutor para grids masivos (Fase 17).

LIVE order routing permanece bloqueado. Worker picklable a nivel de módulo.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.data.storage.parquet_store import ParquetProcessedStore
from quantlab.execution.live_gate import LIVE_BLOCKED, assert_live_routing_blocked


@dataclass(frozen=True, slots=True)
class SimJob:
    """Job serializable para pool de procesos."""

    job_id: int
    params: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ParallelRunResult:
    n_jobs: int
    results: tuple[dict[str, Any], ...]
    elapsed_seconds: float
    workers: int
    parquet_path: str | None


def _cpu_bound_score(job: SimJob) -> dict[str, Any]:
    """Worker default: score determinista con carga CPU ligera (picklable)."""
    acc = 0
    seed = int(job.params.get("seed", job.job_id)) % 10_000
    n = int(job.params.get("work", 5_000))
    x = seed
    for _ in range(max(n, 1)):
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF
        acc += x % 97
    score = float(acc % 10_000) / 10_000.0
    return {
        "job_id": job.job_id,
        "score": score,
        "params": dict(job.params),
        "live_blocked": LIVE_BLOCKED,
    }


class ParallelBacktester:
    """Ejecuta N jobs en ``ProcessPoolExecutor``; export Parquet opcional."""

    def __init__(self, *, max_workers: int | None = None) -> None:
        if LIVE_BLOCKED is not True:
            assert_live_routing_blocked()
        cpu = os.cpu_count() or 2
        workers = max_workers if max_workers is not None else max(1, min(cpu, 8))
        if workers < 1:
            raise ValidationError("max_workers >= 1")
        self._max_workers = workers

    def run(
        self,
        jobs: Sequence[SimJob],
        *,
        worker: Callable[[SimJob], dict[str, Any]] | None = None,
        export_parquet_dir: Path | None = None,
    ) -> ParallelRunResult:
        if not jobs:
            raise ValidationError("jobs vacío")
        fn = worker or _cpu_bound_score
        t0 = time.perf_counter()
        with ProcessPoolExecutor(max_workers=self._max_workers) as pool:
            raw = list(pool.map(fn, list(jobs)))
        elapsed = time.perf_counter() - t0
        # Orden estable por job_id
        ordered = tuple(sorted(raw, key=lambda r: int(r["job_id"])))

        parquet_path: str | None = None
        if export_parquet_dir is not None:
            store = ParquetProcessedStore(export_parquet_dir)
            rows = [
                {
                    "job_id": str(r["job_id"]),
                    "score": str(r.get("score", "")),
                    "params": str(r.get("params", {})),
                }
                for r in ordered
            ]
            written = store.write_rows(
                dataset_id="parallel_backtester",
                schema_version="1.0",
                symbol="JOBS",
                timeframe="batch",
                rows=rows,
                meta={"n_jobs": len(jobs), "workers": self._max_workers},
            )
            parquet_path = written.path

        return ParallelRunResult(
            n_jobs=len(jobs),
            results=ordered,
            elapsed_seconds=elapsed,
            workers=self._max_workers,
            parquet_path=parquet_path,
        )

    def run_sequential(
        self,
        jobs: Sequence[SimJob],
        *,
        worker: Callable[[SimJob], dict[str, Any]] | None = None,
    ) -> ParallelRunResult:
        """Baseline secuencial para comparar throughput."""
        if not jobs:
            raise ValidationError("jobs vacío")
        fn = worker or _cpu_bound_score
        t0 = time.perf_counter()
        raw = [fn(j) for j in jobs]
        elapsed = time.perf_counter() - t0
        ordered = tuple(sorted(raw, key=lambda r: int(r["job_id"])))
        return ParallelRunResult(
            n_jobs=len(jobs),
            results=ordered,
            elapsed_seconds=elapsed,
            workers=1,
            parquet_path=None,
        )
