"""Tests Session Export/Import ZIP (F39) — zip-slip, secretos, roundtrip."""

from __future__ import annotations

import base64
import http.client
import json
import zipfile
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import (
    ApiError,
    WorkbenchState,
    handle_get_session_export,
    handle_post_session_import,
)
from quantlab.workbench.server import create_server
from quantlab.workbench.session import WorkbenchSession
from quantlab.workbench.session_zip import (
    MANIFEST_NAME,
    export_session,
    import_session_zip,
    is_secret_arcname,
)


def _addr(server: ThreadingHTTPServer) -> tuple[str, int]:
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    return host, port


def _get(server: ThreadingHTTPServer, path: str) -> tuple[int, bytes, str]:
    host, port = _addr(server)
    conn = http.client.HTTPConnection(host, port, timeout=30)
    conn.request("GET", path)
    resp = conn.getresponse()
    raw = resp.read()
    ctype = resp.getheader("Content-Type") or ""
    status = resp.status
    conn.close()
    return status, raw, ctype


def _post_json(
    server: ThreadingHTTPServer, path: str, body: dict[str, Any]
) -> tuple[int, dict[str, Any]]:
    host, port = _addr(server)
    payload = json.dumps(body).encode("utf-8")
    conn = http.client.HTTPConnection(host, port, timeout=30)
    conn.request(
        "POST",
        path,
        body=payload,
        headers={"Content-Type": "application/json", "Content-Length": str(len(payload))},
    )
    resp = conn.getresponse()
    data = json.loads(resp.read().decode("utf-8"))
    status = resp.status
    conn.close()
    return status, data


@pytest.fixture
def session_tree(tmp_path: Path) -> WorkbenchSession:
    parent = tmp_path / "sessions"
    session = WorkbenchSession.create_or_load(parent, "sess39a")
    session.journal_path.write_text('{"fill":1}\n', encoding="utf-8")
    session.settings_path.write_text(
        json.dumps({"version": 1, "theme": "slate", "locale": "es"}) + "\n",
        encoding="utf-8",
    )
    (session.reports_dir / "r1.json").write_text('{"ok":true}\n', encoding="utf-8")
    (session.optimizer_dir / "opt1.json").write_text('{"n":1}\n', encoding="utf-8")
    # Secreto que NO debe exportarse.
    (session.root / ".env").write_text("SECRET=1\n", encoding="utf-8")
    (session.exports_dir / "api_key.txt").write_text("leak\n", encoding="utf-8")
    return session


def test_live_blocked_still_true() -> None:
    assert LIVE_BLOCKED is True


def test_is_secret_arcname() -> None:
    assert is_secret_arcname(".env") is True
    assert is_secret_arcname("exports/api_key.txt") is True
    assert is_secret_arcname("secrets/x.json") is True
    assert is_secret_arcname("settings.json") is False
    assert is_secret_arcname("reports/r1.json") is False


def test_export_skips_secrets(session_tree: WorkbenchSession) -> None:
    result = export_session(session_tree)
    assert result.archive_path.is_file()
    assert result.files_count >= 2
    with zipfile.ZipFile(result.archive_path, "r") as zf:
        names = set(zf.namelist())
    assert MANIFEST_NAME in names
    assert "journal.jsonl" in names
    assert "settings.json" in names
    assert "reports/r1.json" in names
    assert "optimizer/opt1.json" in names
    assert ".env" not in names
    assert "exports/api_key.txt" not in names
    assert any("secret" in e or ".env" in e or "api_key" in e for e in result.excluded_secrets)


def test_roundtrip_new_session(session_tree: WorkbenchSession, tmp_path: Path) -> None:
    result = export_session(session_tree)
    parent = tmp_path / "sessions"
    imported = import_session_zip(
        result.archive_path,
        session_parent=parent,
        mode="new",
        session_id="sess39b",
    )
    assert imported.mode == "new"
    assert imported.session_id == "sess39b"
    assert imported.files_written >= 2
    dest = imported.session_root
    assert (dest / "journal.jsonl").read_text(encoding="utf-8") == '{"fill":1}\n'
    assert (dest / "reports" / "r1.json").is_file()
    assert (dest / "optimizer" / "opt1.json").is_file()
    assert not (dest / ".env").exists()


def test_import_blocks_zip_slip(tmp_path: Path, session_tree: WorkbenchSession) -> None:
    evil = tmp_path / "evil.zip"
    with zipfile.ZipFile(evil, "w") as zf:
        zf.writestr(
            MANIFEST_NAME,
            json.dumps(
                {
                    "format": "quantlab_session_zip",
                    "format_version": 1,
                    "session_id": "evil",
                }
            ),
        )
        zf.writestr("../escape.txt", "pwned")
    with pytest.raises(ValidationError, match="zip-slip"):
        import_session_zip(
            evil,
            session_parent=session_tree.root.parent,
            mode="new",
            session_id="evil39",
        )
    assert not (session_tree.root.parent / "escape.txt").exists()
    assert not (tmp_path / "escape.txt").exists()


