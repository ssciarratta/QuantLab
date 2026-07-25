"""Paper ledger local (SQLite append-only) — Fase 18.

Persiste fills/órdenes de ``SimulationResult`` para auditoría research.
No envía órdenes; no toca A3 LIVE.
Idempotencia: un experiment_id se registra una sola vez (append-once).

Federación multi-nodo research (TD-03 mitigado):
- cada instancia tiene ``node_id``
- ``experiment_index`` / ``merge_from`` permiten reconciliar shards SQLite
- no es ledger ACID distribuido ni HA cluster (sigue fuera de trading-prod)
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
from quantlab.ledger.federation import ReconcileReport, reconcile_indexes


@dataclass(frozen=True, slots=True)
class PaperLedgerEntry:
    entry_id: int
    experiment_id: str
    kind: str
    payload: dict[str, object]
    recorded_at: datetime


@dataclass(frozen=True, slots=True)
class MergeResult:
    """Resultado de fusionar un shard remoto en el ledger local."""

    imported_experiments: int
    imported_entries: int
    skipped_identical: int


class LocalPaperLedger:
    """Append-once SQLite para resultados de simulación / paper research."""

    def __init__(self, path: Path, *, node_id: str = "local") -> None:
        if not LIVE_BLOCKED:
            raise ValidationError("LocalPaperLedger requiere LIVE_BLOCKED=True")
        require_non_empty_str(node_id, "node_id")
        self._path = path
        self._node_id = node_id
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @property
    def path(self) -> Path:
        return self._path

    @property
    def node_id(self) -> str:
        return self._node_id

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
            conn.execute("CREATE INDEX IF NOT EXISTS idx_paper_exp ON paper_entries(experiment_id)")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS paper_experiments (
                    experiment_id TEXT PRIMARY KEY,
                    payload_sha256 TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    node_id TEXT NOT NULL DEFAULT 'local'
                )
                """
            )
            cols = {
                str(row["name"])
                for row in conn.execute("PRAGMA table_info(paper_experiments)").fetchall()
            }
            if "node_id" not in cols:
                conn.execute(
                    "ALTER TABLE paper_experiments ADD COLUMN node_id TEXT NOT NULL DEFAULT 'local'"
                )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS paper_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                INSERT INTO paper_meta(key, value) VALUES ('node_id', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (self._node_id,),
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
            "equity_end": (str(result.equity_curve[-1].equity) if result.equity_curve else None),
            "node_id": self._node_id,
        }
        digest_src = json.dumps(
            {
                "meta": {
                    "n_orders": meta_payload["n_orders"],
                    "n_fills": meta_payload["n_fills"],
                    "equity_end": meta_payload["equity_end"],
                },
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
                INSERT INTO paper_experiments(
                    experiment_id, payload_sha256, recorded_at, node_id
                )
                VALUES (?, ?, ?, ?)
                """,
                (result.experiment_id, payload_sha, now, self._node_id),
            )
        return rows

    def experiment_index(self) -> dict[str, str]:
        """Mapa experiment_id → payload_sha256 (índice federable)."""
        return _read_experiment_index(self._path)

    def reconcile_with(self, other: LocalPaperLedger | Path) -> ReconcileReport:
        """Compara índices con otro shard (path o ledger)."""
        if isinstance(other, LocalPaperLedger):
            remote = other.experiment_index()
        else:
            remote = _read_experiment_index(Path(other))
        return reconcile_indexes(self.experiment_index(), remote)

    def merge_from(self, source: Path | LocalPaperLedger) -> MergeResult:
        """Importa experiments ausentes desde otro shard SQLite.

        Idempotente si el hash coincide. Conflictos de hash → ValidationError.
        """
        src_path = source.path if isinstance(source, LocalPaperLedger) else Path(source)
        if not src_path.exists():
            raise ValidationError(f"shard fuente inexistente: {src_path}")
        if src_path.resolve() == self._path.resolve():
            raise ValidationError("merge_from: source y target son el mismo path")

        report = self.reconcile_with(src_path)
        if report.conflicts:
            conflict = report.conflicts[0]
            raise ValidationError(
                f"paper ledger merge conflict experiment_id={conflict.experiment_id} "
                f"local={conflict.local_sha256[:12]}… remote={conflict.remote_sha256[:12]}…"
            )

        imported_experiments = 0
        imported_entries = 0
        skipped = len(report.matched)

        with sqlite3.connect(src_path, timeout=30.0) as src, self._connect() as dst:
            src.row_factory = sqlite3.Row
            src_node_default = _read_shard_node_id(src)

            for exp_id in report.only_remote:
                exp = src.execute(
                    """
                    SELECT experiment_id, payload_sha256, recorded_at
                    FROM paper_experiments WHERE experiment_id = ?
                    """,
                    (exp_id,),
                ).fetchone()
                if exp is None:
                    continue
                local = dst.execute(
                    "SELECT payload_sha256 FROM paper_experiments WHERE experiment_id = ?",
                    (exp_id,),
                ).fetchone()
                if local is not None:
                    if str(local["payload_sha256"]) == str(exp["payload_sha256"]):
                        skipped += 1
                        continue
                    raise ValidationError(f"paper ledger merge conflict experiment_id={exp_id}")
                entries = src.execute(
                    """
                    SELECT experiment_id, kind, payload_json, recorded_at
                    FROM paper_entries WHERE experiment_id = ? ORDER BY id ASC
                    """,
                    (exp_id,),
                ).fetchall()
                for entry in entries:
                    dst.execute(
                        """
                        INSERT INTO paper_entries(
                            experiment_id, kind, payload_json, recorded_at
                        ) VALUES (?, ?, ?, ?)
                        """,
                        (
                            str(entry["experiment_id"]),
                            str(entry["kind"]),
                            str(entry["payload_json"]),
                            str(entry["recorded_at"]),
                        ),
                    )
                    imported_entries += 1
                src_node = _experiment_node_id(src, exp_id, default=src_node_default)
                dst.execute(
                    """
                    INSERT INTO paper_experiments(
                        experiment_id, payload_sha256, recorded_at, node_id
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        str(exp["experiment_id"]),
                        str(exp["payload_sha256"]),
                        str(exp["recorded_at"]),
                        src_node,
                    ),
                )
                imported_experiments += 1

        return MergeResult(
            imported_experiments=imported_experiments,
            imported_entries=imported_entries,
            skipped_identical=skipped,
        )

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


def _read_experiment_index(path: Path) -> dict[str, str]:
    if not path.exists():
        raise ValidationError(f"shard inexistente: {path}")
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT experiment_id, payload_sha256 FROM paper_experiments ORDER BY experiment_id"
        ).fetchall()
    except sqlite3.OperationalError as exc:
        raise ValidationError(f"shard sin paper_experiments: {path}") from exc
    finally:
        conn.close()
    return {str(r["experiment_id"]): str(r["payload_sha256"]) for r in rows}


def _read_shard_node_id(conn: sqlite3.Connection) -> str:
    try:
        row = conn.execute("SELECT value FROM paper_meta WHERE key = ?", ("node_id",)).fetchone()
    except sqlite3.OperationalError:
        return "remote"
    if row is None:
        return "remote"
    return str(row["value"] if isinstance(row, sqlite3.Row) else row[0])


def _experiment_node_id(conn: sqlite3.Connection, experiment_id: str, *, default: str) -> str:
    cols = {str(r["name"]) for r in conn.execute("PRAGMA table_info(paper_experiments)")}
    if "node_id" not in cols:
        return default
    row = conn.execute(
        "SELECT node_id FROM paper_experiments WHERE experiment_id = ?",
        (experiment_id,),
    ).fetchone()
    if row is None:
        return default
    value = row["node_id"] if isinstance(row, sqlite3.Row) else row[0]
    if value is None or str(value) == "":
        return default
    return str(value)
