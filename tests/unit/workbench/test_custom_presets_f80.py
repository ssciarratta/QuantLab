"""Tests custom preset save + list/apply (F80)."""

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
    WorkbenchState,
    handle_get_presets,
    handle_post_presets_apply,
    handle_post_presets_save,
)
from quantlab.workbench.layout import load_layout, save_layout
from quantlab.workbench.presets import (
    PRESET_NAMES,
    apply_preset,
    get_preset,
    list_presets,
    save_custom_preset,
    validate_preset_name,
)
from quantlab.workbench.session import WorkbenchSession


def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.90.0"
    assert PHASES_SUMMARY == "F19–F98 INTERNAL"
    assert not Path("docs/audit/FASE_80_APPROVED.md").exists()


def test_validate_preset_name_rejects_builtin_and_bad() -> None:
    assert validate_preset_name("my_desk") == "my_desk"
    with pytest.raises(ValidationError, match="built-in"):
        validate_preset_name("research")
    with pytest.raises(ValidationError, match="inválido"):
        validate_preset_name("../escape")
    with pytest.raises(ValidationError, match="inválido"):
        validate_preset_name("1bad")


def test_save_list_apply_custom(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "preset80")
    layout = {
        "version": 1,
        "windows": {
            "health": {"x": 10, "y": 10, "w": 400, "h": 300, "z": 1},
            "market": {"x": 420, "y": 10, "w": 400, "h": 300, "z": 2},
        },
    }
    save_layout(session.layout_path, layout)

    saved = save_custom_preset(session.layout_path, session.presets_dir, "my_desk")
    assert saved["ok"] is True
    assert saved["preset"]["custom"] is True
    assert saved["preset"]["name"] == "my_desk"
    path = session.presets_dir / "my_desk.json"
    assert path.is_file()
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["custom"] is True
    assert set(raw["windows"].keys()) == {"health", "market"}

    catalog = list_presets(session.presets_dir)
    assert catalog["builtin_count"] == 3
    assert catalog["custom_count"] == 1
    assert catalog["count"] == 4
    names = {p["name"] for p in catalog["presets"]}
    assert names == set(PRESET_NAMES) | {"my_desk"}
    custom = next(p for p in catalog["presets"] if p["name"] == "my_desk")
    assert custom["custom"] is True

    # Change layout, then apply custom → restore saved windows.
    save_layout(
        session.layout_path,
        {"version": 1, "windows": {"chat": {"x": 1, "y": 1, "w": 300, "h": 200}}},
    )
    applied = apply_preset(session.layout_path, "my_desk", session.presets_dir)
    assert applied["ok"] is True
    assert applied["preset"]["custom"] is True
    loaded = load_layout(session.layout_path)
    assert set(loaded["windows"].keys()) == {"health", "market"}
    assert "chat" not in loaded["windows"]

    preset = get_preset("my_desk", session.presets_dir)
    assert preset["custom"] is True
    assert set(preset["window_ids"]) == {"health", "market"}


def test_api_handlers_save_list_apply(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "api80")
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

    listed0 = handle_get_presets(state)
    assert listed0["custom_count"] == 0
    assert listed0["count"] == 3

    saved = handle_post_presets_save(state, {"name": "desk_a"})
    assert saved["ok"] is True
    assert saved["preset"]["name"] == "desk_a"
    assert (session.presets_dir / "desk_a.json").is_file()

    listed = handle_get_presets(state)
    assert listed["custom_count"] == 1
    assert listed["count"] == 4
    assert "desk_a" in listed["names"]

    # Apply builtin still works.
    builtin = handle_post_presets_apply(state, {"name": "ops"})
    assert builtin["preset"]["name"] == "ops"
    assert builtin["preset"]["custom"] is False

    custom = handle_post_presets_apply(state, {"name": "desk_a"})
    assert custom["ok"] is True
    assert custom["preset"]["custom"] is True
    assert set(custom["layout"]["windows"].keys()) == {"blotter"}


def test_api_save_rejects_builtin_and_missing(tmp_path: Path) -> None:
    from quantlab.workbench.api import ApiError

    session = WorkbenchSession.create_or_load(tmp_path, "bad80")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    state.ensure_session()
    with pytest.raises(ApiError) as exc:
        handle_post_presets_save(state, {})
    assert exc.value.status == 400
    with pytest.raises(ApiError) as exc2:
        handle_post_presets_save(state, {"name": "research"})
    assert exc2.value.status == 400


def test_http_save_list_apply(
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
                "settings": {"x": 520, "y": 30, "w": 400, "h": 360, "z": 6},
            },
        },
    )

    conn = http.client.HTTPConnection(host, port, timeout=5)
    body = json.dumps({"name": "http_desk"}).encode("utf-8")
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
    assert saved["preset"]["custom"] is True

    conn.request("GET", "/api/presets")
    resp = conn.getresponse()
    listed = json.loads(resp.read().decode("utf-8"))
    assert resp.status == 200
    assert listed["custom_count"] == 1
    assert "http_desk" in listed["names"]

    body2 = json.dumps({"name": "http_desk"}).encode("utf-8")
    conn.request(
        "POST",
        "/api/presets/apply",
        body=body2,
        headers={"Content-Type": "application/json", "Content-Length": str(len(body2))},
    )
    resp = conn.getresponse()
    applied = json.loads(resp.read().decode("utf-8"))
    conn.close()
    assert resp.status == 200
    assert applied["preset"]["name"] == "http_desk"
    assert set(applied["layout"]["windows"].keys()) == {"docs", "settings"}
    assert (session.presets_dir / "http_desk.json").is_file()


def test_static_ui_has_save_controls() -> None:
    root = Path(__file__).resolve().parents[3]
    static = root / "src" / "quantlab" / "workbench" / "static"
    html = (static / "index.html").read_text(encoding="utf-8")
    api = (static / "js" / "api.js").read_text(encoding="utf-8")
    shell = (static / "js" / "shell.js").read_text(encoding="utf-8")
    assert 'id="btn-preset-save"' in html
    assert 'id="custom-presets"' in html
    assert "/api/presets/save" in api
    assert "savePreset" in api
    assert "saveCurrentAsPreset" in shell
    assert "refreshPresetsMenu" in shell
