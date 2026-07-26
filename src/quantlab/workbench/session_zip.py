"""Export / import de sesión workbench a ZIP (F39) — sin secretos, anti zip-slip.

Reutiliza la protección zip-slip de ``quantlab.scale.backup`` y escritura
atómica vía ``atomic_write_bytes`` para el manifiesto / artefactos.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import shutil
import tempfile
import zipfile
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from quantlab.core.exceptions import ValidationError
from quantlab.data.atomic_io import atomic_write_bytes, atomic_write_text
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.scale.backup import _assert_safe_zip_member
from quantlab.workbench.session import WorkbenchSession, validate_session_id

MANIFEST_NAME = "quantlab_session_export.json"
EXPORT_FORMAT_VERSION = 1

# Archivos/dirs de sesión a incluir (relativos a session root).
INCLUDE_FILES: frozenset[str] = frozenset(
    {
        "journal.jsonl",
        "book.json",
        "meta.json",
        "layout.json",
        "settings.json",
        "watchlist.json",
        "chat_audit.jsonl",
        "activity.jsonl",
        "equity.jsonl",
        "access.jsonl",
    }
)
INCLUDE_DIRS: frozenset[str] = frozenset(
    {
        "experiments",
        "exports",
        "reports",
        "features",
        "validation",
        "optimizer",
        "montecarlo",
        "presets",
    }
)

# Nombres / patrones denegados (secretos) — export e import fail-closed.
_SECRET_BASENAME_RE = re.compile(
    r"(?i)^("
    r"\.env.*|"
    r".*\.secret|"
    r".*\.pem|"
    r".*\.key|"
    r".*credentials.*|"
    r".*api[_-]?key.*|"
    r".*password.*|"
    r"sync_token\.txt|"
    r"sync_approved\.txt|"
    r".*token\.txt"
    r")$"
)
_SECRET_PARTS = frozenset(
    {
        ".env",
        "secrets",
        "credentials",
        "private",
    }
)

ImportMode = Literal["new", "merge"]
MAX_ZIP_BYTES = 50 * 1024 * 1024  # 50 MiB


@dataclass(frozen=True, slots=True)
class SessionExportResult:
    session_id: str
    archive_path: Path
    files_count: int
    bytes_written: int
    sha256: str
    excluded_secrets: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SessionImportResult:
    mode: ImportMode
    session_id: str
    session_root: Path
    files_written: int
    skipped_existing: int
    manifest: dict[str, Any]


def is_secret_arcname(arcname: str) -> bool:
    """True si el miembro ZIP / path relativo parece secreto."""
    name = arcname.replace("\\", "/").strip("/")
    if not name:
        return False
    parts = [p for p in name.split("/") if p and p != "."]
    if any(p.lower() in _SECRET_PARTS for p in parts):
        return True
    base = parts[-1] if parts else ""
    return bool(_SECRET_BASENAME_RE.match(base))


def _is_sqlite_ephemeral(path: Path) -> bool:
    """Omite sidecars SQLite WAL/SHM/journal (efímeros / race en export)."""
    name = path.name.lower()
    return (
        name.endswith("-wal")
        or name.endswith("-shm")
        or name.endswith("-journal")
        or name.endswith(".db-wal")
        or name.endswith(".db-shm")
        or name.endswith(".sqlite-wal")
        or name.endswith(".sqlite-shm")
        or name.endswith(".sqlite3-wal")
        or name.endswith(".sqlite3-shm")
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iter_export_files(session_root: Path) -> list[tuple[Path, str]]:
    """Lista (abs_path, arcname) a exportar; omite secretos."""
    root = session_root.resolve()
    out: list[tuple[Path, str]] = []
    for name in sorted(INCLUDE_FILES):
        path = root / name
        if path.is_file() and not is_secret_arcname(name):
            out.append((path, name))
    for dirname in sorted(INCLUDE_DIRS):
        dpath = root / dirname
        if not dpath.is_dir():
            continue
        for path in sorted(dpath.rglob("*")):
            if not path.is_file():
                continue
            if _is_sqlite_ephemeral(path):
                continue
            try:
                rel = path.relative_to(root).as_posix()
            except ValueError:
                continue
            if is_secret_arcname(rel):
                continue
            # No incluir ZIPs de sesión anidados bajo exports/.
            if path.suffix.lower() == ".zip" and "session" in path.name.lower():
                continue
            out.append((path, rel))
    return out


def session_exports_dir(session_parent: Path) -> Path:
    """Directorio hermano ``_session_zips`` (fuera del árbol de sesión)."""
    dest = Path(session_parent).resolve() / "_session_zips"
    dest.mkdir(parents=True, exist_ok=True)
    return dest


def export_session(
    session: WorkbenchSession,
    *,
    dest_dir: Path | None = None,
) -> SessionExportResult:
    """Empaqueta la sesión en ZIP (sin secretos) bajo ``_session_zips``."""
    root = session.root.resolve()
    if not root.is_dir():
        raise ValidationError(f"session root inexistente: {root}")
    parent = root.parent
    out_dir = dest_dir if dest_dir is not None else session_exports_dir(parent)
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    files = _iter_export_files(root)
    # Contar secretos omitidos (solo bajo includes).
    excluded: list[str] = []
    for name in sorted(INCLUDE_FILES):
        path = root / name
        if path.is_file() and is_secret_arcname(name):
            excluded.append(name)
    for dirname in sorted(INCLUDE_DIRS):
        dpath = root / dirname
        if not dpath.is_dir():
            continue
        for path in sorted(dpath.rglob("*")):
            if not path.is_file():
                continue
            try:
                rel = path.relative_to(root).as_posix()
            except ValueError:
                continue
            if is_secret_arcname(rel):
                excluded.append(rel)

    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S%fZ")
    archive = out_dir / f"session_{session.session_id}_{stamp}.zip"
    manifest: dict[str, Any] = {
        "format": "quantlab_session_zip",
        "format_version": EXPORT_FORMAT_VERSION,
        "session_id": session.session_id,
        "created_at": datetime.now(tz=UTC).isoformat(),
        "quantlab_live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "files": [arc for _, arc in files],
        "excluded_secrets": excluded,
        "include_files": sorted(INCLUDE_FILES),
        "include_dirs": sorted(INCLUDE_DIRS),
    }

    count = 0
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            MANIFEST_NAME,
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        )
        count += 1
        for path, arcname in files:
            # Defensa zip-slip en escritura: arcname no puede salir.
            _assert_safe_zip_member(arcname, root)
            try:
                zf.write(path, arcname=arcname)
            except FileNotFoundError:
                # Race: sidecar SQLite / archivo borrado entre listado y write.
                continue
            count += 1

    digest = _sha256_file(archive)
    return SessionExportResult(
        session_id=session.session_id,
        archive_path=archive,
        files_count=count,
        bytes_written=archive.stat().st_size,
        sha256=digest,
        excluded_secrets=tuple(excluded),
    )


def export_result_to_dict(result: SessionExportResult) -> dict[str, Any]:
    return {
        "ok": True,
        "kind": "session_export",
        "session_id": result.session_id,
        "path": str(result.archive_path),
        "filename": result.archive_path.name,
        "files_count": result.files_count,
        "bytes": result.bytes_written,
        "sha256": result.sha256,
        "excluded_secrets": list(result.excluded_secrets),
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
        "banner": "session ZIP research-safe — sin secretos · sin LIVE",
    }


def _read_manifest(zf: zipfile.ZipFile) -> dict[str, Any]:
    try:
        raw = zf.read(MANIFEST_NAME)
    except KeyError as exc:
        raise ValidationError(f"ZIP de sesión inválido: falta {MANIFEST_NAME}") from exc
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"manifiesto ZIP inválido: {exc}") from exc
    if not isinstance(data, dict):
        raise ValidationError("manifiesto ZIP debe ser objeto JSON")
    if data.get("format") != "quantlab_session_zip":
        raise ValidationError("format de manifiesto no es quantlab_session_zip")
    return data


def _validate_all_members(zf: zipfile.ZipFile, dest_root: Path) -> None:
    """Fail-closed: zip-slip + secretos antes de escribir nada."""
    for info in zf.infolist():
        name = info.filename.replace("\\", "/")
        if name.endswith("/"):
            _assert_safe_zip_member(name.rstrip("/"), dest_root)
            continue
        if name == MANIFEST_NAME:
            _assert_safe_zip_member(name, dest_root)
            continue
        _assert_safe_zip_member(name, dest_root)
        if is_secret_arcname(name):
            raise ValidationError(f"secreto rechazado en ZIP: {name}")
        # Solo allowlist de top-level.
        top = name.split("/", 1)[0]
        if top in INCLUDE_FILES or top in INCLUDE_DIRS:
            continue
        raise ValidationError(f"miembro fuera de allowlist de sesión: {name}")


def _extract_member(
    zf: zipfile.ZipFile,
    info: zipfile.ZipInfo,
    dest_root: Path,
    *,
    overwrite: bool,
) -> Literal["written", "skipped", "dir"]:
    name = info.filename.replace("\\", "/")
    if info.is_dir() or name.endswith("/"):
        target = _assert_safe_zip_member(name.rstrip("/"), dest_root)
        if name.rstrip("/"):
            target.mkdir(parents=True, exist_ok=True)
        return "dir"
    if name == MANIFEST_NAME:
        # Manifiesto no se materializa en session root (metadata del ZIP).
        return "skipped"
    target = _assert_safe_zip_member(name, dest_root)
    if target.exists() and not overwrite:
        return "skipped"
    target.parent.mkdir(parents=True, exist_ok=True)
    with zf.open(info, "r") as src:
        data = src.read()
    atomic_write_bytes(target, data)
    return "written"


def import_session_zip(
    archive: Path,
    *,
    session_parent: Path,
    mode: ImportMode,
    session_id: str | None = None,
    merge_into: WorkbenchSession | None = None,
) -> SessionImportResult:
    """Importa ZIP a sesión nueva o merge fail-closed (sin overwrite)."""
    if mode not in ("new", "merge"):
        raise ValidationError(f"mode inválido (new|merge): {mode!r}")
    archive = Path(archive)
    if not archive.is_file():
        raise ValidationError(f"archive inexistente: {archive}")
    size = archive.stat().st_size
    if size <= 0 or size > MAX_ZIP_BYTES:
        raise ValidationError(f"ZIP tamaño fuera de rango (1..{MAX_ZIP_BYTES}): {size}")

    parent = Path(session_parent).resolve()
    parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive, "r") as zf:
        try:
            zf.testzip()
        except Exception as exc:  # noqa: BLE001 — zip corrupto
            raise ValidationError(f"ZIP corrupto: {exc}") from exc
        manifest = _read_manifest(zf)

        if mode == "new":
            raw_sid = (session_id or "").strip() or f"imp{datetime.now(tz=UTC).strftime('%H%M%S')}"
            sid = validate_session_id(raw_sid)
            dest = (parent / sid).resolve()
            if not dest.is_relative_to(parent):
                raise ValidationError("session root fuera de parent (path traversal)")
            if dest.exists() and any(dest.iterdir()):
                raise ValidationError(f"destino de import no vacío: {dest}")
            dest.mkdir(parents=True, exist_ok=True)
            _validate_all_members(zf, dest)
            written = 0
            skipped = 0
            for info in zf.infolist():
                outcome = _extract_member(zf, info, dest, overwrite=False)
                if outcome == "written":
                    written += 1
                elif outcome == "skipped" and info.filename.replace("\\", "/") != MANIFEST_NAME:
                    skipped += 1
            # Asegura layout mínimo.
            session = WorkbenchSession(root=dest, session_id=sid)
            session.ensure_layout()
            if not session.meta_path.exists():
                session.save_meta(
                    {
                        "session_id": sid,
                        "created_at": datetime.now(tz=UTC).isoformat(),
                        "imported_from": str(archive.name),
                        "import_mode": "new",
                    }
                )
            return SessionImportResult(
                mode="new",
                session_id=sid,
                session_root=dest,
                files_written=written,
                skipped_existing=skipped,
                manifest=manifest,
            )

        # merge fail-closed: no overwrite; zip-slip + secretos rechazados.
        if merge_into is None:
            raise ValidationError("merge requiere sesión destino")
        dest = merge_into.root.resolve()
        if dest.parent.resolve() != parent:
            raise ValidationError("merge destino fuera del session parent")
        merge_into.ensure_layout()
        _validate_all_members(zf, dest)

        # Pre-scan: si algún archivo destino existe → fail-closed (no merge parcial).
        conflicts: list[str] = []
        for info in zf.infolist():
            name = info.filename.replace("\\", "/")
            if info.is_dir() or name.endswith("/") or name == MANIFEST_NAME:
                continue
            target = _assert_safe_zip_member(name, dest)
            if target.exists():
                conflicts.append(name)
        if conflicts:
            preview = ", ".join(conflicts[:8])
            more = "" if len(conflicts) <= 8 else f" (+{len(conflicts) - 8})"
            raise ValidationError(
                f"merge fail-closed: archivos existentes (usar mode=new): {preview}{more}"
            )

        written = 0
        for info in zf.infolist():
            outcome = _extract_member(zf, info, dest, overwrite=False)
            if outcome == "written":
                written += 1
        return SessionImportResult(
            mode="merge",
            session_id=merge_into.session_id,
            session_root=dest,
            files_written=written,
            skipped_existing=0,
            manifest=manifest,
        )


def decode_zip_base64(raw: str, *, dest: Path) -> Path:
    """Decodifica base64 a archivo ZIP (tamaño acotado)."""
    if not isinstance(raw, str) or not raw.strip():
        raise ValidationError("zip_base64 vacío")
    try:
        data = base64.b64decode(raw.strip(), validate=True)
    except Exception as exc:  # noqa: BLE001
        raise ValidationError(f"zip_base64 inválido: {exc}") from exc
    if not data or len(data) > MAX_ZIP_BYTES:
        raise ValidationError(f"ZIP decodificado fuera de rango (1..{MAX_ZIP_BYTES})")
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_bytes(dest, data)
    return dest


def resolve_upload_archive(
    *,
    zip_path: str | None,
    zip_base64: str | None,
    work_dir: Path,
    allowed_roots: Sequence[Path] | None = None,
) -> Path:
    """Resuelve archivo ZIP desde path local o base64 (mutuamente excluyentes).

    ``zip_path`` solo se acepta si resuelve bajo alguno de ``allowed_roots``
    (fail-closed F43: sin lectura arbitraria del filesystem).
    """
    has_path = bool(zip_path and str(zip_path).strip())
    has_b64 = bool(zip_base64 and str(zip_base64).strip())
    if has_path == has_b64:
        raise ValidationError("indicar exactamente uno de zip_path | zip_base64")
    if has_b64:
        assert zip_base64 is not None
        tmp = Path(work_dir) / f"upload_{datetime.now(tz=UTC).strftime('%Y%m%dT%H%M%S%f')}.zip"
        return decode_zip_base64(zip_base64, dest=tmp)
    assert zip_path is not None
    if "\x00" in zip_path:
        raise ValidationError("zip_path inválido (null byte)")
    path = Path(zip_path).expanduser()
    try:
        resolved = path.resolve()
    except OSError as exc:
        raise ValidationError(f"zip_path irresoluble: {zip_path}") from exc
    roots = list(allowed_roots) if allowed_roots else []
    if not roots:
        raise ValidationError(
            "zip_path requiere allowed_roots (sandbox session parent / _session_zips)"
        )
    ok = False
    for root in roots:
        try:
            if resolved.is_relative_to(Path(root).resolve()):
                ok = True
                break
        except (OSError, ValueError):
            continue
    if not ok:
        raise ValidationError(f"zip_path fuera de sandbox (session parent): {zip_path!r}")
    if not resolved.is_file():
        raise ValidationError(f"zip_path inexistente: {zip_path}")
    if resolved.stat().st_size > MAX_ZIP_BYTES:
        raise ValidationError(f"zip_path excede {MAX_ZIP_BYTES} bytes")
    return resolved


def import_result_to_dict(result: SessionImportResult) -> dict[str, Any]:
    return {
        "ok": True,
        "kind": "session_import",
        "mode": result.mode,
        "session_id": result.session_id,
        "session_root": str(result.session_root),
        "files_written": result.files_written,
        "skipped_existing": result.skipped_existing,
        "manifest": {
            "format": result.manifest.get("format"),
            "format_version": result.manifest.get("format_version"),
            "source_session_id": result.manifest.get("session_id"),
            "created_at": result.manifest.get("created_at"),
        },
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
        "banner": "session import research-safe — zip-slip/secretos fail-closed · sin LIVE",
    }


def cleanup_temp_upload(path: Path, *, owned: bool) -> None:
    if owned and path.is_file():
        path.unlink(missing_ok=True)


def make_temp_work_dir() -> Path:
    return Path(tempfile.mkdtemp(prefix="ql-session-zip-"))


def rmtree_quiet(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)


def write_export_sidecar_sha(result: SessionExportResult) -> Path:
    """Escribe ``.sha256`` junto al ZIP (atómico)."""
    side = Path(str(result.archive_path) + ".sha256")
    atomic_write_text(side, f"{result.sha256}  {result.archive_path.name}\n")
    return side
