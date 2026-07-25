"""CRUD de experimentos + vinculación artifacts (Fase 9)."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import ExperimentStatus
from quantlab.core.types.validation import require_non_empty_str
from quantlab.data.atomic_io import atomic_write_text


@dataclass(frozen=True, slots=True)
class ExperimentRecord:
    experiment_id: str
    status: ExperimentStatus
    dataset_id: str
    strategy_version: str
    created_at: datetime
    updated_at: datetime
    artifact_paths: tuple[str, ...]
    metadata: dict[str, Any]


class ExperimentRegistry:
    """Registry SQLite + sidecars JSON atómicos."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._sidecar = self._path.parent / f"{self._path.stem}_records"
        self._sidecar.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS experiments (
                    experiment_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    dataset_id TEXT NOT NULL,
                    strategy_version TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    artifact_paths_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def create(
        self,
        *,
        experiment_id: str,
        dataset_id: str,
        strategy_version: str,
        metadata: dict[str, Any] | None = None,
    ) -> ExperimentRecord:
        require_non_empty_str(experiment_id, "experiment_id")
        require_non_empty_str(dataset_id, "dataset_id")
        require_non_empty_str(strategy_version, "strategy_version")
        if self.get(experiment_id) is not None:
            raise ValidationError(f"experiment ya existe: {experiment_id}")
        now = datetime.now(tz=UTC)
        rec = ExperimentRecord(
            experiment_id=experiment_id,
            status=ExperimentStatus.DRAFT,
            dataset_id=dataset_id,
            strategy_version=strategy_version,
            created_at=now,
            updated_at=now,
            artifact_paths=(),
            metadata=dict(metadata or {}),
        )
        self._upsert(rec)
        return rec

    def get(self, experiment_id: str) -> ExperimentRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM experiments WHERE experiment_id = ?", (experiment_id,)
            ).fetchone()
        if row is None:
            return None
        return self._row(row)

    def list(self, *, status: ExperimentStatus | None = None) -> list[ExperimentRecord]:
        with self._connect() as conn:
            if status is None:
                rows = conn.execute(
                    "SELECT * FROM experiments ORDER BY created_at DESC"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM experiments WHERE status = ? ORDER BY created_at DESC",
                    (status.value,),
                ).fetchall()
        return [self._row(r) for r in rows]

    def set_status(self, experiment_id: str, status: ExperimentStatus) -> ExperimentRecord:
        rec = self.get(experiment_id)
        if rec is None:
            raise ValidationError(f"experiment no encontrado: {experiment_id}")
        updated = ExperimentRecord(
            experiment_id=rec.experiment_id,
            status=status,
            dataset_id=rec.dataset_id,
            strategy_version=rec.strategy_version,
            created_at=rec.created_at,
            updated_at=datetime.now(tz=UTC),
            artifact_paths=rec.artifact_paths,
            metadata=rec.metadata,
        )
        self._upsert(updated)
        return updated

    def link_artifact(self, experiment_id: str, path: str) -> ExperimentRecord:
        require_non_empty_str(path, "path")
        rec = self.get(experiment_id)
        if rec is None:
            raise ValidationError(f"experiment no encontrado: {experiment_id}")
        paths = tuple(dict.fromkeys([*rec.artifact_paths, path]))
        updated = ExperimentRecord(
            experiment_id=rec.experiment_id,
            status=rec.status,
            dataset_id=rec.dataset_id,
            strategy_version=rec.strategy_version,
            created_at=rec.created_at,
            updated_at=datetime.now(tz=UTC),
            artifact_paths=paths,
            metadata=rec.metadata,
        )
        self._upsert(updated)
        return updated

    def _upsert(self, rec: ExperimentRecord) -> None:
        payload = {
            "experiment_id": rec.experiment_id,
            "status": rec.status.value,
            "dataset_id": rec.dataset_id,
            "strategy_version": rec.strategy_version,
            "created_at": rec.created_at.isoformat(),
            "updated_at": rec.updated_at.isoformat(),
            "artifact_paths": list(rec.artifact_paths),
            "metadata": rec.metadata,
        }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO experiments
                (experiment_id, status, dataset_id, strategy_version, created_at, updated_at,
                 artifact_paths_json, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec.experiment_id,
                    rec.status.value,
                    rec.dataset_id,
                    rec.strategy_version,
                    rec.created_at.isoformat(),
                    rec.updated_at.isoformat(),
                    json.dumps(list(rec.artifact_paths)),
                    json.dumps(rec.metadata, sort_keys=True),
                ),
            )
            conn.commit()
        atomic_write_text(
            self._sidecar / f"{rec.experiment_id}.json",
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
        )

    @staticmethod
    def _row(row: sqlite3.Row) -> ExperimentRecord:
        return ExperimentRecord(
            experiment_id=row["experiment_id"],
            status=ExperimentStatus(row["status"]),
            dataset_id=row["dataset_id"],
            strategy_version=row["strategy_version"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            artifact_paths=tuple(json.loads(row["artifact_paths_json"])),
            metadata=json.loads(row["metadata_json"]),
        )
