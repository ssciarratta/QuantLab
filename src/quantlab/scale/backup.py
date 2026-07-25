"""Backup local de directorios de experimentos/artifacts (Fase 17)."""

from __future__ import annotations

import shutil
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from quantlab.core.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class BackupResult:
    source: str
    archive_path: str
    files_count: int
    bytes_written: int


def backup_directory(source: Path, dest_dir: Path, *, label: str = "backup") -> BackupResult:
    """Crea un ZIP timestamped del directorio ``source`` dentro de ``dest_dir``."""
    if not source.exists() or not source.is_dir():
        raise ValidationError(f"source no es directorio: {source}")
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    archive = dest_dir / f"{label}_{stamp}.zip"
    count = 0
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                zf.write(path, arcname=str(path.relative_to(source)))
                count += 1
    size = archive.stat().st_size
    return BackupResult(
        source=str(source),
        archive_path=str(archive),
        files_count=count,
        bytes_written=size,
    )


def restore_backup(archive: Path, dest_dir: Path) -> Path:
    """Extrae un ZIP de backup en ``dest_dir`` (debe no existir o estar vacío)."""
    if not archive.is_file():
        raise ValidationError(f"archive inexistente: {archive}")
    dest_dir.mkdir(parents=True, exist_ok=True)
    if any(dest_dir.iterdir()):
        raise ValidationError(f"dest_dir no vacío: {dest_dir}")
    with zipfile.ZipFile(archive, "r") as zf:
        zf.extractall(dest_dir)
    return dest_dir


def copy_tree_backup(source: Path, dest: Path) -> Path:
    """Copia recursiva (sin comprimir) para snapshots rápidos."""
    if dest.exists():
        raise ValidationError(f"dest ya existe: {dest}")
    shutil.copytree(source, dest)
    return dest
