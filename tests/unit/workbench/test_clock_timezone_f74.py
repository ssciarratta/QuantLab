"""Tests timezone settings + status bar clock hooks (F74)."""

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
    ALLOWED_TIMEZONES,
    DEFAULT_TIMEZONE,
    default_settings,
    load_settings,
    normalize_settings,
    save_settings,
)


def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.81.0"
    assert PHASES_SUMMARY == "F19–F89 INTERNAL"
    assert not Path("docs/audit/FASE_74_APPROVED.md").exists()


def test_default_timezone_utc() -> None:
    s = default_settings()
    assert s["timezone"] == "UTC"
    assert DEFAULT_TIMEZONE == "UTC"
    assert frozenset({"UTC", "local"}) == ALLOWED_TIMEZONES


def test_normalize_rejects_bad_timezone() -> None:
    with pytest.raises(ValidationError, match="timezone"):
        normalize_settings({"timezone": "America/New_York"})
    with pytest.raises(ValidationError, match="timezone"):
        normalize_settings({"timezone": "utc"})
    with pytest.raises(ValidationError, match="timezone"):
        normalize_settings({"timezone": True})


def test_save_load_timezone_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    base = default_settings()
    assert base["timezone"] == "UTC"
    saved = save_settings(path, {**base, "timezone": "local"})
    assert saved["timezone"] == "local"
    loaded = load_settings(path)
    assert loaded == saved
    assert loaded["timezone"] == "local"
    saved2 = save_settings(path, {**loaded, "timezone": "UTC"})
    assert load_settings(path)["timezone"] == "UTC"
    assert saved2["timezone"] == "UTC"


def test_legacy_settings_without_timezone_defaults_utc(tmp_path: Path) -> None:
    """Archivos viejos sin la clave → default UTC al normalizar."""
    path = tmp_path / "settings.json"
    path.write_text(
        '{\n  "version": 1,\n  "theme": "slate",\n'
        '  "default_venue": "paper",\n  "default_strategy": "momentum",\n'
        '  "slippage_bps": "0",\n  "locale": "es",\n'
        '  "access_log": true,\n  "auto_backup_minutes": 0,\n'
        '  "desktop_notifications": false,\n'
        '  "sound_alerts": false\n}\n',
        encoding="utf-8",
    )
    loaded = load_settings(path)
    assert loaded["timezone"] == "UTC"


def test_api_put_get_timezone_roundtrip(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "clock-tz")
    state = WorkbenchState(session=session)
    state.ensure_session()
    got0 = handle_get_settings(state)
    assert got0["settings"]["timezone"] == "UTC"
    assert got0["allowed_timezones"] == ["UTC", "local"]

    put = handle_put_settings(state, {"timezone": "local"})
    assert put["ok"] is True
    assert put["live_blocked"] is True
    assert put["settings"]["timezone"] == "local"
    assert session.settings_path.is_file()

    got = handle_get_settings(state)
    assert got["settings"]["timezone"] == "local"

    put2 = handle_put_settings(state, {"timezone": "UTC"})
    assert put2["settings"]["timezone"] == "UTC"
    assert handle_get_settings(state)["settings"]["timezone"] == "UTC"


def test_api_put_rejects_bad_timezone(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "bad-tz")
    state = WorkbenchState(session=session)
    state.ensure_session()
    with pytest.raises(ApiError, match="timezone"):
        handle_put_settings(state, {"timezone": "GMT"})


def test_static_clock_timezone_hook_present() -> None:
    root = Path(__file__).resolve().parents[3]
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
    assert "timezone" in settings_js
    assert "set-timezone" in settings_js
    assert "UTC" in settings_js
    assert "local" in settings_js
    shell = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "shell.js"
    ).read_text(encoding="utf-8")
    assert "setClockTimezone" in shell
    assert "clockTimezone" in shell
    assert 'timeZone: "UTC"' in shell or 'timeZone:"UTC"' in shell or "timeZone" in shell
    assert "settings.timezone" in shell
