"""Contadores ops in-process (H7 research-prod) + export Prometheus text."""

from __future__ import annotations

import re
import threading
from collections.abc import Mapping
from dataclasses import dataclass

_PROM_NAME_RE = re.compile(r"[^a-zA-Z0-9_:]")


@dataclass(frozen=True, slots=True)
class OpsSnapshot:
    counters: Mapping[str, int]


def _prom_metric_name(name: str) -> str:
    cleaned = _PROM_NAME_RE.sub("_", name.strip())
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"ql_{cleaned}"
    return cleaned


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

    def render_prometheus_text(self) -> str:
        """Export text/plain Prometheus (counters → ``TYPE counter``)."""
        snap = self.snapshot()
        lines: list[str] = []
        for raw_name, value in snap.counters.items():
            metric = _prom_metric_name(raw_name)
            lines.append(f"# HELP {metric} QuantLab ops counter ({raw_name})")
            lines.append(f"# TYPE {metric} counter")
            lines.append(f"{metric} {int(value)}")
        return "\n".join(lines) + ("\n" if lines else "")


_GLOBAL = OpsMetrics()


def get_ops_metrics() -> OpsMetrics:
    return _GLOBAL


def render_prometheus_text() -> str:
    """Atajo sobre el registro global."""
    return get_ops_metrics().render_prometheus_text()
