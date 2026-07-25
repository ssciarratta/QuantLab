"""Utilidades de plataforma, git y hashing."""

from __future__ import annotations

import hashlib
import platform
import subprocess
import sys
from importlib.metadata import distributions


def get_platform_info() -> str:
    """Retorna descripción de plataforma para manifests."""
    return platform.platform()


def get_python_version() -> str:
    """Versión de Python en ejecución."""
    return sys.version.split()[0]


def get_git_commit(default: str = "unknown") -> str:
    """Obtiene commit git actual o default si no hay repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return default


def hash_dependencies() -> str:
    """Hash determinista de dependencias instaladas."""
    lines: list[str] = []
    for dist in sorted(distributions(), key=lambda d: d.metadata["Name"].lower()):
        name = dist.metadata["Name"]
        version = dist.version
        lines.append(f"{name}=={version}")
    payload = "\n".join(lines).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def sha256_hex(data: bytes) -> str:
    """SHA-256 hex de bytes."""
    return hashlib.sha256(data).hexdigest()
