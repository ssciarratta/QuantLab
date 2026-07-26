"""Tests Backups panel UI wiring + POST /api/backups/run (F64)."""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import WorkbenchState, handle_get_backups, handle_post_backups_run
from quantlab.workbench.commands import list_commands
from quantlab.workbench.server import make_handler
from quantlab.workbench.session import WorkbenchSession


def _static_root() -> Path:
    return Path(__file__).resolve().parents[3] / "src" / "quantlab" / "workbench" / "static"


def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.90.0"
    assert PHASES_SUMMARY == "F19–F98 INTERNAL"
    assert not Path("docs/audit/FASE_64_APPROVED.md").exists()


def test_command_open_backups() -> None:
    payload = list_commands()
    ids = {c["id"] for c in payload["commands"]}
    assert "open.backups" in ids
    cmd = next(c for c in payload["commands"] if c["id"] == "open.backups")
    assert cmd["pane_id"] == "backups"
    assert cmd["kind"] == "pane"
    assert cmd["safe"] is True
    assert cmd["live"] is False
    assert "backup" in cmd["keywords"]


def test_static_backups_pane_present() -> None:
    root = _static_root()
    index = root / "index.html"
    pane_js = root / "js" / "panes" / "backups.js"
    shell = root / "js" / "shell.js"
    api = root / "js" / "api.js"
    i18n = root / "js" / "i18n.js"

    assert index.is_file()
    assert pane_js.is_file()

    index_text = index.read_text(encoding="utf-8")
    assert 'data-open="backups"' in index_text
    assert "panes/backups.js" in index_text

    js = pane_js.read_text(encoding="utf-8")
    assert "QLApi.getBackups" in js
    assert "QLApi.runBackup" in js
    assert "Backup ahora" in js
    assert "createBackupsPane" in js

    shell_text = shell.read_text(encoding="utf-8")
    assert "openBackups" in shell_text
    assert "backups: openBackups" in shell_text

    api_text = api.read_text(encoding="utf-8")
    assert "/api/backups" in api_text
    assert "/api/backups/run" in api_text
    assert "getBackups" in api_text
    assert "runBackup" in api_text

    i18n_text = i18n.read_text(encoding="utf-8")
    assert '"pane.backups"' in i18n_text


def test_handle_post_backups_run(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "run64")
    session.save_meta({"session_id": session.session_id})
    state = WorkbenchState(session=session, session_parent=tmp_path)

    empty = handle_get_backups(state)
    assert empty["count"] == 0

    out = handle_post_backups_run(state)
    assert out["ok"] is True
    assert out["kind"] == "backup_run"
    assert out["filename"]
    assert str(out["filename"]).endswith(".zip")
    assert out["count"] >= 1
    assert out["live_blocked"] is True
    assert out["research_safe"] is True
    assert Path(str(out["path"])).is_file()


def test_http_post_backups_run(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "http64")
    session.save_meta({"session_id": session.session_id})
    state = WorkbenchState(session=session, session_parent=tmp_path)
    handler = make_handler(state)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = __import__("threading").Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        conn = http.client.HTTPConnection(str(host), int(port), timeout=30)
        conn.request(
            "POST",
            "/api/backups/run",
            body=b"{}",
            headers={"Content-Type": "application/json"},
        )
        resp = conn.getresponse()
        body: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
        conn.close()
        assert resp.status == 200
        assert body["kind"] == "backup_run"
        assert body["count"] >= 1
        assert body["live_blocked"] is True

        conn2 = http.client.HTTPConnection(str(host), int(port), timeout=30)
        conn2.request("GET", "/api/backups")
        resp2 = conn2.getresponse()
        listed: dict[str, Any] = json.loads(resp2.read().decode("utf-8"))
        conn2.close()
        assert resp2.status == 200
        assert listed["count"] >= 1
    finally:
        server.shutdown()
        server.server_close()
