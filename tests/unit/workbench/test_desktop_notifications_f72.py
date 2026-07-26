"""Tests desktop_notifications settings roundtrip (F72)."""

from __future__ import annotations

from pathlib import Path

import pytest

from quantlab import __version__
from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import (
    ApiError,
    WorkbenchState,
    handle_get_settings,
    handle_put_settings,
)
from quantlab.workbench.session import WorkbenchSession
from quantlab.workbench.settings import (
    DEFAULT_DESKTOP_NOTIFICATIONS,
    default_settings,
    load_settings,
    normalize_settings,
    save_settings,
)


def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.75.0"
    assert PHASES_SUMMARY == "F19–F83 INTERNAL"
    assert not Path("docs/audit/FASE_72_APPROVED.md").exists()


def test_default_desktop_notifications_false() -> None:
    s = default_settings()
    assert s["desktop_notifications"] is False
    assert DEFAULT_DESKTOP_NOTIFICATIONS is False


def test_normalize_rejects_non_bool_desktop_notifications() -> None:
    with pytest.raises(ValidationError, match="desktop_notifications"):
        normalize_settings({"desktop_notifications": "yes"})
    with pytest.raises(ValidationError, match="desktop_notifications"):
        normalize_settings({"desktop_notifications": 1})


def test_save_load_desktop_notifications_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    base = default_settings()
    assert base["desktop_notifications"] is False
    saved = save_settings(path, {**base, "desktop_notifications": True})
    assert saved["desktop_notifications"] is True
    loaded = load_settings(path)
    assert loaded == saved
    assert loaded["desktop_notifications"] is True
    # Toggle back to false
    saved2 = save_settings(path, {**loaded, "desktop_notifications": False})
    assert load_settings(path)["desktop_notifications"] is False
    assert saved2["desktop_notifications"] is False


def test_legacy_settings_without_field_defaults_false(tmp_path: Path) -> None:
    """Archivos viejos sin la clave → default false al normalizar."""
    path = tmp_path / "settings.json"
    path.write_text(
        '{\n  "version": 1,\n  "theme": "slate",\n'
        '  "default_venue": "paper",\n  "default_strategy": "momentum",\n'
        '  "slippage_bps": "0",\n  "locale": "es",\n'
        '  "access_log": true,\n  "auto_backup_minutes": 0\n}\n',
        encoding="utf-8",
    )
    loaded = load_settings(path)
    assert loaded["desktop_notifications"] is False


def test_api_put_get_desktop_notifications_roundtrip(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "desk-notif")
    state = WorkbenchState(session=session)
    state.ensure_session()
    got0 = handle_get_settings(state)
    assert got0["settings"]["desktop_notifications"] is False

    put = handle_put_settings(state, {"desktop_notifications": True})
    assert put["ok"] is True
    assert put["live_blocked"] is True
    assert put["settings"]["desktop_notifications"] is True
    assert session.settings_path.is_file()

    got = handle_get_settings(state)
    assert got["settings"]["desktop_notifications"] is True

    put2 = handle_put_settings(state, {"desktop_notifications": False})
    assert put2["settings"]["desktop_notifications"] is False
    assert handle_get_settings(state)["settings"]["desktop_notifications"] is False


def test_api_put_rejects_bad_desktop_notifications(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "bad-desk")
    state = WorkbenchState(session=session)
    state.ensure_session()
    with pytest.raises(ApiError, match="desktop_notifications"):
        handle_put_settings(state, {"desktop_notifications": "on"})


def test_static_hook_present() -> None:
    root = Path(__file__).resolve().parents[3]
    toasts = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "toasts.js"
    ).read_text(encoding="utf-8")
    assert "setDesktopNotifications" in toasts
    assert "notifyKillEngage" in toasts
    assert "Notification" in toasts
    api = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "api.js"
    ).read_text(encoding="utf-8")
    assert "notifyKillEngage" in api
    settings_js = (
        root
        / "src"
        / "quantlab"
        / "workbench"
        / "static"
        / "js"
        / "panes"
        / "settings.js"
    ).read_text(encoding="utf-8")
    assert "desktop_notifications" in settings_js
    assert "set-desktop-notif" in settings_js
