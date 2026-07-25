"""Protocolos y modelos del catálogo (abstracción SQLite → DuckDB/Parquet)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from quantlab.core.types.manifests import DatasetManifest


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    dataset_id: str
    kind: str
    provider: str
    symbol: str | None
    timeframe: str | None
    manifest: dict[str, Any]


@runtime_checkable
class CatalogBackend(Protocol):
    """Interfaz de lectura/escritura del catálogo (sin acoplar al motor SQL)."""

    def upsert_dataset(self, manifest: DatasetManifest, *, kind: str, provider: str) -> None: ...

    def get_dataset(self, dataset_id: str) -> CatalogEntry | None: ...

    def list_datasets(
        self,
        *,
        provider: str | None = None,
        kind: str | None = None,
        symbol: str | None = None,
    ) -> list[CatalogEntry]: ...

    def find_latest(self, *, provider: str, symbol: str, timeframe: str) -> CatalogEntry | None: ...

    def verify_dataset(self, dataset_id: str) -> bool: ...
