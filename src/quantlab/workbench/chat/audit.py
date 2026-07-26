"""Audit log append-only del chat (chat_audit.jsonl)."""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ChatAuditLog:
    """Append-only JSONL: un evento por línea, sin rewrite."""

    def __init__(self, path: Path | None = None) -> None:
        if path is None:
            root = Path(tempfile.mkdtemp(prefix="ql_wb_chat_audit_"))
            path = root / "chat_audit.jsonl"
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.touch()

    @property
    def path(self) -> Path:
        return self._path

    def append(self, event: dict[str, Any]) -> None:
        payload = dict(event)
        payload.setdefault("ts", datetime.now(UTC).isoformat())
        line = json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n"
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(line)

    def read_all(self) -> list[dict[str, Any]]:
        if not self._path.is_file():
            return []
        rows: list[dict[str, Any]] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rows.append(json.loads(line))
        return rows
