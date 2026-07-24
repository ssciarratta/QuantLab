"""Hashing utilities for reproducibility.

Computes deterministic hashes from lockfiles, not from the full environment.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def compute_file_hash(path: Path, algorithm: str = "sha256") -> str:
    """Compute the full (non-truncated) hash of a file.

    Returns the complete hex digest to avoid information loss.
    Truncation is intentionally avoided per audit requirements;
    if needed in display contexts, truncate at the caller.
    """
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def compute_lockfile_hash(project_root: Path | None = None) -> str:
    """Compute the hash of the lockfile (uv.lock or fallback).

    Computes from the lockfile itself, not from `pip freeze` output.
    """
    root = project_root or Path(".")
    candidates = ["uv.lock", "requirements.lock", "poetry.lock"]
    for candidate in candidates:
        lockfile = root / candidate
        if lockfile.exists():
            return compute_file_hash(lockfile)
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        return compute_file_hash(pyproject)
    return "no-lockfile-found"
