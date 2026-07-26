"""Browser read-only del Feature Store (session/features o default) — F31.

Investiga ``quantlab.features.store.FeatureStore`` (layout hashed_segments_v1 +
``meta.json``). Persistencia demo vía ``FeatureStore.put`` en la sesión.

Prioridad de root:
1. ``explicit``
2. env ``QUANTLAB_FEATURE_STORE_PATH``
3. ``session_root/features`` (workbench)
4. default ``data/features`` si existe como directorio

Listado vacío es OK (sin crear artifacts).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from quantlab.execution.live_gate import LIVE_BLOCKED

DEFAULT_FEATURES_PATH = Path("data/features")
FEATURES_ENV = "QUANTLAB_FEATURE_STORE_PATH"
MAX_ARTIFACTS_LIST = 500


def features_dir_for(session_root: Path) -> Path:
    return Path(session_root) / "features"


def default_feature_store_candidates() -> tuple[Path, ...]:
    return (DEFAULT_FEATURES_PATH,)


def resolve_feature_store_root(
    *,
    explicit: Path | str | None = None,
    session_root: Path | str | None = None,
) -> tuple[Path | None, str | None]:
    """Resuelve root del Feature Store + etiqueta de fuente.

    Retorna ``(path, source)`` donde source ∈ env|explicit|session|default.
    Preferencia: explicit → env → session/features → default si existe.
    Si solo hay session_root, usa ``session/features`` aunque aún no exista
    (empty-ok; se crea al persistir un run).
    """
    if explicit is not None:
        return Path(explicit).expanduser().resolve(), "explicit"

    env_raw = os.environ.get(FEATURES_ENV, "").strip()
    if env_raw and env_raw.upper() != "DISABLED":
        return Path(env_raw).expanduser().resolve(), "env"

    if session_root is not None:
        return features_dir_for(Path(session_root)).resolve(), "session"

    for cand in default_feature_store_candidates():
        try:
            resolved = cand.expanduser().resolve()
        except OSError:
            continue
        if resolved.is_dir():
            return resolved, "default"
    return None, None


def _artifact_from_meta(meta_path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    instrument_id = raw.get("instrument_id")
    pipeline_name = raw.get("pipeline_name")
    version = raw.get("version")
    if not (
        isinstance(instrument_id, str)
        and instrument_id
        and isinstance(pipeline_name, str)
        and pipeline_name
        and isinstance(version, str)
        and version
    ):
        return None
    series_raw = raw.get("series")
    series: list[str] = []
    if isinstance(series_raw, list):
        series = [str(s) for s in series_raw if isinstance(s, str)]
    frame_path = meta_path.parent / "frame.json"
    return {
        "instrument_id": instrument_id,
        "pipeline_name": pipeline_name,
        "version": version,
        "checksum": raw.get("checksum") if isinstance(raw.get("checksum"), str) else None,
        "schema_version": (
            raw.get("schema_version") if isinstance(raw.get("schema_version"), str) else None
        ),
        "created_at": raw.get("created_at") if isinstance(raw.get("created_at"), str) else None,
        "bar_count": raw.get("bar_count") if isinstance(raw.get("bar_count"), int) else None,
        "series": series,
        "columns": series,
        "path": str(frame_path) if frame_path.is_file() else str(meta_path.parent),
        "meta_path": str(meta_path),
    }


def list_feature_artifacts(root: Path | str | None) -> list[dict[str, Any]]:
    """Lista artifacts leyendo ``meta.json`` bajo el root (read-only)."""
    if root is None:
        return []
    base = Path(root)
    if not base.is_dir():
        return []
    found: list[dict[str, Any]] = []
    for meta_path in sorted(base.rglob("meta.json")):
        if not meta_path.is_file():
            continue
        # Solo layouts FeatureStore: sibling frame.json
        if not (meta_path.parent / "frame.json").is_file():
            continue
        art = _artifact_from_meta(meta_path)
        if art is not None:
            found.append(art)
        if len(found) >= MAX_ARTIFACTS_LIST:
            break
    # Orden estable: instrument / pipeline / version
    found.sort(
        key=lambda a: (
            str(a.get("instrument_id") or ""),
            str(a.get("pipeline_name") or ""),
            str(a.get("version") or ""),
        )
    )
    return found


def list_feature_store(
    *,
    explicit: Path | str | None = None,
    session_root: Path | str | None = None,
) -> dict[str, Any]:
    """Payload JSON para GET /api/lab/features/store."""
    root, source = resolve_feature_store_root(explicit=explicit, session_root=session_root)
    base: dict[str, Any] = {
        "ok": True,
        "live_blocked": LIVE_BLOCKED is True,
        "read_only": True,
        "features_env": FEATURES_ENV,
        "default_candidates": [str(p) for p in default_feature_store_candidates()],
    }
    if root is None:
        return {
            **base,
            "available": False,
            "store_path": None,
            "source": None,
            "message": (
                "Feature store no encontrado. "
                f"Corré el pipeline demo (persiste en session/features) o colocá un store en "
                f"{DEFAULT_FEATURES_PATH} / definí {FEATURES_ENV}."
            ),
            "artifacts": [],
            "count": 0,
            "columns_union": [],
        }

    artifacts = list_feature_artifacts(root)
    columns_union: list[str] = []
    seen: set[str] = set()
    for art in artifacts:
        for col in art.get("columns") or []:
            if isinstance(col, str) and col not in seen:
                seen.add(col)
                columns_union.append(col)

    empty = not artifacts
    exists = root.is_dir()
    return {
        **base,
        "available": exists or source == "session",
        "store_path": str(root),
        "source": source,
        "message": (
            "Feature store vacío — corré el pipeline demo para persistir artifacts."
            if empty
            else None
        ),
        "artifacts": artifacts,
        "count": len(artifacts),
        "truncated": False,
        "columns_union": columns_union,
    }
