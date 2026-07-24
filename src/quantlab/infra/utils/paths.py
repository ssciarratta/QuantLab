"""Path utilities for project root discovery."""

from __future__ import annotations

from pathlib import Path


def find_project_root(start: Path | None = None) -> Path:
    """Find the project root by looking for pyproject.toml.

    Traverses upward from start (or cwd) until pyproject.toml is found.
    Raises FileNotFoundError if not found.
    """
    current = (start or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    raise FileNotFoundError(f"Could not find project root (pyproject.toml) from {current}")
