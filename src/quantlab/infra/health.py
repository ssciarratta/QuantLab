"""Health check research-prod — Fase 18. Sin probes LIVE."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED, LIVE_ROUTING_BLOCKED_MSG
from quantlab.infra.ops_metrics import get_ops_metrics


@dataclass(frozen=True, slots=True)
class HealthReport:
    ok: bool
    version: str
    live_blocked: bool
    checks: tuple[tuple[str, bool, str], ...]
    ops_counters: dict[str, int]
    checked_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "version": self.version,
            "live_blocked": self.live_blocked,
            "checks": [
                {"name": n, "ok": o, "detail": d} for n, o, d in self.checks
            ],
            "ops_counters": self.ops_counters,
            "checked_at": self.checked_at.isoformat(),
        }


def run_health_checks() -> HealthReport:
    """Verifica invariantes research-prod locales."""
    checks: list[tuple[str, bool, str]] = []

    live_ok = LIVE_BLOCKED is True
    checks.append(
        (
            "live_gate",
            live_ok,
            LIVE_ROUTING_BLOCKED_MSG if live_ok else "LIVE_BLOCKED is False — PELIGRO",
        )
    )

    try:
        from quantlab.execution import NullRouter

        checks.append(("null_router_import", True, NullRouter.__name__))
    except Exception as exc:  # noqa: BLE001 — health must not crash
        checks.append(("null_router_import", False, str(exc)))

    try:
        from quantlab.ledger import LocalPaperLedger

        checks.append(("paper_ledger_import", True, LocalPaperLedger.__name__))
    except Exception as exc:  # noqa: BLE001
        checks.append(("paper_ledger_import", False, str(exc)))

    ops = dict(get_ops_metrics().snapshot().counters)
    ok = all(c[1] for c in checks)
    return HealthReport(
        ok=ok,
        version=__version__,
        live_blocked=LIVE_BLOCKED,
        checks=tuple(checks),
        ops_counters=ops,
        checked_at=datetime.now(tz=UTC),
    )


def export_ops_snapshot(path: Path) -> Path:
    """Escribe snapshot JSON de ops metrics + health."""
    report = run_health_checks()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    report = run_health_checks()
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
