#!/usr/bin/env python3
"""Ejecuta las lanes de certificación read-only A3 y emite JSON saneado."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from quantlab import __version__
from quantlab.brokers.a3.read_contract import (
    A3ReadContractStatus,
    run_fake_read_contract,
    run_sandbox_read_contract_from_env,
)
from quantlab.execution.live_gate import LIVE_BLOCKED

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "reports" / "certification" / "a3-md-cert.json"
_A3_ENV_NAMES = (
    "QUANTLAB_RUN_A3_SANDBOX_CERT",
    "QUANTLAB_A3_MD_READONLY",
    "QUANTLAB_A3_ENVIRONMENT",
    "QUANTLAB_A3_USER",
    "QUANTLAB_A3_PASSWORD",
    "QUANTLAB_A3_ACCOUNT",
    "QUANTLAB_A3_TOKEN",
)
_SAFE_PROCESS_ENV_NAMES = (
    "PATH",
    "VIRTUAL_ENV",
    "SSL_CERT_FILE",
    "REQUESTS_CA_BUNDLE",
    "LANG",
    "LC_ALL",
)


def _sanitized_worker_env() -> dict[str, str]:
    env = {
        name: value
        for name in (*_SAFE_PROCESS_ENV_NAMES, *_A3_ENV_NAMES)
        if (value := os.environ.get(name)) is not None
    }
    env["PYTHONPATH"] = str(ROOT / "src")
    env["PYTHONUNBUFFERED"] = "1"
    return env


def _sandbox_failure(issue: str) -> dict[str, object]:
    raw_environment = os.environ.get("QUANTLAB_A3_ENVIRONMENT", "simulation").strip().lower()
    environment = raw_environment if raw_environment in {"simulation", "production"} else "invalid"
    return {
        "status": A3ReadContractStatus.FAIL.value,
        "lane": "sandbox",
        "provider": "pyRofex",
        "environment": environment,
        "instruments_count": 0,
        "snapshots_count": 0,
        "latency_ms": {"count": 0, "min": 0.0, "max": 0.0, "mean": 0.0},
        "live_blocked": LIVE_BLOCKED,
        "write_calls": 0,
        "issues": [issue],
    }


def _run_sandbox_subprocess(timeout: float) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="quantlab-a3-cert-") as tmp:
        worker_output = Path(tmp) / "sandbox.json"
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker-sandbox-output",
            str(worker_output),
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                env=_sanitized_worker_env(),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return _sandbox_failure("sandbox_timeout")

        if completed.returncode != 0 or not worker_output.is_file():
            return _sandbox_failure("sandbox_worker_failed")
        try:
            payload: Any = json.loads(worker_output.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return _sandbox_failure("sandbox_worker_report_invalid")
        if not isinstance(payload, dict) or payload.get("lane") != "sandbox":
            return _sandbox_failure("sandbox_worker_report_invalid")
        return payload


def _write_payload(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _worker(output: Path) -> int:
    report = run_sandbox_read_contract_from_env()
    _write_payload(output, report.to_dict())
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Certifica el contrato MD read-only A3")
    parser.add_argument("--lane", choices=("fake", "sandbox", "all"), default="all")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--worker-sandbox-output", type=Path, help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.worker_sandbox_output is not None:
        return _worker(args.worker_sandbox_output)
    if args.timeout <= 0:
        raise SystemExit("--timeout debe ser mayor que cero")

    lanes: list[dict[str, object]] = []
    if args.lane in {"fake", "all"}:
        lanes.append(run_fake_read_contract().to_dict())
    if args.lane in {"sandbox", "all"}:
        lanes.append(_run_sandbox_subprocess(args.timeout))

    payload: dict[str, object] = {
        "schema_version": 1,
        "phase": 89,
        "quantlab_version": __version__,
        "live_blocked": LIVE_BLOCKED,
        "lanes": lanes,
    }
    _write_payload(args.output, payload)

    statuses = {str(lane["lane"]): str(lane["status"]) for lane in lanes}
    if (
        args.lane == "sandbox"
        and statuses.get("sandbox") == A3ReadContractStatus.SKIPPED_NOT_REQUESTED
    ):
        return 2
    if any(status == A3ReadContractStatus.FAIL for status in statuses.values()):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
