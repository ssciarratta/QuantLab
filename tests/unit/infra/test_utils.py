"""Tests for infrastructure utilities — hashing, git, paths."""

from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.infra.utils.git import get_git_commit
from quantlab.infra.utils.hashing import compute_file_hash, compute_lockfile_hash
from quantlab.infra.utils.paths import find_project_root


class TestComputeFileHash:
    def test_deterministic(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        h1 = compute_file_hash(f)
        h2 = compute_file_hash(f)
        assert h1 == h2

    def test_different_content_different_hash(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("hello")
        f2.write_text("world")
        assert compute_file_hash(f1) != compute_file_hash(f2)

    def test_full_hash_not_truncated(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("test content")
        h = compute_file_hash(f)
        assert len(h) == 64  # SHA-256 hex digest


class TestComputeLockfileHash:
    def test_no_lockfile_returns_fallback(self, tmp_path):
        result = compute_lockfile_hash(tmp_path)
        assert result == "no-lockfile-found"

    def test_uses_uv_lock_first(self, tmp_path):
        (tmp_path / "uv.lock").write_text("lockfile content")
        (tmp_path / "pyproject.toml").write_text("[project]")
        result = compute_lockfile_hash(tmp_path)
        assert result == compute_file_hash(tmp_path / "uv.lock")

    def test_falls_back_to_pyproject(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]")
        result = compute_lockfile_hash(tmp_path)
        assert result == compute_file_hash(tmp_path / "pyproject.toml")

    def test_deterministic(self, tmp_path):
        (tmp_path / "uv.lock").write_text("content")
        r1 = compute_lockfile_hash(tmp_path)
        r2 = compute_lockfile_hash(tmp_path)
        assert r1 == r2


class TestGetGitCommit:
    def test_returns_commit_or_unknown(self):
        result = get_git_commit()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_in_git_repo_returns_hash(self):
        result = get_git_commit()
        if result != "unknown":
            assert len(result) == 40


class TestFindProjectRoot:
    def test_finds_root_from_workspace(self):
        root = find_project_root(Path("/workspace"))
        assert (root / "pyproject.toml").exists()

    def test_not_found_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="project root"):
            find_project_root(tmp_path)
