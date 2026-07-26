"""F50 — Performance baseline Workbench API (loopback, in-thread server).

Mide latencia de endpoints clave; assert p95 y max < 500ms local.
"""

from __future__ import annotations

from http.server import ThreadingHTTPServer

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.perf_baseline import (
    DEFAULT_MAX_THRESHOLD_MS,
    DEFAULT_P95_THRESHOLD_MS,
    DEFAULT_SAMPLES,
    PERF_ENDPOINTS,
    assert_baseline_within_budget,
    run_perf_baseline,
)


def test_live_blocked_invariant_f50() -> None:
    assert LIVE_BLOCKED is True


def test_version_and_phases_f50() -> None:
    assert __version__ == "0.89.0"
    assert PHASES_SUMMARY == "F19–F97 INTERNAL"


def test_perf_baseline_key_endpoints_p95(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    """p95 y max de health/mode/commands/about/lab/capabilities < 500ms."""
    assert LIVE_BLOCKED is True
    server, _state = workbench_server
    report = run_perf_baseline(
        server,
        endpoints=PERF_ENDPOINTS,
        samples=DEFAULT_SAMPLES,
        warmup=3,
        p95_threshold_ms=DEFAULT_P95_THRESHOLD_MS,
        max_threshold_ms=DEFAULT_MAX_THRESHOLD_MS,
        version=__version__,
        live_blocked=LIVE_BLOCKED is True,
    )
    assert len(report.endpoints) == len(PERF_ENDPOINTS)
    for ep in report.endpoints:
        assert ep.status_ok, ep.path
        assert ep.p95_ms < DEFAULT_P95_THRESHOLD_MS, (
            f"{ep.path} p95={ep.p95_ms:.2f}ms"
        )
        assert ep.max_ms < DEFAULT_MAX_THRESHOLD_MS, (
            f"{ep.path} max={ep.max_ms:.2f}ms"
        )
    assert_baseline_within_budget(report)
    # Sanity: health is usually the slowest (local ledger smoke) but still << budget.
    by_path = {ep.path: ep for ep in report.endpoints}
    assert by_path["/api/mode"].mean_ms < by_path["/api/health"].mean_ms + 50.0
