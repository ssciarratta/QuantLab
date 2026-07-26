"""Tests sound_alerts settings roundtrip (F73)."""

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
    DEFAULT_SOUND_ALERTS,
    default_settings,
    load_settings,
    normalize_settings,
    save_settings,
)


def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.85.0"
    assert PHASES_SUMMARY == "F19–F93 INTERNAL"
    assert not Path("docs/audit/FASE_73_APPROVED.md").exists()


def test_default_sound_alerts_false() -> None:
    s = default_settings()
    assert s["sound_alerts"] is False
    assert DEFAULT_SOUND_ALERTS is False


def test_normalize_rejects_non_bool_sound_alerts() -> None:
    with pytest.raises(ValidationError, match="sound_alerts"):
        normalize_settings({"sound_alerts": "yes"})
    with pytest.raises(ValidationError, match="sound_alerts"):
        normalize_settings({"sound_alerts": 1})


def test_save_load_sound_alerts_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    base = default_settings()
    assert base["sound_alerts"] is False
    saved = save_settings(path, {**base, "sound_alerts": True})
    assert saved["sound_alerts"] is True
    loaded = load_settings(path)
    assert loaded == saved
    assert loaded["sound_alerts"] is True
    # Toggle back to false
    saved2 = save_settings(path, {**loaded, "sound_alerts": False})
    assert load_settings(path)["sound_alerts"] is False
    assert saved2["sound_alerts"] is False


def test_legacy_settings_without_field_defaults_false(tmp_path: Path) -> None:
    """Archivos viejos sin la clave → default false al normalizar."""
    path = tmp_path / "settings.json"
    path.write_text(
        '{\n  "version": 1,\n  "theme": "slate",\n'
        '  "default_venue": "paper",\n  "default_strategy": "momentum",\n'
        '  "slippage_bps": "0",\n  "locale": "es",\n'
        '  "access_log": true,\n  "auto_backup_minutes": 0,\n'
        '  "desktop_notifications": false\n}\n',
        encoding="utf-8",
    )
    loaded = load_settings(path)
    assert loaded["sound_alerts"] is False


def test_api_put_get_sound_alerts_roundtrip(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "sound-alerts")
    state = WorkbenchState(session=session)
    state.ensure_session()
    got0 = handle_get_settings(state)
    assert got0["settings"]["sound_alerts"] is False

    put = handle_put_settings(state, {"sound_alerts": True})
    assert put["ok"] is True
    assert put["live_blocked"] is True
    assert put["settings"]["sound_alerts"] is True
    assert session.settings_path.is_file()

    got = handle_get_settings(state)
    assert got["settings"]["sound_alerts"] is True

    put2 = handle_put_settings(state, {"sound_alerts": False})
    assert put2["settings"]["sound_alerts"] is False
    assert handle_get_settings(state)["settings"]["sound_alerts"] is False


def test_api_put_rejects_bad_sound_alerts(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "bad-sound")
    state = WorkbenchState(session=session)
    state.ensure_session()
    with pytest.raises(ApiError, match="sound_alerts"):
        handle_put_settings(state, {"sound_alerts": "on"})


def test_static_webaudio_hook_present() -> None:
    root = Path(__file__).resolve().parents[3]
    toasts = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "toasts.js"
    ).read_text(encoding="utf-8")
    assert "setSoundAlerts" in toasts
    assert "playBeep" in toasts
    assert "AudioContext" in toasts
    assert "notifyKillEngage" in toasts
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
    assert "sound_alerts" in settings_js
    assert "set-sound-alerts" in settings_js
    shell = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "shell.js"
    ).read_text(encoding="utf-8")
    assert "setSoundAlerts" in shell
    assert "sound_alerts" in shell
