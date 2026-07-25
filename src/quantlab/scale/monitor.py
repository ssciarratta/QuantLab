"""Monitoring de corridas masivas (Fase 17) — thread-safe real."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MonitorSnapshot:
    total: int
    completed: int
    failed: int
    elapsed_seconds: float
    throughput_per_sec: float
    pct: float


class ProgressMonitor:
    """Contador thread-safe para batch jobs."""

    def __init__(self, total: int) -> None:
        if total < 0:
            raise ValueError("total debe ser >= 0")
        self._total = total
        self._completed = 0
        self._failed = 0
        self._t0 = time.perf_counter()
        self._lock = threading.Lock()

    def tick(self, *, ok: bool = True, n: int = 1) -> None:
        if n < 1:
            raise ValueError("n debe ser >= 1")
        with self._lock:
            if ok:
                self._completed += n
            else:
                self._failed += n

    def snapshot(self) -> MonitorSnapshot:
        with self._lock:
            completed = self._completed
            failed = self._failed
        elapsed = max(time.perf_counter() - self._t0, 1e-9)
        done = completed + failed
        pct = (100.0 * done / self._total) if self._total else 100.0
        return MonitorSnapshot(
            total=self._total,
            completed=completed,
            failed=failed,
            elapsed_seconds=elapsed,
            throughput_per_sec=done / elapsed,
            pct=min(pct, 100.0),
        )
