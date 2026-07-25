"""Feature Store versionado (Fase 5 Oficial — Módulo 3)."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.validation import require_non_empty_str
from quantlab.data.atomic_io import atomic_write_bytes, atomic_write_text
from quantlab.features.contracts import FEATURES_SCHEMA_VERSION, FeatureFrame
from quantlab.features.serialization import feature_frame_from_dict, feature_frame_to_dict

_SAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_segment(value: str) -> str:
    """Sanitiza segmento e incluye hash del valor original (anti-colisión TD-13).

    Así ``a/b`` y ``a_b`` no comparten path on-disk.
    """
    cleaned = _SAFE_RE.sub("_", value.strip())
    if not cleaned or cleaned in {".", ".."} or set(cleaned) <= {"."}:
        raise ValidationError(f"segmento de path inseguro: {value!r}")
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:10]
    return f"{cleaned}__{digest}"


@dataclass(frozen=True, slots=True)
class FeatureStoreRef:
    """Referencia inmutable a un FeatureFrame persistido."""

    instrument_id: str
    pipeline_name: str
    version: str
    path: str
    checksum: str
    schema_version: str
    created_at: datetime


@dataclass
class FeatureStore:
    """Persistencia versionada de FeatureFrame (JSON determinista + checksum + caché).

    TD-09 (aceptado research-prod): backend filesystem local únicamente.
    Sin S3/remoto; ``root`` debe ser path local (no URL).
    """

    root: Path
    _cache: dict[tuple[str, str, str], FeatureFrame] = field(
        default_factory=dict, init=False, repr=False
    )

    def __post_init__(self) -> None:
        root = Path(self.root)
        # Windows: Path("s3://x") → "s3:/x"; detectar ambos estilos.
        raw = str(self.root).replace("\\", "/").lower()
        remote_prefixes = ("s3:/", "http:/", "https:/", "gs:/", "az:/")
        if "://" in raw or raw.startswith(remote_prefixes):
            raise ValidationError("FeatureStore TD-09: solo filesystem local (sin URL remota)")
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, frame: FeatureFrame, *, version: str) -> FeatureStoreRef:
        require_non_empty_str(version, "version")
        payload = feature_frame_to_dict(frame)
        body = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
        raw_bytes = (body + "\n").encode("utf-8")
        checksum = hashlib.sha256(raw_bytes).hexdigest()
        directory = (
            self.root
            / _safe_segment(frame.instrument_id)
            / _safe_segment(frame.pipeline_name)
            / _safe_segment(version)
        )
        directory.mkdir(parents=True, exist_ok=True)
        frame_path = directory / "frame.json"
        meta_path = directory / "meta.json"
        if frame_path.exists():
            existing = hashlib.sha256(frame_path.read_bytes()).hexdigest()
            if existing == checksum:
                # Idempotente: mismo contenido
                meta_existing = (
                    json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
                )
                created_raw = (
                    meta_existing.get("created_at") if isinstance(meta_existing, dict) else None
                )
                created = (
                    datetime.fromisoformat(str(created_raw))
                    if isinstance(created_raw, str)
                    else datetime.now(tz=UTC)
                )
                key = (frame.instrument_id, frame.pipeline_name, version)
                self._cache[key] = frame
                return FeatureStoreRef(
                    instrument_id=frame.instrument_id,
                    pipeline_name=frame.pipeline_name,
                    version=version,
                    path=str(frame_path),
                    checksum=checksum,
                    schema_version=frame.schema_version or FEATURES_SCHEMA_VERSION,
                    created_at=created,
                )
            raise ValidationError(
                f"feature version ya existe con otro checksum: {frame.instrument_id}/"
                f"{frame.pipeline_name}/{version}"
            )
        atomic_write_bytes(frame_path, raw_bytes)
        created = datetime.now(tz=UTC)
        meta = {
            "instrument_id": frame.instrument_id,
            "pipeline_name": frame.pipeline_name,
            "version": version,
            "checksum": checksum,
            "schema_version": frame.schema_version,
            "created_at": created.isoformat(),
            "bar_count": frame.bar_count,
            "series": sorted(frame.series.keys()),
            "path_layout": "hashed_segments_v1",
        }
        atomic_write_text(
            meta_path,
            json.dumps(meta, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        )
        key = (frame.instrument_id, frame.pipeline_name, version)
        self._cache[key] = frame
        return FeatureStoreRef(
            instrument_id=frame.instrument_id,
            pipeline_name=frame.pipeline_name,
            version=version,
            path=str(frame_path),
            checksum=checksum,
            schema_version=frame.schema_version or FEATURES_SCHEMA_VERSION,
            created_at=created,
        )

    def get(self, instrument_id: str, pipeline_name: str, version: str) -> FeatureFrame:
        require_non_empty_str(instrument_id, "instrument_id")
        require_non_empty_str(pipeline_name, "pipeline_name")
        require_non_empty_str(version, "version")
        key = (instrument_id, pipeline_name, version)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        frame_path = (
            self.root
            / _safe_segment(instrument_id)
            / _safe_segment(pipeline_name)
            / _safe_segment(version)
            / "frame.json"
        )
        if not frame_path.exists():
            raise ValidationError(f"feature frame no encontrado: {frame_path}")
        raw_bytes = frame_path.read_bytes()
        checksum = hashlib.sha256(raw_bytes).hexdigest()
        meta_path = frame_path.parent / "meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if isinstance(meta, dict) and meta.get("checksum") != checksum:
                raise ValidationError("checksum de feature frame no coincide")
        raw = json.loads(raw_bytes.decode("utf-8"))
        if not isinstance(raw, dict):
            raise ValidationError("frame.json inválido")
        frame = feature_frame_from_dict(raw)
        self._cache[key] = frame
        return frame

    def clear_cache(self) -> None:
        self._cache.clear()

    def list_versions(self, instrument_id: str, pipeline_name: str) -> tuple[str, ...]:
        base = self.root / _safe_segment(instrument_id) / _safe_segment(pipeline_name)
        if not base.exists():
            return ()
        versions: list[str] = []
        for path in base.iterdir():
            if not path.is_dir() or not (path / "frame.json").exists():
                continue
            meta_path = path / "meta.json"
            if not meta_path.exists():
                continue
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            ver = meta.get("version") if isinstance(meta, dict) else None
            if isinstance(ver, str) and ver:
                versions.append(ver)
        return tuple(sorted(set(versions)))
