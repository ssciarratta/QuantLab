"""Activity log append-only de sesión (activity.jsonl) — F41.

Eventos: connect, submit, backtest, optimize, export, error.
Sin flip LIVE · sin place_order venue.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED

ACTIVITY_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "connect",
        "submit",
        "backtest",
        "optimize",
        "export",
        "error",
    }
)

DEFAULT_ACTIVITY_LIMIT = 100
MAX_ACTIVITY_LIMIT = 500


def validate_event_type(event: str) -> str:
    """Fail-closed: solo tipos allowlist."""
    key = str(event or "").strip().lower()
    if key not in ACTIVITY_EVENT_TYPES:
        known = ", ".join(sorted(ACTIVITY_EVENT_TYPES))
        raise ValidationError(f"activity event desconocido: {event!r} (válidos: {known})")
    return key


def clamp_limit(limit: int | None) -> int:
    """Limita lecturas; default 100, max 500."""
    if limit is None:
        return DEFAULT_ACTIVITY_LIMIT
    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValidationError("limit debe ser int")
    if limit < 1:
        raise ValidationError("limit debe ser >= 1")
    return min(limit, MAX_ACTIVITY_LIMIT)


class ActivityLog:
    """Append-only JSONL: un evento por línea, sin rewrite."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.touch()

    @property
    def path(self) -> Path:
        return self._path

    def append(
        self,
        event: str,
        *,
        ok: bool = True,
        message: str = "",
        detail: dict[str, Any] | None = None,
        op: str | None = None,
    ) -> dict[str, Any]:
        """Append evento; retorna el registro escrito."""
        kind = validate_event_type(event)
        payload: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(),
            "event": kind,
            "ok": bool(ok),
            "message": str(message or ""),
            "live_blocked": LIVE_BLOCKED is True,
        }
        if op:
            payload["op"] = str(op)
        if detail:
            # Solo tipos JSON-safe simples.
            clean: dict[str, Any] = {}
            for key, value in detail.items():
                if isinstance(value, (str, int, float, bool)) or value is None:
                    clean[str(key)] = value
                else:
                    clean[str(key)] = str(value)
            payload["detail"] = clean
        line = json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n"
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(line)
        return payload

    def read_tail(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Lee últimos ``limit`` eventos (más recientes al final)."""
        n = clamp_limit(limit)
        if not self._path.is_file():
            return []
        rows: list[dict[str, Any]] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
        if len(rows) > n:
            return rows[-n:]
        return rows


def list_activity(path: Path, *, limit: int | None = None) -> dict[str, Any]:
    """Payload API: últimos eventos de ``activity.jsonl``."""
    log = ActivityLog(path)
    events = log.read_tail(limit)
    return {
        "ok": True,
        "kind": "activity",
        "count": len(events),
        "limit": clamp_limit(limit),
        "events": events,
        "event_types": sorted(ACTIVITY_EVENT_TYPES),
        "path": str(path),
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }
