"""Contadores ops in-process (H7 research-prod). Sin exporter externo."""

from __future__ import annotations

import threading
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OpsSnapshot:
    counters: Mapping[str, int]


class OpsMetrics:
    """Registro thread-safe de contadores (proceso local)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, int] = {}

    def inc(self, name: str, n: int = 1) -> None:
        if not name or n < 0:
            return
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + n

    def get(self, name: str) -> int:
        with self._lock:
            return self._counters.get(name, 0)

    def snapshot(self) -> OpsSnapshot:
        with self._lock:
            return OpsSnapshot(counters=dict(sorted(self._counters.items())))

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()


_GLOBAL = OpsMetrics()


def get_ops_metrics() -> OpsMetrics:
    return _GLOBAL
