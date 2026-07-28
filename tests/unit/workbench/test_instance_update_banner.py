"""Tests singleton lock + update status (banner / GitHub)."""

from __future__ import annotations

import os
from pathlib import Path

from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.git_update import (
    build_update_status,
    format_es_ar,
    parse_pyproject_version,
)
from quantlab.workbench.instance_lock import (
    claim_singleton,
    clear_lock,
    pid_is_alive,
    read_lock_pid,
    write_lock,
)


def test_live_blocked() -> None:
    assert LIVE_BLOCKED is True


def test_parse_pyproject_version() -> None:
    text = '[project]\nname = "x"\nversion = "1.01.0"\n'
    assert parse_pyproject_version(text) == "1.01.0"


def test_format_es_ar() -> None:
    assert format_es_ar(None) == "—"
    out = format_es_ar("2026-07-27T22:05:00+00:00")
    assert "/" in out
    assert ":" in out


def test_write_read_clear_lock(tmp_path: Path) -> None:
    lock = tmp_path / "workbench.pid"
    write_lock(lock, 424242)
    assert read_lock_pid(lock) == 424242
    clear_lock(lock, only_if_pid=424242)
    assert not lock.exists()


def test_pid_is_alive_self() -> None:
    assert pid_is_alive(os.getpid()) is True
    assert pid_is_alive(-1) is False


def test_claim_singleton_writes_lock(tmp_path: Path) -> None:
    lock = tmp_path / "workbench.pid"
    # Puerto efímero alto improbable en uso
    result = claim_singleton(host="127.0.0.1", port=58765, lock_path=lock)
    assert result["ok"] is True
    assert result["pid"] == os.getpid()
    assert read_lock_pid(lock) == os.getpid()
    clear_lock(lock, only_if_pid=os.getpid())


def test_build_update_status_local_only(monkeypatch: object) -> None:
    monkeypatch.setattr(  # type: ignore[attr-defined]
        "quantlab.workbench.git_update.fetch_github_tip",
        lambda **_kwargs: {
            "ok": True,
            "owner": "ssciarratta",
            "repo": "QuantLab",
            "branch": "main",
            "version": "9.99.0",
            "committed_at": "2026-07-27T20:00:00Z",
            "commit": "abc123def456",
            "source": "github",
            "error": None,
        },
    )
    payload = build_update_status(fetch_remote=True)
    assert payload["ok"] is True
    assert payload["github_version"] == "9.99.0"
    assert payload["update_available"] is True
    assert payload["last_modified_display"]
    assert payload["live_blocked"] is True


def test_working_tree_mtime_beats_stale_git(tmp_path: Path, monkeypatch: object) -> None:
    from quantlab.workbench import git_update as gu

    src = tmp_path / "src" / "quantlab" / "workbench" / "static" / "js"
    src.mkdir(parents=True)
    hot = src / "simulator.js"
    hot.write_text("// fresh", encoding="utf-8")

    monkeypatch.setattr(  # type: ignore[attr-defined]
        gu,
        "local_git_head_info",
        lambda root=None: {
            "commit": "deadbeef",
            "committed_at": "2020-01-01T12:00:00+00:00",
            "subject": "old",
            "branch": "main",
        },
    )
    monkeypatch.setattr(  # type: ignore[attr-defined]
        gu,
        "fetch_github_tip",
        lambda **_kwargs: {"ok": False, "error": "skip", "version": None, "committed_at": None},
    )
    monkeypatch.setattr(  # type: ignore[attr-defined]
        gu,
        "local_pyproject_version",
        lambda root=None: "1.01.0",
    )

    payload = gu.build_update_status(root=tmp_path, fetch_remote=True)
    assert payload["last_modified_source"] == "working_tree"
    assert payload["last_modified_at"]
    assert payload["last_modified_display"] != "—"
    # Debe ser ~ahora, no 2020
    assert "2020" not in payload["last_modified_display"]
