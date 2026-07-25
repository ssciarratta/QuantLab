"""Paper ledger local (SQLite append-only) — Fase 18.

Persiste fills/órdenes de ``SimulationResult`` para auditoría research.
No envía órdenes; no toca A3 LIVE.
Idempotencia: un experiment_id se registra una sola vez (append-once).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.results import SimulationResult
from quantlab.core.types.serialization import dataclass_to_dict
from quantlab.core.types.validation import require_non_empty_str
from quantlab.execution.live_gate import LIVE_BLOCKED


@dataclass(frozen=True, slots=True)
class PaperLedgerEntry:
    entry_id: int
    experiment_id: str
    kind: str
    payload: dict[str, object]
    recorded_at: datetime


class LocalPaperLedger:
    """Append-once SQLite para resultados de simulación / paper research."""

    def __init__(self, path: Path) -> None:
        if not LIVE_BLOCKED:
            raise ValidationError("LocalPaperLedger requiere LIVE_BLOCKED=True")
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS paper_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    recorded_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_paper_exp ON paper_entries(experiment_id)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS paper_experiments (
                    experiment_id TEXT PRIMARY KEY,
                    payload_sha256 TEXT NOT NULL,
                    recorded_at TEXT NOT NULL
                )
                """
            )

    def append_simulation(self, result: SimulationResult) -> int:
        """Registra snapshot de fills + orders + equity final.

        Idempotente: si ``experiment_id`` ya existe con el mismo hash → 0.
        Si existe con hash distinto → ValidationError.
        """
        require_non_empty_str(result.experiment_id, "experiment_id")
        now = datetime.now(tz=UTC).isoformat()
        meta_payload = {
            "n_orders": len(result.orders),
            "n_fills": len(result.fills),
            "equity_end": (
                str(result.equity_curve[-1].equity) if result.equity_curve else None
            ),
        }
        digest_src = json.dumps(
            {
                "meta": meta_payload,
                "orders": [dataclass_to_dict(o) for o in result.orders],
                "fills": [dataclass_to_dict(f) for f in result.fills],
            },
            sort_keys=True,
            default=str,
        )
        payload_sha = hashlib.sha256(digest_src.encode("utf-8")).hexdigest()

        with self._connect() as conn:
            existing = conn.execute(
                "SELECT payload_sha256 FROM paper_experiments WHERE experiment_id = ?",
                (result.experiment_id,),
            ).fetchone()
            if existing is not None:
                if str(existing["payload_sha256"]) == payload_sha:
                    return 0
                raise ValidationError(
                    f"paper ledger: experiment_id ya registrado con otro payload: "
                    f"{result.experiment_id}"
                )

            rows = 0
            for order in result.orders:
                conn.execute(
                    """
                    INSERT INTO paper_entries(experiment_id, kind, payload_json, recorded_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        result.experiment_id,
                        "order",
                        json.dumps(dataclass_to_dict(order), sort_keys=True, default=str),
                        now,
                    ),
                )
                rows += 1
            for fill in result.fills:
                conn.execute(
                    """
                    INSERT INTO paper_entries(experiment_id, kind, payload_json, recorded_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        result.experiment_id,
                        "fill",
                        json.dumps(dataclass_to_dict(fill), sort_keys=True, default=str),
                        now,
                    ),
                )
                rows += 1
            if result.equity_curve:
                eq = result.equity_curve[-1]
                conn.execute(
                    """
                    INSERT INTO paper_entries(experiment_id, kind, payload_json, recorded_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        result.experiment_id,
                        "equity_end",
                        json.dumps(
                            {"timestamp": eq.timestamp.isoformat(), "equity": str(eq.equity)},
                            sort_keys=True,
                        ),
                        now,
                    ),
                )
                rows += 1
            meta_payload["payload_sha256"] = payload_sha
            conn.execute(
                """
                INSERT INTO paper_entries(experiment_id, kind, payload_json, recorded_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    result.experiment_id,
                    "simulation_meta",
                    json.dumps(meta_payload, sort_keys=True),
                    now,
                ),
            )
            rows += 1
            conn.execute(
                """
                INSERT INTO paper_experiments(experiment_id, payload_sha256, recorded_at)
                VALUES (?, ?, ?)
                """,
                (result.experiment_id, payload_sha, now),
            )
        return rows

    def list_entries(self, experiment_id: str) -> tuple[PaperLedgerEntry, ...]:
        require_non_empty_str(experiment_id, "experiment_id")
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, experiment_id, kind, payload_json, recorded_at
                FROM paper_entries
                WHERE experiment_id = ?
                ORDER BY id ASC
                """,
                (experiment_id,),
            ).fetchall()
        out: list[PaperLedgerEntry] = []
        for row in rows:
            payload = json.loads(row["payload_json"])
            if not isinstance(payload, dict):
                payload = {"raw": payload}
            out.append(
                PaperLedgerEntry(
                    entry_id=int(row["id"]),
                    experiment_id=str(row["experiment_id"]),
                    kind=str(row["kind"]),
                    payload=payload,
                    recorded_at=datetime.fromisoformat(str(row["recorded_at"])),
                )
            )
        return tuple(out)

    def count(self, experiment_id: str | None = None) -> int:
        with self._connect() as conn:
            if experiment_id is None:
                row = conn.execute("SELECT COUNT(*) AS c FROM paper_entries").fetchone()
            else:
                row = conn.execute(
                    "SELECT COUNT(*) AS c FROM paper_entries WHERE experiment_id = ?",
                    (experiment_id,),
                ).fetchone()
        return int(row["c"]) if row is not None else 0
