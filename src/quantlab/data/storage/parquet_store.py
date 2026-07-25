"""Processed storage columnar Parquet vía DuckDB (Fase 17 / TD-01)."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb

from quantlab.core.exceptions import ValidationError
from quantlab.data.atomic_io import atomic_write_text
from quantlab.data.exchanges.a3.mappers import sanitize_symbol_for_path


@dataclass(frozen=True, slots=True)
class ParquetWriteResult:
    path: str
    rows: int
    columns: tuple[str, ...]


class ParquetProcessedStore:
    """Escribe/lee datasets processed como Parquet (DuckDB COPY)."""

    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def write_rows(
        self,
        *,
        dataset_id: str,
        schema_version: str,
        symbol: str,
        timeframe: str | None,
        rows: Sequence[Mapping[str, Any]],
        meta: Mapping[str, Any] | None = None,
    ) -> ParquetWriteResult:
        if not rows:
            raise ValidationError("rows vacío")
        safe = sanitize_symbol_for_path(symbol)
        tf = timeframe or "none"
        directory = self._root / dataset_id / f"schema_v{schema_version}" / safe / tf
        directory.mkdir(parents=True, exist_ok=True)
        out = directory / "data.parquet"
        if out.exists():
            raise ValidationError(f"parquet ya existe (inmutable): {out}")

        columns = tuple(sorted(rows[0].keys()))
        for row in rows:
            if set(row.keys()) != set(columns):
                raise ValidationError("filas con columnas inconsistentes")

        cols_sql = ", ".join(f'"{c}"' for c in columns)
        create_sql = ", ".join(f'"{c}" VARCHAR' for c in columns)
        con = duckdb.connect(database=":memory:")
        try:
            con.execute(f"CREATE TABLE data ({create_sql})")
            placeholders = ", ".join("?" for _ in columns)
            insert_sql = f"INSERT INTO data ({cols_sql}) VALUES ({placeholders})"
            for row in rows:
                vals = [None if row[c] is None else str(row[c]) for c in columns]
                con.execute(insert_sql, vals)
            # path con forward slashes para DuckDB en Windows
            con.execute(f"COPY data TO '{out.as_posix()}' (FORMAT PARQUET)")
        finally:
            con.close()

        meta_path = directory / "meta.json"
        payload = {
            "dataset_id": dataset_id,
            "schema_version": schema_version,
            "symbol": symbol,
            "timeframe": timeframe,
            "rows": len(rows),
            "columns": list(columns),
            "format": "parquet",
            **dict(meta or {}),
        }
        atomic_write_text(
            meta_path, json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        )
        return ParquetWriteResult(path=str(out), rows=len(rows), columns=columns)

    def read_rows(self, path: Path) -> list[dict[str, Any]]:
        if not path.is_file():
            raise ValidationError(f"parquet inexistente: {path}")
        con = duckdb.connect(database=":memory:")
        try:
            rel = con.execute(f"SELECT * FROM read_parquet('{path.as_posix()}')")
            cols = [d[0] for d in rel.description] if rel.description else []
            raw = rel.fetchall()
        finally:
            con.close()
        return [dict(zip(cols, row, strict=True)) for row in raw]