def test_import_blocks_secret_member(tmp_path: Path, session_tree: WorkbenchSession) -> None:
    bad = tmp_path / "secret.zip"
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr(
            MANIFEST_NAME,
            json.dumps({"format": "quantlab_session_zip", "format_version": 1}),
        )
        zf.writestr(".env", "SECRET=1\n")
    with pytest.raises(ValidationError, match="secreto"):
        import_session_zip(
            bad,
            session_parent=session_tree.root.parent,
            mode="new",
            session_id="sec39",
        )


def test_merge_fail_closed_on_conflict(session_tree: WorkbenchSession, tmp_path: Path) -> None:
    result = export_session(session_tree)
    with pytest.raises(ValidationError, match="merge fail-closed"):
        import_session_zip(
            result.archive_path,
            session_parent=session_tree.root.parent,
            mode="merge",
            merge_into=session_tree,
        )


def test_merge_additive_ok(session_tree: WorkbenchSession, tmp_path: Path) -> None:
    only = tmp_path / "additive.zip"
    with zipfile.ZipFile(only, "w") as zf:
        zf.writestr(
            MANIFEST_NAME,
            json.dumps({"format": "quantlab_session_zip", "format_version": 1}),
        )
        zf.writestr("reports/extra_f39.json", '{"extra":true}\n')
    imported = import_session_zip(
        only,
        session_parent=session_tree.root.parent,
        mode="merge",
        merge_into=session_tree,
    )
    assert imported.files_written == 1
    assert (session_tree.reports_dir / "extra_f39.json").read_text(encoding="utf-8") == (
        '{"extra":true}\n'
    )


def test_api_export_and_import(tmp_path: Path) -> None:
    parent = tmp_path / "sessions"
    session = WorkbenchSession.create_or_load(parent, "api39")
    (session.reports_dir / "x.json").write_text("{}\n", encoding="utf-8")
    state = WorkbenchState(session=session)
    state.ensure_session()

    exported = handle_get_session_export(state)
    assert exported["ok"] is True
    assert exported["kind"] == "session_export"
    assert exported["live_blocked"] is True
    assert exported["live_routing"] is False
    assert Path(exported["path"]).is_file()

    imported = handle_post_session_import(
        state,
        {"mode": "new", "session_id": "api39b", "zip_path": exported["path"]},
    )
    assert imported["ok"] is True
    assert imported["session_id"] == "api39b"
    assert imported["live_blocked"] is True

    with pytest.raises(ApiError):
        handle_post_session_import(
            state,
            {"mode": "merge", "zip_path": exported["path"]},
        )


def test_http_download_and_base64_import(tmp_path: Path) -> None:
    import threading

    parent = tmp_path / "sessions"
    session = WorkbenchSession.create_or_load(parent, "http39")
    session.journal_path.write_text("j\n", encoding="utf-8")
    state = WorkbenchState(session=session)
    state.ensure_session()
    server = create_server("127.0.0.1", 0, state)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        # Espera breve a que el socket acepte (evita flake en suite completa).
        import time

        time.sleep(0.05)
        status, raw, ctype = _get(server, "/api/session/export")
        assert status == 200, raw.decode("utf-8", errors="replace")
        meta = json.loads(raw.decode("utf-8"))
        assert meta["ok"] is True
        assert "path" in meta

        status, raw, ctype = _get(server, "/api/session/export?download=1")
        assert status == 200, raw.decode("utf-8", errors="replace")
        assert "zip" in ctype
        assert raw[:2] == b"PK"

        b64 = base64.b64encode(raw).decode("ascii")
        status, data = _post_json(
            server,
            "/api/session/import",
            {"mode": "new", "session_id": "http39b", "zip_base64": b64},
        )
        assert status == 200, data
        assert data["ok"] is True
        assert data["session_id"] == "http39b"
    finally:
        server.shutdown()
        server.server_close()


def test_settings_pane_has_export_import() -> None:
    root = Path(__file__).resolve().parents[3]
    settings_js = root / "src/quantlab/workbench/static/js/panes/settings.js"
    api_js = root / "src/quantlab/workbench/static/js/api.js"
    assert settings_js.is_file()
    text = settings_js.read_text(encoding="utf-8")
    assert "set-export" in text
    assert "set-import" in text
    assert "QLApi.sessionExport" in text
    assert "QLApi.sessionImport" in text
    api = api_js.read_text(encoding="utf-8")
    assert "sessionExport" in api
    assert "/api/session/import" in api
