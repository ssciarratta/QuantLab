"""Equity curve append-only de sesión (equity.jsonl) — F66.

Puntos: ``{ts, equity, cash}`` tras fills paper / paper session step.
Sin flip LIVE · sin place_order venue.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED

DEFAULT_EQUITY_LIMIT = 200
MAX_EQUITY_LIMIT = 2000


def clamp_equity_limit(limit: int | None) -> int:
    """Limita lecturas; default 200, max 2000."""
    if limit is None:
        return DEFAULT_EQUITY_LIMIT
    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValidationError("limit debe ser int")
    if limit < 1:
        raise ValidationError("limit debe ser >= 1")
    return min(limit, MAX_EQUITY_LIMIT)


def _as_str_decimal(value: Decimal | str | int | float | None) -> str:
    if value is None:
        return "0"
    if isinstance(value, Decimal):
        return str(value)
    return str(Decimal(str(value)))


class EquityCurveLog:
    """Append-only JSONL: un punto ``{ts, equity, cash}`` por línea."""

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
        *,
        equity: Decimal | str | int | float,
        cash: Decimal | str | int | float,
        ts: datetime | None = None,
    ) -> dict[str, Any]:
        """Append punto; retorna el registro escrito."""
        when = ts if ts is not None else datetime.now(UTC)
        if when.tzinfo is None:
            when = when.replace(tzinfo=UTC)
        payload: dict[str, Any] = {
            "ts": when.isoformat(),
            "equity": _as_str_decimal(equity),
            "cash": _as_str_decimal(cash),
        }
        line = json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n"
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())
        return payload

    def read_tail(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Lee últimos ``limit`` puntos (más recientes al final)."""
        n = clamp_equity_limit(limit)
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
            if not isinstance(row, dict):
                continue
            if "ts" not in row or "equity" not in row or "cash" not in row:
                continue
            rows.append(
                {
                    "ts": str(row["ts"]),
                    "equity": str(row["equity"]),
                    "cash": str(row["cash"]),
                }
            )
        if len(rows) > n:
            return rows[-n:]
        return rows


def list_equity(path: Path, *, limit: int | None = None) -> dict[str, Any]:
    """Payload API: últimos puntos de ``equity.jsonl``."""
    log = EquityCurveLog(path)
    points = log.read_tail(limit)
    return {
        "ok": True,
        "kind": "equity",
        "count": len(points),
        "limit": clamp_equity_limit(limit),
        "points": points,
        "path": str(path),
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }
