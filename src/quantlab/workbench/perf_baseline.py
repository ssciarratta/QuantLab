"""Performance baseline for key Workbench API endpoints (F50).

Measures loopback HTTP latency against a ThreadingHTTPServer in-process.
Research-safe: no LIVE, no WAN bind, no network egress.
"""

from __future__ import annotations

import http.client
import json
import statistics
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from http.server import ThreadingHTTPServer
from typing import Any

# Local loopback budget — generous vs observed ~0.3–20 ms; catches regressions.
DEFAULT_P95_THRESHOLD_MS = 500.0
DEFAULT_MAX_THRESHOLD_MS = 500.0
DEFAULT_SAMPLES = 25
DEFAULT_WARMUP = 3

# Key read-only surfaces (health does light local sqlite smoke).
PERF_ENDPOINTS: tuple[str, ...] = (
    "/api/health",
    "/api/mode",
    "/api/commands",
    "/api/about",
    "/api/lab/capabilities",
)


@dataclass(frozen=True, slots=True)
class EndpointLatency:
    """Latency sample summary for one path (milliseconds)."""

    path: str
    samples_ms: tuple[float, ...]
    mean_ms: float
    p50_ms: float
    p95_ms: float
    max_ms: float
    min_ms: float
    status_ok: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "n": len(self.samples_ms),
            "mean_ms": round(self.mean_ms, 3),
            "p50_ms": round(self.p50_ms, 3),
            "p95_ms": round(self.p95_ms, 3),
            "max_ms": round(self.max_ms, 3),
            "min_ms": round(self.min_ms, 3),
            "status_ok": self.status_ok,
        }


@dataclass(frozen=True, slots=True)
class PerfBaselineReport:
    """Aggregate baseline across endpoints."""

    endpoints: tuple[EndpointLatency, ...]
    p95_threshold_ms: float
    max_threshold_ms: float
    version: str
    live_blocked: bool

    @property
    def ok(self) -> bool:
        if not self.live_blocked:
            return False
        for ep in self.endpoints:
            if not ep.status_ok:
                return False
            if ep.p95_ms >= self.p95_threshold_ms:
                return False
            if ep.max_ms >= self.max_threshold_ms:
                return False
        return True

    def failures(self) -> list[str]:
        out: list[str] = []
        if not self.live_blocked:
            out.append("LIVE_BLOCKED is not True")
        for ep in self.endpoints:
            if not ep.status_ok:
                out.append(f"{ep.path}: non-200 responses")
            if ep.p95_ms >= self.p95_threshold_ms:
                out.append(
                    f"{ep.path}: p95={ep.p95_ms:.2f}ms >= {self.p95_threshold_ms:.0f}ms"
                )
            if ep.max_ms >= self.max_threshold_ms:
                out.append(
                    f"{ep.path}: max={ep.max_ms:.2f}ms >= {self.max_threshold_ms:.0f}ms"
                )
        return out

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "kind": "perf_baseline",
            "version": self.version,
            "live_blocked": self.live_blocked,
            "p95_threshold_ms": self.p95_threshold_ms,
            "max_threshold_ms": self.max_threshold_ms,
            "endpoints": [ep.to_dict() for ep in self.endpoints],
            "failures": self.failures(),
        }


def percentile(sorted_samples: Sequence[float], pct: float) -> float:
    """Linear-index percentile on a pre-sorted ascending sequence (ms)."""
    if not sorted_samples:
        raise ValueError("empty samples")
    if pct <= 0:
        return float(sorted_samples[0])
    if pct >= 100:
        return float(sorted_samples[-1])
    n = len(sorted_samples)
    idx = min(n - 1, max(0, int(round((pct / 100.0) * (n - 1)))))
    return float(sorted_samples[idx])


def _server_addr(server: ThreadingHTTPServer) -> tuple[str, int]:
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    return host, port


def _timed_get(host: str, port: int, path: str, *, timeout: float = 30.0) -> tuple[int, float]:
    conn = http.client.HTTPConnection(host, port, timeout=timeout)
    try:
        t0 = time.perf_counter()
        conn.request("GET", path)
        resp = conn.getresponse()
        _ = resp.read()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return resp.status, elapsed_ms
    finally:
        conn.close()


def measure_endpoint(
    server: ThreadingHTTPServer,
    path: str,
    *,
    samples: int = DEFAULT_SAMPLES,
    warmup: int = DEFAULT_WARMUP,
    timeout: float = 30.0,
) -> EndpointLatency:
    """Measure GET latency for ``path`` against a running workbench server."""
    if samples < 1:
        raise ValueError("samples must be >= 1")
    host, port = _server_addr(server)
    for _ in range(max(0, warmup)):
        status, _ms = _timed_get(host, port, path, timeout=timeout)
        if status != 200:
            raise RuntimeError(f"warmup {path} returned HTTP {status}")

    times: list[float] = []
    status_ok = True
    for _ in range(samples):
        status, ms = _timed_get(host, port, path, timeout=timeout)
        if status != 200:
            status_ok = False
        times.append(ms)

    ordered = tuple(sorted(times))
    return EndpointLatency(
        path=path,
        samples_ms=ordered,
        mean_ms=float(statistics.fmean(ordered)),
        p50_ms=percentile(ordered, 50),
        p95_ms=percentile(ordered, 95),
        max_ms=float(ordered[-1]),
        min_ms=float(ordered[0]),
        status_ok=status_ok,
    )


def run_perf_baseline(
    server: ThreadingHTTPServer,
    *,
    endpoints: Sequence[str] = PERF_ENDPOINTS,
    samples: int = DEFAULT_SAMPLES,
    warmup: int = DEFAULT_WARMUP,
    p95_threshold_ms: float = DEFAULT_P95_THRESHOLD_MS,
    max_threshold_ms: float = DEFAULT_MAX_THRESHOLD_MS,
    version: str = "",
    live_blocked: bool = True,
) -> PerfBaselineReport:
    """Run baseline for all endpoints; returns structured report."""
    measured: list[EndpointLatency] = []
    for path in endpoints:
        measured.append(
            measure_endpoint(
                server,
                path,
                samples=samples,
                warmup=warmup,
            )
        )
    return PerfBaselineReport(
        endpoints=tuple(measured),
        p95_threshold_ms=p95_threshold_ms,
        max_threshold_ms=max_threshold_ms,
        version=version,
        live_blocked=live_blocked,
    )


def format_report_table(report: PerfBaselineReport) -> str:
    """Human-readable latency table."""
    lines = [
        f"QuantLab perf baseline v{report.version} · live_blocked={report.live_blocked}",
        (
            f"thresholds: p95 < {report.p95_threshold_ms:.0f}ms"
            f" · max < {report.max_threshold_ms:.0f}ms"
        ),
        f"{'path':<28} {'mean':>8} {'p50':>8} {'p95':>8} {'max':>8} {'min':>8}",
        "-" * 72,
    ]
    for ep in report.endpoints:
        lines.append(
            f"{ep.path:<28} {ep.mean_ms:8.2f} {ep.p50_ms:8.2f} "
            f"{ep.p95_ms:8.2f} {ep.max_ms:8.2f} {ep.min_ms:8.2f}"
        )
    lines.append("-" * 72)
    lines.append("PASS" if report.ok else "FAIL: " + "; ".join(report.failures()))
    return "\n".join(lines)


def report_to_json(report: PerfBaselineReport) -> str:
    return json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"


def assert_baseline_within_budget(
    report: PerfBaselineReport,
    *,
    extra: Mapping[str, Any] | None = None,
) -> None:
    """Raise AssertionError if any endpoint breaches thresholds."""
    _ = extra
    if not report.ok:
        detail = "; ".join(report.failures()) or "unknown"
        raise AssertionError(f"perf baseline failed: {detail}\n{format_report_table(report)}")
