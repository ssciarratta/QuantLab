"""Fixtures compartidas."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def project_root() -> Path:
    """Raíz del repositorio QuantLab."""
    root = Path(__file__).resolve().parents[1]
    assert (root / "pyproject.toml").exists()
    return root


@pytest.fixture
def config_dir(project_root: Path) -> Path:
    return project_root / "config"
