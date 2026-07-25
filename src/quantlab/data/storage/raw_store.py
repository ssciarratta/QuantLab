"""Almacenamiento raw append-only y processed (Parquet vía filas JSONL/CSV mínimo)."""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from quantlab.data.atomic_io import atomic_write_text
from quantlab.data.exchanges.a3.constants import PROVIDER_ID, SCHEMA_VERSION_RAW
from quantlab.data.exchanges.a3.exceptions import A3DataError
from quantlab.data.exchanges.a3.mappers import sanitize_symbol_for_path


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return dict(value)
    return str(value)


@dataclass(frozen=True, slots=True)
class RawRecord:
    provider: str
    endpoint_or_message_type: str
    environment: str
    symbol: str | None
    event_timestamp: datetime | None
    received_timestamp: datetime
    request_id: str | None
    schema_version: str
    payload: dict[str, Any]
    checksum: str
    ingestion_run_id: str


class RawStore:
    """Raw append-only bajo data/raw/a3/YYYY-MM-DD/SYMBOL_SAFE/kind/."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def append(
        self,
        *,
        kind: str,
        environment: str,
        symbol: str | None,
        endpoint_or_message_type: str,
        payload: dict[str, Any],
        event_timestamp: datetime | None = None,
        request_id: str | None = None,
        ingestion_run_id: str | None = None,
    ) -> Path:
        received = datetime.now(tz=UTC)
        run_id = ingestion_run_id or str(uuid.uuid4())
        body = json.dumps(payload, sort_keys=True, default=_json_default, ensure_ascii=False)
        checksum = hashlib.sha256(body.encode("utf-8")).hexdigest()
        day = received.strftime("%Y-%m-%d")
        sym = sanitize_symbol_for_path(symbol) if symbol else "_none_"
        directory = self._root / day / sym / kind
        directory.mkdir(parents=True, exist_ok=True)
        record = {
            "provider": PROVIDER_ID,
            "endpoint_or_message_type": endpoint_or_message_type,
            "environment": environment,
            "symbol": symbol,
            "event_timestamp": event_timestamp.isoformat() if event_timestamp else None,
            "received_timestamp": received.isoformat(),
            "request_id": request_id,
            "schema_version": SCHEMA_VERSION_RAW,
            "payload": payload,
            "checksum": checksum,
            "ingestion_run_id": run_id,
        }
        # Nombre único: nunca sobrescribe
        out = directory / f"{received.strftime('%H%M%S%f')}_{checksum[:12]}.json"
        if out.exists():
            raise A3DataError(f"colisión de raw (no sobrescribir): {out}")
        out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return out


class ProcessedStore:
    """Persiste datasets processed como JSONL determinista (+ sidecar meta)."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def write_jsonl(
        self,
        *,
        dataset_id: str,
        schema_version: str,
        symbol: str,
        timeframe: str | None,
        rows: list[dict[str, Any]],
        meta: dict[str, Any],
    ) -> Path:
        safe = sanitize_symbol_for_path(symbol)
        tf = timeframe or "none"
        directory = self._root / dataset_id / f"schema_v{schema_version}" / safe / tf
        directory.mkdir(parents=True, exist_ok=True)
        out = directory / "data.jsonl"
        if out.exists():
            raise A3DataError(f"processed ya existe (inmutable): {out}")
        lines = [
            json.dumps(row, sort_keys=True, default=_json_default, ensure_ascii=False)
            for row in rows
        ]
        atomic_write_text(out, "\n".join(lines) + ("\n" if lines else ""))
        meta_path = directory / "meta.json"
        atomic_write_text(
            meta_path,
            json.dumps(meta, indent=2, sort_keys=True, default=_json_default) + "\n",
        )
        return out
