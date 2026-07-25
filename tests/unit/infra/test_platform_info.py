"""Tests de get_git_commit / hash_dependencies / sha256_hex / python version."""

from __future__ import annotations

import hashlib
import subprocess
import sys
from unittest.mock import MagicMock

import pytest

from quantlab.infra.utils.platform_info import (
    get_git_commit,
    get_python_version,
    hash_dependencies,
    sha256_hex,
)


def test_get_python_version_matches_sys() -> None:
    assert get_python_version() == sys.version.split()[0]
    assert get_python_version().count(".") >= 1


def test_sha256_hex_known_payload() -> None:
    data = b"quantlab-platform"
    assert sha256_hex(data) == hashlib.sha256(data).hexdigest()
    assert len(sha256_hex(b"")) == 64


def test_hash_dependencies_is_stable_hex16() -> None:
    h1 = hash_dependencies()
    h2 = hash_dependencies()
    assert h1 == h2
    assert len(h1) == 16
    assert all(c in "0123456789abcdef" for c in h1)


def test_get_git_commit_success(monkeypatch: pytest.MonkeyPatch) -> None:
    mock = MagicMock()
    mock.stdout = "abc123deadbeef\n"
    mock.returncode = 0

    def _run(*_a: object, **_k: object) -> MagicMock:
        return mock

    monkeypatch.setattr(subprocess, "run", _run)
    assert get_git_commit() == "abc123deadbeef"


def test_get_git_commit_fallback_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_a: object, **_k: object) -> MagicMock:
        raise subprocess.CalledProcessError(128, "git")

    monkeypatch.setattr(subprocess, "run", _boom)
    assert get_git_commit() == "unknown"
    assert get_git_commit(default="n/a") == "n/a"


def test_get_git_commit_fallback_on_oserror(monkeypatch: pytest.MonkeyPatch) -> None:
    def _missing(*_a: object, **_k: object) -> MagicMock:
        raise FileNotFoundError("git")

    monkeypatch.setattr(subprocess, "run", _missing)
    assert get_git_commit(default="offline") == "offline"
