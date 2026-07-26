"""Tests API Explorer panel (F94) — navegador read-only del catálogo OpenAPI."""

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
    assert __version__ == "0.87.0"
    assert PHASES_SUMMARY == "F19–F95 INTERNAL"
    assert not Path("docs/audit/FASE_94_APPROVED.md").exists()


def test_command_open_api_explorer() -> None:
    payload = list_commands()
    cmd = next(c for c in payload["commands"] if c["id"] == "open.api_explorer")
    assert cmd["pane_id"] == "api_explorer"
    assert cmd["kind"] == "pane"
    assert cmd["safe"] is True
    assert cmd["live"] is False
    assert "openapi" in cmd["keywords"]


def test_static_api_explorer_pane_present() -> None:
    root = _static_root()
    index_text = (root / "index.html").read_text(encoding="utf-8")
    assert 'data-open="api_explorer"' in index_text
    assert "panes/api_explorer.js" in index_text

    js = (root / "js" / "panes" / "api_explorer.js").read_text(encoding="utf-8")
    assert "createApiExplorerPane" in js
    assert "QLApi.openapi" in js

    shell_text = (root / "js" / "shell.js").read_text(encoding="utf-8")
    assert "openApiExplorer" in shell_text
    assert "api_explorer: openApiExplorer" in shell_text

    api_text = (root / "js" / "api.js").read_text(encoding="utf-8")
    assert "/api/openapi.json" in api_text

    i18n_text = (root / "js" / "i18n.js").read_text(encoding="utf-8")
    assert '"pane.api_explorer"' in i18n_text


def test_pane_is_strictly_read_only() -> None:
    """DoD F94: el pane solo hace GET /api/openapi.json; sin mutaciones."""
    js = (_static_root() / "js" / "panes" / "api_explorer.js").read_text(encoding="utf-8")
    for verb in ("POST", "PUT", "DELETE", "paperSubmit", "setMode", "QLApi.connect"):
        assert verb not in js
    assert js.count("QLApi.") == js.count("QLApi.openapi")


def test_i18n_locales_have_pane_key() -> None:
    for locale in ("es", "en"):
        raw = json.loads(
            (_static_root() / "i18n" / f"{locale}.json").read_text(encoding="utf-8")
        )
        assert "pane.api_explorer" in raw
