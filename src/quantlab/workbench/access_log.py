"""HTTP access log append-only de sesión (access.jsonl) — F61.

Campos por línea: method, path, status, ms (+ ts, live_blocked).
Sin bodies / headers / secrets. Toggle vía settings.access_log (default true).
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED

DEFAULT_ACCESS_LIMIT = 100
MAX_ACCESS_LIMIT = 500
MAX_PATH_LEN = 512

_METHOD_RE = re.compile(r"^[A-Z]{1,16}$")


def clamp_limit(limit: int | None) -> int:
    """Limita lecturas; default 100, max 500."""
    if limit is None:
        return DEFAULT_ACCESS_LIMIT
    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValidationError("limit debe ser int")
    if limit < 1:
        raise ValidationError("limit debe ser >= 1")
    return min(limit, MAX_ACCESS_LIMIT)


def sanitize_path(path: str) -> str:
    """Path sin query/fragment; acotado; sin bodies/secrets."""
    raw = str(path or "").strip() or "/"
    # Solo path: descartar query/fragment si llegaran pegados.
    for sep in ("?", "#"):
        if sep in raw:
            raw = raw.split(sep, 1)[0]
    if not raw.startswith("/"):
        raw = "/" + raw
    # Conservar ASCII imprimible seguro para rutas HTTP.
    safe = "".join(
        ch if ch.isascii() and (ch.isalnum() or ch in "/._~-") else "_" for ch in raw
    )
    if not safe.startswith("/"):
        safe = "/" + safe
    if len(safe) > MAX_PATH_LEN:
        safe = safe[:MAX_PATH_LEN]
    return safe or "/"


def sanitize_method(method: str) -> str:
    """HTTP method allowlist-ish (uppercase corto)."""
    key = str(method or "GET").strip().upper()
    if not _METHOD_RE.fullmatch(key):
        return "GET"
    return key


class AccessLog:
    """Append-only JSONL: un request por línea, sin rewrite."""

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
        method: str,
        path: str,
        status: int,
        ms: float,
    ) -> dict[str, Any]:
        """Append request metadata; retorna el registro escrito."""
        try:
            status_i = int(status)
        except (TypeError, ValueError):
            status_i = 0
        try:
            ms_f = round(float(ms), 3)
        except (TypeError, ValueError):
            ms_f = 0.0
        if ms_f < 0:
            ms_f = 0.0
        # Solo metadata de request: nunca body / headers / secrets.
        payload: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(),
            "method": sanitize_method(method),
            "path": sanitize_path(path),
            "status": status_i,
            "ms": ms_f,
            "live_blocked": LIVE_BLOCKED is True,
        }
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


def list_access_log(path: Path, *, limit: int | None = None) -> dict[str, Any]:
    """Payload API: últimos eventos de ``access.jsonl``."""
    log = AccessLog(path)
    events = log.read_tail(limit)
    return {
        "ok": True,
        "kind": "access_log",
        "count": len(events),
        "limit": clamp_limit(limit),
        "events": events,
        "fields": ["ts", "method", "path", "status", "ms", "live_blocked"],
        "path": str(path),
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }
