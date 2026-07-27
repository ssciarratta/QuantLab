"""Rendimiento y observabilidad del Alpha Scanner (FASE 9)."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from quantlab.core.types.market import Bar
from quantlab.research.alpha.profiles import score_with_profile
from quantlab.research.alpha.scoring import ScoredRow


class ScanCancelled(Exception):
    """Scan cancelado por el caller."""


@dataclass
class CancellationToken:
    _flag: threading.Event = field(default_factory=threading.Event)

    def cancel(self) -> None:
        self._flag.set()

    @property
    def cancelled(self) -> bool:
        return self._flag.is_set()

    def raise_if_cancelled(self) -> None:
        if self.cancelled:
            raise ScanCancelled("scan cancelado")


@dataclass(frozen=True, slots=True)
class ProgressEvent:
    stage: str
    current: int
    total: int
    message: str = ""
    ts_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "current": self.current,
            "total": self.total,
            "message": self.message,
            "ts_ms": self.ts_ms,
            "pct": round(100.0 * self.current / self.total, 2) if self.total else 0.0,
        }


ProgressCallback = Callable[[ProgressEvent], None]


@dataclass
class ScanMetrics:
    started_ms: float
    finished_ms: float | None = None
    n_instruments: int = 0
    n_scored: int = 0
    cache_hit: bool = False
    cancelled: bool = False
    profile: str = ""
    error: str | None = None

    @property
    def duration_ms(self) -> float | None:
        if self.finished_ms is None:
            return None
        return max(0.0, self.finished_ms - self.started_ms)

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_ms": self.started_ms,
            "finished_ms": self.finished_ms,
            "duration_ms": self.duration_ms,
            "n_instruments": self.n_instruments,
            "n_scored": self.n_scored,
            "cache_hit": self.cache_hit,
            "cancelled": self.cancelled,
            "profile": self.profile,
            "error": self.error,
        }


@dataclass
class _CacheEntry:
    expires_at: float
    rows: tuple[ScoredRow, ...]


class ScoreCache:
    """Cache TTL en memoria de resultados score_with_profile (keyed por hash)."""

    def __init__(self, *, ttl_seconds: float = 60.0, max_entries: int = 32) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._lock = threading.Lock()
        self._data: dict[str, _CacheEntry] = {}

    def get(self, key: str) -> tuple[ScoredRow, ...] | None:
        now = time.monotonic()
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            if entry.expires_at < now:
                del self._data[key]
                return None
            return entry.rows

    def put(self, key: str, rows: Sequence[ScoredRow]) -> None:
        now = time.monotonic()
        with self._lock:
            if len(self._data) >= self.max_entries:
                # Evict oldest expiry
                oldest = min(self._data.items(), key=lambda kv: kv[1].expires_at)
                del self._data[oldest[0]]
            self._data[key] = _CacheEntry(
                expires_at=now + self.ttl_seconds,
                rows=tuple(rows),
            )

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


_GLOBAL_CACHE = ScoreCache()


def get_score_cache() -> ScoreCache:
    return _GLOBAL_CACHE


@dataclass(frozen=True, slots=True)
class ObservedScanResult:
    rows: tuple[ScoredRow, ...]
    metrics: ScanMetrics
    progress: tuple[ProgressEvent, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "rows": [r.to_dict() for r in self.rows],
            "metrics": self.metrics.to_dict(),
            "progress": [p.to_dict() for p in self.progress],
        }


def run_observed_profile_scan(
    bars_by_instrument: Mapping[str, Sequence[Bar]],
    profile: str = "legacy_v1",
    *,
    cache_key: str | None = None,
    cache: ScoreCache | None = None,
    token: CancellationToken | None = None,
    on_progress: ProgressCallback | None = None,
    use_cache: bool = True,
) -> ObservedScanResult:
    """Ejecuta score_with_profile con progreso, cancelacion y cache opcional."""
    started = time.time() * 1000.0
    metrics = ScanMetrics(
        started_ms=started,
        n_instruments=len(bars_by_instrument),
        profile=profile,
    )
    events: list[ProgressEvent] = []
    cancel = token or CancellationToken()
    store = cache if cache is not None else get_score_cache()

    def emit(stage: str, current: int, total: int, message: str = "") -> None:
        cancel.raise_if_cancelled()
        ev = ProgressEvent(
            stage=stage,
            current=current,
            total=total,
            message=message,
            ts_ms=time.time() * 1000.0,
        )
        events.append(ev)
        if on_progress is not None:
            on_progress(ev)

    try:
        emit("start", 0, 3, "inicio")
        if use_cache and cache_key:
            hit = store.get(cache_key)
            if hit is not None:
                metrics.cache_hit = True
                metrics.n_scored = len([r for r in hit if not r.excluded])
                metrics.finished_ms = time.time() * 1000.0
                emit("cache_hit", 3, 3, "cache")
                return ObservedScanResult(rows=hit, metrics=metrics, progress=tuple(events))

        emit("score", 1, 3, f"profile={profile}")
        rows = score_with_profile(bars_by_instrument, profile)
        cancel.raise_if_cancelled()
        emit("done", 3, 3, "ok")
        metrics.n_scored = len([r for r in rows if not r.excluded])
        if use_cache and cache_key:
            store.put(cache_key, rows)
        metrics.finished_ms = time.time() * 1000.0
        return ObservedScanResult(rows=rows, metrics=metrics, progress=tuple(events))
    except ScanCancelled:
        metrics.cancelled = True
        metrics.finished_ms = time.time() * 1000.0
        metrics.error = "cancelled"
        events.append(
            ProgressEvent(
                stage="cancelled",
                current=0,
                total=3,
                message="cancelado",
                ts_ms=time.time() * 1000.0,
            )
        )
        raise
    except Exception as exc:
        metrics.error = str(exc)
        metrics.finished_ms = time.time() * 1000.0
        raise


__all__ = [
    "CancellationToken",
    "ObservedScanResult",
    "ProgressEvent",
    "ScanCancelled",
    "ScanMetrics",
    "ScoreCache",
    "get_score_cache",
    "run_observed_profile_scan",
]
