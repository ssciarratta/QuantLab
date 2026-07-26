"""Tests Diagnostics snapshot + panel (F95) — agregado read-only para soporte."""

from __future__ import annotations

import json
from pathlib import Path

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import WorkbenchState, handle_get_diagnostics
from quantlab.workbench.commands import list_commands
from quantlab.workbench.session import WorkbenchSession


def _static_root() -> Path:
    return Path(__file__).resolve().parents[3] / "src" / "quantlab" / "workbench" / "static"


def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"
    assert not Path("docs/audit/FASE_95_APPROVED.md").exists()


def test_diagnostics_payload_aggregates(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "diag")
    state = WorkbenchState(session=session, session_parent=tmp_path)

    payload = handle_get_diagnostics(state)

    assert payload["ok"] is True
    assert payload["kind"] == "diagnostics"
    assert payload["version"] == __version__
    assert payload["phases_summary"] == PHASES_SUMMARY
    assert payload["live_blocked"] is True
    assert payload["live_routing"] is False
    assert payload["session_id"] == "diag"
    assert payload["connected_venue"] is None
    assert payload["broker_connected"] is False
    assert set(payload["health"]) == {"status", "checks_ok", "checks_total"}
    assert payload["health"]["checks_total"] >= payload["health"]["checks_ok"]
    assert "status" in payload["reconciliation"]


def test_diagnostics_never_mutates(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "diag2")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    before = state.venue, state.broker, state.paper_kill_engaged

    handle_get_diagnostics(state)
    handle_get_diagnostics(state)

    assert (state.venue, state.broker, state.paper_kill_engaged) == before


def test_command_open_diagnostics() -> None:
    cmd = next(c for c in list_commands()["commands"] if c["id"] == "open.diagnostics")
    assert cmd["pane_id"] == "diagnostics"
    assert cmd["kind"] == "pane"
    assert cmd["safe"] is True
    assert cmd["live"] is False
    assert "diagnostics" in cmd["keywords"]


def test_static_diagnostics_pane_present() -> None:
    root = _static_root()
    index_text = (root / "index.html").read_text(encoding="utf-8")
    assert 'data-open="diagnostics"' in index_text
    assert "panes/diagnostics.js" in index_text

    js = (root / "js" / "panes" / "diagnostics.js").read_text(encoding="utf-8")
    assert "createDiagnosticsPane" in js
    assert "QLApi.diagnostics" in js

    shell_text = (root / "js" / "shell.js").read_text(encoding="utf-8")
    assert "openDiagnostics" in shell_text
    assert "diagnostics: openDiagnostics" in shell_text

    api_text = (root / "js" / "api.js").read_text(encoding="utf-8")
    assert "/api/diagnostics" in api_text

    i18n_text = (root / "js" / "i18n.js").read_text(encoding="utf-8")
    assert '"pane.diagnostics"' in i18n_text


def test_pane_is_strictly_read_only() -> None:
    """DoD F95: el pane solo hace GET /api/diagnostics; sin mutaciones."""
    js = (_static_root() / "js" / "panes" / "diagnostics.js").read_text(encoding="utf-8")
    for verb in ("POST", "PUT", "DELETE", "paperSubmit", "setMode", "QLApi.connect"):
        assert verb not in js
    assert js.count("QLApi.") == js.count("QLApi.diagnostics")


def test_i18n_locales_have_pane_key() -> None:
    for locale in ("es", "en"):
        raw = json.loads(
            (_static_root() / "i18n" / f"{locale}.json").read_text(encoding="utf-8")
        )
        assert "pane.diagnostics" in raw
