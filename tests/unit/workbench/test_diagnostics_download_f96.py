"""Tests Diagnostics download (F96) — snapshot descargable para soporte."""

from __future__ import annotations

import json
from pathlib import Path

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import WorkbenchState, handle_get_diagnostics_download
from quantlab.workbench.api_catalog import API_ROUTES
from quantlab.workbench.session import WorkbenchSession


def _static_root() -> Path:
    return Path(__file__).resolve().parents[3] / "src" / "quantlab" / "workbench" / "static"


def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.89.0"
    assert PHASES_SUMMARY == "F19–F97 INTERNAL"
    assert not Path("docs/audit/FASE_96_APPROVED.md").exists()


def test_download_returns_json_attachment(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "dl")
    state = WorkbenchState(session=session, session_parent=tmp_path)

    body, filename = handle_get_diagnostics_download(state)

    assert filename == "quantlab-diagnostics-dl.json"
    payload = json.loads(body.decode("utf-8"))
    assert payload["kind"] == "diagnostics"
    assert payload["version"] == __version__
    assert payload["live_blocked"] is True
    assert payload["session_id"] == "dl"


def test_download_filename_is_sanitized(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "s3ss-01")
    state = WorkbenchState(session=session, session_parent=tmp_path)

    _, filename = handle_get_diagnostics_download(state)

    assert filename.startswith("quantlab-diagnostics-")
    assert filename.endswith(".json")
    stem = filename[len("quantlab-diagnostics-") : -len(".json")]
    assert all(ch.isalnum() or ch in "-_" for ch in stem)


def test_route_declared_in_catalog() -> None:
    paths = {(r.path, r.method) for r in API_ROUTES}
    assert ("/api/diagnostics.json", "GET") in paths


def test_pane_has_download_button() -> None:
    js = (_static_root() / "js" / "panes" / "diagnostics.js").read_text(encoding="utf-8")
    assert "/api/diagnostics.json" in js
    assert "download" in js
    api_text = (_static_root() / "js" / "api.js").read_text(encoding="utf-8")
    assert "diagnosticsDownloadUrl" in api_text
