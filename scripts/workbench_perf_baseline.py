#!/usr/bin/env python3
"""CLI: medir baseline de latencia Workbench API (F50).

Arranca un ThreadingHTTPServer loopback efímero, mide endpoints clave,
imprime tabla y sale 0/1 según umbral (default 500ms p95/max).

Uso:
  uv run python scripts/workbench_perf_baseline.py
  uv run python scripts/workbench_perf_baseline.py --samples 40 --json
  uv run python scripts/workbench_perf_baseline.py --threshold-ms 200
"""

from __future__ import annotations

import argparse
import sys
import tempfile
import threading
from pathlib import Path

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.perf_baseline import (
    DEFAULT_P95_THRESHOLD_MS,
    DEFAULT_SAMPLES,
    PERF_ENDPOINTS,
    format_report_table,
    report_to_json,
    run_perf_baseline,
)
from quantlab.workbench.server import create_server
from quantlab.workbench.session import WorkbenchSession


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="QuantLab Workbench API performance baseline (F50)",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=DEFAULT_SAMPLES,
        help=f"samples per endpoint (default {DEFAULT_SAMPLES})",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=3,
        help="warmup GETs discarded per endpoint (default 3)",
    )
    parser.add_argument(
        "--threshold-ms",
        type=float,
        default=DEFAULT_P95_THRESHOLD_MS,
        help=f"p95 and max budget in ms (default {DEFAULT_P95_THRESHOLD_MS:.0f})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print JSON report instead of table",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="optional path to write JSON report",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if LIVE_BLOCKED is not True:
        print("FAIL: LIVE_BLOCKED is not True", file=sys.stderr)
        return 1
    if args.samples < 1:
        print("FAIL: --samples must be >= 1", file=sys.stderr)
        return 1

    root = Path(tempfile.mkdtemp(prefix="quantlab-perf-f50-"))
    session = WorkbenchSession.create_or_load(root, "perf-baseline")
    state = WorkbenchState(session=session)
    state.ensure_session()
    server = create_server(host="127.0.0.1", port=0, state=state)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        report = run_perf_baseline(
            server,
            endpoints=PERF_ENDPOINTS,
            samples=args.samples,
            warmup=args.warmup,
            p95_threshold_ms=float(args.threshold_ms),
            max_threshold_ms=float(args.threshold_ms),
            version=__version__,
            live_blocked=True,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report_to_json(report), encoding="utf-8")

    if args.json:
        sys.stdout.write(report_to_json(report))
    else:
        print(format_report_table(report))

    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
