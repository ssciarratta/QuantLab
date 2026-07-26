"""Tests Session Auto-Backup (F63) — settings + run_auto_backup + GET /api/backups."""

from __future__ import annotations

import http.client
import json
import time
import zipfile
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from quantlab import __version__
from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import (
    WorkbenchState,
    handle_get_backups,
    handle_put_settings,
)
from quantlab.workbench.auto_backup import (
    MAX_BACKUPS,
    AutoBackupScheduler,
    list_backups,
    rotate_backups,
    run_auto_backup,
)
from quantlab.workbench.server import make_handler
from quantlab.workbench.session import WorkbenchSession
from quantlab.workbench.session_zip import MANIFEST_NAME, export_session
from quantlab.workbench.settings import (
    DEFAULT_AUTO_BACKUP_MINUTES,
    default_settings,
    load_settings,
    normalize_settings,
    parse_auto_backup_minutes,
    save_settings,
)


def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.76.0"
    assert PHASES_SUMMARY == "F19–F84 INTERNAL"
    assert not Path("docs/audit/FASE_63_APPROVED.md").exists()


def test_default_auto_backup_off() -> None:
    s = default_settings()
    assert s["auto_backup_minutes"] == 0
    assert DEFAULT_AUTO_BACKUP_MINUTES == 0


def test_parse_auto_backup_minutes() -> None:
    assert parse_auto_backup_minutes(None) == 0
    assert parse_auto_backup_minutes(0) == 0
    assert parse_auto_backup_minutes(15) == 15
    assert parse_auto_backup_minutes(1440) == 1440
    with pytest.raises(ValidationError):
        parse_auto_backup_minutes(-1)
    with pytest.raises(ValidationError):
        parse_auto_backup_minutes(1441)
    with pytest.raises(ValidationError):
        parse_auto_backup_minutes(True)
    with pytest.raises(ValidationError):
        parse_auto_backup_minutes("5")


def test_normalize_settings_auto_backup(tmp_path: Path) -> None:
    normalized = normalize_settings(
        {
            "version": 1,
            "theme": "slate",
            "default_venue": "paper",
            "default_strategy": "momentum",
            "slippage_bps": "0",
            "locale": "es",
            "access_log": True,
            "auto_backup_minutes": 30,
        }
    )
    assert normalized["auto_backup_minutes"] == 30
    path = tmp_path / "settings.json"
    save_settings(path, normalized)
    loaded = load_settings(path)
    assert loaded["auto_backup_minutes"] == 30


def test_run_auto_backup_writes_zip_and_reuses_allowlist(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "bak63")
    session.save_meta({"session_id": session.session_id, "note": "f63"})
    (session.root / "journal.jsonl").write_text('{"ok":1}\n', encoding="utf-8")
    # Secreto no debe entrar en el ZIP.
    (session.root / ".env").write_text("SECRET=1\n", encoding="utf-8")

    result = run_auto_backup(session)
    assert result.archive_path.is_file()
    assert result.archive_path.parent == (session.root / "backups").resolve()
    assert result.archive_path.name.startswith(f"session_{session.session_id}_")
    assert result.bytes_written > 0

    with zipfile.ZipFile(result.archive_path, "r") as zf:
        names = set(zf.namelist())
        assert MANIFEST_NAME in names
        assert "meta.json" in names or "journal.jsonl" in names
        assert ".env" not in names
        assert not any(n.startswith("backups/") for n in names)


def test_rotation_max_five(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "rot63")
    session.save_meta({"session_id": session.session_id})
    paths: list[Path] = []
    for _ in range(MAX_BACKUPS + 2):
        # Fuerza mtime distinto entre backups.
        result = run_auto_backup(session)
        paths.append(result.archive_path)
        time.sleep(0.02)
    backups = list_backups(session)
    assert backups["count"] == MAX_BACKUPS
    assert backups["max_keep"] == MAX_BACKUPS
    surviving = {Path(b["path"]).resolve() for b in backups["backups"]}
    assert paths[-1].resolve() in surviving
    assert paths[0].resolve() not in surviving


def test_rotate_backups_helper(tmp_path: Path) -> None:
    d = tmp_path / "backups"
    d.mkdir()
    created: list[Path] = []
    for i in range(7):
        p = d / f"session_x_2026010{i}T000000Z.zip"
        p.write_bytes(b"PK\x03\x04fake")
        # bump mtime
        time.sleep(0.01)
        created.append(p)
    removed = rotate_backups(d, max_keep=5)
    assert len(removed) == 2
    assert len(list(d.glob("session_*.zip"))) == 5


def test_list_backups_and_api_handler(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "list63")
    session.save_meta({"session_id": session.session_id})
    empty = list_backups(session)
    assert empty["ok"] is True
    assert empty["kind"] == "backups"
    assert empty["count"] == 0
    assert empty["auto_backup_enabled"] is False
    assert empty["live_routing"] is False

    run_auto_backup(session)
    state = WorkbenchState(session=session, session_parent=tmp_path)
    payload = handle_get_backups(state)
    assert payload["count"] == 1
    assert payload["backups"][0]["filename"].endswith(".zip")
    assert payload["research_safe"] is True


def test_put_settings_auto_backup_minutes(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "set63")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    out = handle_put_settings(state, {"auto_backup_minutes": 10})
    assert out["settings"]["auto_backup_minutes"] == 10
    loaded = load_settings(session.settings_path)
    assert loaded["auto_backup_minutes"] == 10


def test_http_get_backups(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "http63")
    session.save_meta({"session_id": session.session_id})
    run_auto_backup(session)
    state = WorkbenchState(session=session, session_parent=tmp_path)
    handler = make_handler(state)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = __import__("threading").Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        conn = http.client.HTTPConnection(str(host), int(port), timeout=30)
        conn.request("GET", "/api/backups")
        resp = conn.getresponse()
        body: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
        conn.close()
        assert resp.status == 200
        assert body["kind"] == "backups"
        assert body["count"] >= 1
        assert body["live_blocked"] is True
    finally:
        server.shutdown()
        server.server_close()


def test_scheduler_manual_trigger_path(tmp_path: Path) -> None:
    """Scheduler idle con minutes=0; run_auto_backup es el trigger de tests."""
    session = WorkbenchSession.create_or_load(tmp_path, "sched63")
    session.save_meta({"session_id": session.session_id})
    state = WorkbenchState(session=session, session_parent=tmp_path)
    sched = AutoBackupScheduler(state)
    sched.start()
    try:
        assert sched.alive is True
        # Off → no corre backups solos en poll corto.
        time.sleep(0.15)
        assert list_backups(session)["count"] == 0
        result = run_auto_backup(session)
        assert result.archive_path.is_file()
    finally:
        sched.stop()


def test_export_session_excludes_backups_dir(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "excl63")
    session.save_meta({"session_id": session.session_id})
    run_auto_backup(session)
    # Export normal (fuera de backups/) no debe incluir backups/*.zip.
    result = export_session(session, dest_dir=tmp_path / "_zips")
    with zipfile.ZipFile(result.archive_path, "r") as zf:
        assert not any(n.startswith("backups/") for n in zf.namelist())
