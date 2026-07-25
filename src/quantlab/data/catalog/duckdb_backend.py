"""CatalogBackend analítico con DuckDB (Fase 17 / TD-02)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import duckdb

from quantlab.core.types.manifests import DatasetManifest
from quantlab.data.atomic_io import atomic_write_text
from quantlab.data.catalog.protocols import CatalogEntry

_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class DuckDBCatalogBackend:
    """Backend DuckDB del catálogo (+ sidecar JSON atómico)."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._sidecar_root = self._path.parent / f"{self._path.stem}_sidecars"
        self._sidecar_root.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(database=str(self._path))

    def _init_db(self) -> None:
        con = self._connect()
        try:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS datasets (
                    dataset_id VARCHAR PRIMARY KEY,
                    kind VARCHAR NOT NULL,
                    provider VARCHAR NOT NULL,
                    symbol VARCHAR,
                    timeframe VARCHAR,
                    created_at VARCHAR NOT NULL,
                    manifest_json VARCHAR NOT NULL
                )
                """
            )
        finally:
            con.close()

    def _row_to_entry(self, row: tuple[object, ...]) -> CatalogEntry:
        return CatalogEntry(
            dataset_id=str(row[0]),
            kind=str(row[1]),
            provider=str(row[2]),
            symbol=str(row[3]) if row[3] is not None else None,
            timeframe=str(row[4]) if row[4] is not None else None,
            manifest=json.loads(str(row[6])),
        )

    def upsert_dataset(self, manifest: DatasetManifest, *, kind: str, provider: str) -> None:
        symbol = manifest.instruments[0] if manifest.instruments else None
        payload = json.dumps(manifest.to_dict(), ensure_ascii=False, sort_keys=True)
        con = self._connect()
        try:
            con.execute("DELETE FROM datasets WHERE dataset_id = ?", [manifest.dataset_id])
            con.execute(
                """
                INSERT INTO datasets
                (dataset_id, kind, provider, symbol, timeframe, created_at, manifest_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    manifest.dataset_id,
                    kind,
                    provider,
                    symbol,
                    manifest.granularity,
                    manifest.created_at.isoformat(),
                    payload,
                ],
            )
        finally:
            con.close()
        sidecar = self._sidecar_root / f"{manifest.dataset_id}.json"
        atomic_write_text(sidecar, payload + "\n")

    def get_dataset(self, dataset_id: str) -> CatalogEntry | None:
        con = self._connect()
        try:
            row = con.execute(
                "SELECT dataset_id, kind, provider, symbol, timeframe, created_at, manifest_json "
                "FROM datasets WHERE dataset_id = ?",
                [dataset_id],
            ).fetchone()
        finally:
            con.close()
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
        con = self._connect()
        try:
            rows = con.execute(
                "SELECT dataset_id, kind, provider, symbol, timeframe, created_at, manifest_json "
                f"FROM datasets{where} ORDER BY created_at DESC",
                params,
            ).fetchall()
        finally:
            con.close()
        return [self._row_to_entry(r) for r in rows]

    def find_latest(self, *, provider: str, symbol: str, timeframe: str) -> CatalogEntry | None:
        con = self._connect()
        try:
            row = con.execute(
                """
                SELECT dataset_id, kind, provider, symbol, timeframe, created_at, manifest_json
                FROM datasets
                WHERE provider = ? AND symbol = ? AND timeframe = ?
                ORDER BY created_at DESC LIMIT 1
                """,
                [provider, symbol, timeframe],
            ).fetchone()
        finally:
            con.close()
        if row is None:
            return None
        return self._row_to_entry(row)

    def verify_dataset(self, dataset_id: str) -> bool:
        import hashlib
        from pathlib import Path

        entry = self.get_dataset(dataset_id)
        if entry is None:
            return False
        checksum = entry.manifest.get("checksum")
        if not isinstance(checksum, str) or not _SHA256_RE.fullmatch(checksum):
            return False
        storage_path = entry.manifest.get("storage_path")
        if not isinstance(storage_path, str) or not storage_path:
            return False
        path = Path(storage_path)
        if not path.is_file():
            return False
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return digest.lower() == checksum.lower()
