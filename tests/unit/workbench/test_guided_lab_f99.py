"""Tests Guided Lab wizard pane (F99) — flujo amigable paper-only."""

from __future__ import annotations

import json
from pathlib import Path

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.commands import list_commands


def _static_root() -> Path:
    return Path(__file__).resolve().parents[3] / "src" / "quantlab" / "workbench" / "static"


def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.95.0"
    assert PHASES_SUMMARY == "F19–F103 INTERNAL"
    assert not Path("docs/audit/FASE_99_APPROVED.md").exists()


def test_command_open_guided_lab() -> None:
    cmd = next(c for c in list_commands()["commands"] if c["id"] == "open.guided_lab")
    assert cmd["pane_id"] == "guided_lab"
    assert cmd["kind"] == "pane"
    assert cmd["safe"] is True
    assert cmd["live"] is False
    assert "binance" in cmd["keywords"]


def test_static_guided_lab_pane_present() -> None:
    root = _static_root()
    index_text = (root / "index.html").read_text(encoding="utf-8")
    assert 'data-open="guided_lab"' in index_text
    assert "panes/guided_lab.js" in index_text

    js = (root / "js" / "panes" / "guided_lab.js").read_text(encoding="utf-8")
    assert "createGuidedLabPane" in js
    assert "QLApi.labScanner" in js
    assert "QLApi.labBacktest" in js
    assert "LIVE_BLOCKED" in js
    assert "binance" in js
    assert "a3" in js

    shell_text = (root / "js" / "shell.js").read_text(encoding="utf-8")
    assert "openGuidedLab" in shell_text
    assert "guided_lab: openGuidedLab" in shell_text


def test_pane_never_enables_live() -> None:
    js = (_static_root() / "js" / "panes" / "guided_lab.js").read_text(encoding="utf-8")
    for banned in ("setLive", "flip_live", "place_order", "QLApi.connect"):
        assert banned not in js
    # Lab + live unlock/status + binance MD scan (sin submit venue)
    allowed = (
        js.count("QLApi.labScanner")
        + js.count("QLApi.labBacktest")
        + js.count("QLApi.liveStatus")
        + js.count("QLApi.liveUnlock")
        + js.count("QLApi.liveLock")
        + js.count("QLApi.binanceScan")
    )
    assert js.count("QLApi.") == allowed


def test_i18n_locales_have_pane_key() -> None:
    for locale in ("es", "en"):
        raw = json.loads(
            (_static_root() / "i18n" / f"{locale}.json").read_text(encoding="utf-8")
        )
        assert "pane.guided_lab" in raw
