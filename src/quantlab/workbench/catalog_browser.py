"""Browser read-only del Data Catalog local (SQLite/DuckDB) — F30.

Investiga ``quantlab.data.catalog``: ``DataCatalog`` + ``SqliteCatalogBackend``
(default) y ``DuckDBCatalogBackend``. Path default A3:
``data/catalog/quantlab_catalog.sqlite``. Override: ``QUANTLAB_CATALOG_PATH``.

Si el archivo no existe → lista vacía + mensaje (sin crear DB).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.data.catalog import DataCatalog, DuckDBCatalogBackend, SqliteCatalogBackend
from quantlab.execution.live_gate import LIVE_BLOCKED

DEFAULT_SQLITE_PATH = Path("data/catalog/quantlab_catalog.sqlite")
DEFAULT_DUCKDB_PATH = Path("data/catalog/quantlab_catalog.duckdb")
CATALOG_ENV = "QUANTLAB_CATALOG_PATH"
MAX_DATASETS_LIST = 500


def default_catalog_candidates() -> tuple[Path, ...]:
    """Candidatos locales en orden de preferencia."""
    return (DEFAULT_SQLITE_PATH, DEFAULT_DUCKDB_PATH)


def resolve_catalog_path(explicit: Path | str | None = None) -> Path | None:
    """Resuelve path de catálogo existente; ``None`` si no hay archivo local.

    Orden: ``explicit`` → env ``QUANTLAB_CATALOG_PATH`` → defaults si existen.
    No crea archivos.
    """
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(Path(explicit))
    env_raw = os.environ.get(CATALOG_ENV, "").strip()
    if env_raw and env_raw.upper() != "DISABLED":
        candidates.append(Path(env_raw))
    candidates.extend(default_catalog_candidates())

    seen: set[Path] = set()
    for cand in candidates:
        try:
            resolved = cand.expanduser().resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file():
            return resolved
    return None


def _backend_for_path(path: Path) -> tuple[DataCatalog, str]:
    """Abre DataCatalog read-capable según extensión (sqlite|duckdb)."""
    suffix = path.suffix.lower()
    if suffix in {".duckdb", ".ddb"}:
        return DataCatalog(path, backend=DuckDBCatalogBackend(path)), "duckdb"
    if suffix in {".sqlite", ".db", ".sqlite3"} or suffix == "":
        return DataCatalog(path, backend=SqliteCatalogBackend(path)), "sqlite"
    raise ValidationError(
        f"extensión de catálogo no soportada: {suffix!r} (esperado .sqlite/.db/.duckdb)"
    )


def entry_to_dict(entry: Any) -> dict[str, Any]:
    """Serializa CatalogEntry a dict JSON-safe (sin manifest completo pesado)."""
    return {
        "dataset_id": entry.dataset_id,
        "kind": entry.kind,
        "provider": entry.provider,
        "symbol": entry.symbol,
        "timeframe": entry.timeframe,
    }


def list_catalog_datasets(
    *,
    catalog_path: Path | str | None = None,
    provider: str | None = None,
    kind: str | None = None,
    symbol: str | None = None,
) -> dict[str, Any]:
    """Lista datasets del catálogo local (read-only).

    Si no hay archivo → ``available=False``, ``datasets=[]`` + mensaje.
    """
    path = resolve_catalog_path(catalog_path)
    base: dict[str, Any] = {
        "ok": True,
        "live_blocked": LIVE_BLOCKED is True,
        "read_only": True,
        "catalog_env": CATALOG_ENV,
        "default_candidates": [str(p) for p in default_catalog_candidates()],
    }
    if path is None:
        return {
            **base,
            "available": False,
            "catalog_path": None,
            "backend": None,
            "message": (
                "Catálogo local no encontrado. "
                f"Colocá un SQLite/DuckDB en {DEFAULT_SQLITE_PATH} "
                f"(o {DEFAULT_DUCKDB_PATH}) o definí {CATALOG_ENV}."
            ),
            "datasets": [],
            "count": 0,
        }

    try:
        catalog, backend_name = _backend_for_path(path)
        entries = catalog.list_datasets(provider=provider, kind=kind, symbol=symbol)
    except ValidationError:
        raise
    except Exception as exc:  # noqa: BLE001
        return {
            **base,
            "available": False,
            "catalog_path": str(path),
            "backend": None,
            "message": f"Catálogo ilegible: {exc}",
            "datasets": [],
            "count": 0,
        }

    limited = entries[:MAX_DATASETS_LIST]
    return {
        **base,
        "available": True,
        "catalog_path": str(path),
        "backend": backend_name,
        "message": None,
        "datasets": [entry_to_dict(e) for e in limited],
        "count": len(limited),
        "truncated": len(entries) > MAX_DATASETS_LIST,
    }
