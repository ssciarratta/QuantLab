"""Tests custom preset DELETE (F81) — builtins protected."""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from quantlab import __version__
from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import (
    ApiError,
    WorkbenchState,
    handle_delete_presets,
    handle_get_presets,
    handle_post_presets_save,
)
from quantlab.workbench.layout import save_layout
from quantlab.workbench.presets import (
    BUILTIN_PRESET_NAMES,
    PRESET_NAMES,
    delete_custom_preset,
    list_presets,
    save_custom_preset,
)
from quantlab.workbench.session import WorkbenchSession


def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.79.0"
    assert PHASES_SUMMARY == "F19–F87 INTERNAL"
    assert not Path("docs/audit/FASE_81_APPROVED.md").exists()


def test_delete_custom_preset_and_protect_builtins(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "preset81")
    save_layout(
        session.layout_path,
        {
            "version": 1,
            "windows": {
                "health": {"x": 10, "y": 10, "w": 400, "h": 300, "z": 1},
            },
        },
    )
    save_custom_preset(session.layout_path, session.presets_dir, "temp_desk")
    path = session.presets_dir / "temp_desk.json"
    assert path.is_file()

    deleted = delete_custom_preset(session.presets_dir, "temp_desk")
    assert deleted["ok"] is True
    assert deleted["kind"] == "preset_deleted"
    assert deleted["preset"]["name"] == "temp_desk"
    assert deleted["preset"]["custom"] is True
    assert not path.exists()

    catalog = list_presets(session.presets_dir)
    assert catalog["custom_count"] == 0
    assert catalog["builtin_count"] == 3

    for builtin in PRESET_NAMES:
        assert builtin in BUILTIN_PRESET_NAMES
        with pytest.raises(ValidationError, match="built-in"):
            delete_custom_preset(session.presets_dir, builtin)

    with pytest.raises(ValidationError, match="no encontrado"):
        delete_custom_preset(session.presets_dir, "missing_desk")


def test_api_handlers_delete_rejects_builtins(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "api81")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    state.ensure_session()
    save_layout(
        session.layout_path,
        {
            "version": 1,
            "windows": {
                "blotter": {"x": 20, "y": 20, "w": 500, "h": 360, "z": 3},
            },
        },
    )

    saved = handle_post_presets_save(state, {"name": "desk_b"})
    assert saved["ok"] is True
    assert (session.presets_dir / "desk_b.json").is_file()

    deleted = handle_delete_presets(state, "desk_b")
    assert deleted["ok"] is True
    assert deleted["kind"] == "preset_deleted"
    assert not (session.presets_dir / "desk_b.json").exists()

    listed = handle_get_presets(state)
    assert listed["custom_count"] == 0
    assert "desk_b" not in listed["names"]

    for builtin in ("research", "trading_paper", "ops"):
        with pytest.raises(ApiError) as exc:
            handle_delete_presets(state, builtin)
        assert exc.value.status == 400
        assert "built-in" in exc.value.message

    with pytest.raises(ApiError) as exc2:
        handle_delete_presets(state, "ghost_desk")
    assert exc2.value.status == 404


def test_http_delete_custom_and_builtin_blocked(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    session = state.ensure_session()
    save_layout(
        session.layout_path,
        {
            "version": 1,
            "windows": {
                "docs": {"x": 30, "y": 30, "w": 480, "h": 400, "z": 5},
            },
        },
    )

    conn = http.client.HTTPConnection(host, port, timeout=5)
    body = json.dumps({"name": "http_del"}).encode("utf-8")
    conn.request(
        "POST",
        "/api/presets/save",
        body=body,
        headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
    )
    resp = conn.getresponse()
    saved = json.loads(resp.read().decode("utf-8"))
    assert resp.status == 200
    assert saved["ok"] is True

    conn.request("DELETE", "/api/presets/http_del")
    resp = conn.getresponse()
    deleted = json.loads(resp.read().decode("utf-8"))
    assert resp.status == 200
    assert deleted["kind"] == "preset_deleted"
    assert not (session.presets_dir / "http_del.json").exists()

    for builtin in ("research", "trading_paper", "ops"):
        conn.request("DELETE", f"/api/presets/{builtin}")
        resp = conn.getresponse()
        payload = json.loads(resp.read().decode("utf-8"))
        assert resp.status == 400
        assert payload["ok"] is False
        assert "built-in" in payload["error"]

    conn.close()


def test_static_ui_has_delete_controls() -> None:
    root = Path(__file__).resolve().parents[3]
    static = root / "src" / "quantlab" / "workbench" / "static"
    api = (static / "js" / "api.js").read_text(encoding="utf-8")
    shell = (static / "js" / "shell.js").read_text(encoding="utf-8")
    css = (static / "css" / "workbench.css").read_text(encoding="utf-8")
    assert "/api/presets/" in api
    assert "deletePreset" in api
    assert "DELETE /api/presets/{name}" in api
    assert "deleteCustomPreset" in shell
    assert "data-preset-delete" in shell
    assert "custom-preset-row" in shell
    assert "custom-preset-row" in css
    assert "preset-delete" in css
