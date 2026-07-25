"""Replay de datasets (stub mínimo Fase 3)."""

from __future__ import annotations

from quantlab.data.catalog.catalog import CatalogEntry, DataCatalog


def load_catalog_entry(catalog: DataCatalog, dataset_id: str) -> CatalogEntry:
    entry = catalog.get_dataset(dataset_id)
    if entry is None:
        raise KeyError(dataset_id)
    return entry
