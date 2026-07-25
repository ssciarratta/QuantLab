"""Catálogo local SQLite de datasets."""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from quantlab.core.types.manifests import DatasetManifest
from quantlab.data.atomic_io import atomic_write_text
from quantlab.data.catalog.protocols import CatalogBackend, CatalogEntry

_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")

# Re-export para imports legacy `from ...catalog import CatalogEntry`
__all__ = ["CatalogEntry", "DataCatalog", "SqliteCatalogBackend"]


class SqliteCatalogBackend:
    """Backend SQLite del catálogo (+ sidecar JSON atómico por dataset)."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._sidecar_root = self._path.parent / f"{self._path.stem}_sidecars"
        self._sidecar_root.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS datasets (
                    dataset_id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    symbol TEXT,
                    timeframe TEXT,
                    created_at TEXT NOT NULL,
                    manifest_json TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def _row_to_entry(self, row: sqlite3.Row) -> CatalogEntry:
        return CatalogEntry(
            dataset_id=row["dataset_id"],
            kind=row["kind"],
            provider=row["provider"],
            symbol=row["symbol"],
            timeframe=row["timeframe"],
            manifest=json.loads(row["manifest_json"]),
        )

    def upsert_dataset(self, manifest: DatasetManifest, *, kind: str, provider: str) -> None:
        symbol = manifest.instruments[0] if manifest.instruments else None
        payload = json.dumps(manifest.to_dict(), ensure_ascii=False, sort_keys=True)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO datasets
                (dataset_id, kind, provider, symbol, timeframe, created_at, manifest_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    manifest.dataset_id,
                    kind,
                    provider,
                    symbol,
                    manifest.granularity,
                    manifest.created_at.isoformat(),
                    payload,
                ),
            )
            conn.commit()
        # Sidecar atómico: facilita migración/inspección sin tocar SQLite
        sidecar = self._sidecar_root / f"{manifest.dataset_id}.json"
        atomic_write_text(sidecar, payload + "\n")

    def get_dataset(self, dataset_id: str) -> CatalogEntry | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM datasets WHERE dataset_id = ?", (dataset_id,)
            ).fetchone()
        if row is None:
            return None
        return self._row_to_entry(row)

    def list_datasets(
        self,
        *,
        provider: str | None = None,
        kind: str | None = None,
        symbol: str | None = None,
    ) -> list[CatalogEntry]:
        clauses: list[str] = []
        params: list[str] = []
        if provider:
            clauses.append("provider = ?")
            params.append(provider)
        if kind:
            clauses.append("kind = ?")
            params.append(kind)
        if symbol:
            clauses.append("symbol = ?")
            params.append(symbol)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM datasets{where} ORDER BY created_at DESC",
                params,
            ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def find_latest(self, *, provider: str, symbol: str, timeframe: str) -> CatalogEntry | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM datasets
                WHERE provider = ? AND symbol = ? AND timeframe = ?
                ORDER BY created_at DESC LIMIT 1
                """,
                (provider, symbol, timeframe),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_entry(row)

    def verify_dataset(self, dataset_id: str) -> bool:
        entry = self.get_dataset(dataset_id)
        if entry is None:
            return False
        checksum = entry.manifest.get("checksum")
        return isinstance(checksum, str) and bool(_SHA256_RE.fullmatch(checksum))


class DataCatalog:
    """Fachada del catálogo: delega en un CatalogBackend inyectable."""

    def __init__(self, path: Path, *, backend: CatalogBackend | None = None) -> None:
        self._path = path
        self._backend: CatalogBackend = backend or SqliteCatalogBackend(path)

    @property
    def backend(self) -> CatalogBackend:
        return self._backend

    def register_dataset(self, manifest: DatasetManifest, *, kind: str, provider: str) -> None:
        self._backend.upsert_dataset(manifest, kind=kind, provider=provider)

    def get_dataset(self, dataset_id: str) -> CatalogEntry | None:
        return self._backend.get_dataset(dataset_id)

    def list_datasets(
        self,
        *,
        provider: str | None = None,
        kind: str | None = None,
        symbol: str | None = None,
    ) -> list[CatalogEntry]:
        return self._backend.list_datasets(provider=provider, kind=kind, symbol=symbol)

    def find_latest(self, *, provider: str, symbol: str, timeframe: str) -> CatalogEntry | None:
        return self._backend.find_latest(provider=provider, symbol=symbol, timeframe=timeframe)

    def verify_dataset(self, dataset_id: str) -> bool:
        return self._backend.verify_dataset(dataset_id)
