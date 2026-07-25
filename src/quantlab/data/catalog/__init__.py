"""Catálogo de datasets."""

from quantlab.data.catalog.catalog import DataCatalog, SqliteCatalogBackend
from quantlab.data.catalog.duckdb_backend import DuckDBCatalogBackend
from quantlab.data.catalog.protocols import CatalogBackend, CatalogEntry

__all__ = [
    "CatalogBackend",
    "CatalogEntry",
    "DataCatalog",
    "DuckDBCatalogBackend",
    "SqliteCatalogBackend",
]
