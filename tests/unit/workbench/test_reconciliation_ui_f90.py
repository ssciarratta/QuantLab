"""Tests Reconciliación Paper panel UI wiring (F90)."""

from __future__ import annotations

from pathlib import Path

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.commands import list_commands


def _static_root() -> Path:
    return Path(__file__).resolve().parents[3] / "src" / "quantlab" / "workbench" / "static"


def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.85.0"
    assert PHASES_SUMMARY == "F19–F93 INTERNAL"
    assert not Path("docs/audit/FASE_90_APPROVED.md").exists()


def test_command_open_reconciliation() -> None:
    payload = list_commands()
    ids = {c["id"] for c in payload["commands"]}
    assert "open.reconciliation" in ids
    cmd = next(c for c in payload["commands"] if c["id"] == "open.reconciliation")
    assert cmd["pane_id"] == "reconciliation"
    assert cmd["kind"] == "pane"
    assert cmd["safe"] is True
    assert cmd["live"] is False
    assert "reconciliation" in cmd["keywords"]


def test_static_reconciliation_pane_present() -> None:
    root = _static_root()
    index = root / "index.html"
    pane_js = root / "js" / "panes" / "reconciliation.js"
    shell = root / "js" / "shell.js"
    api = root / "js" / "api.js"
    i18n = root / "js" / "i18n.js"

    assert index.is_file()
    assert pane_js.is_file()

    index_text = index.read_text(encoding="utf-8")
    assert 'data-open="reconciliation"' in index_text
    assert "panes/reconciliation.js" in index_text

    js = pane_js.read_text(encoding="utf-8")
    assert "createReconciliationPane" in js
    assert "QLApi.paperReconciliation" in js
    assert "rebuild_via" in js
    assert "recon-auto" in js

    shell_text = shell.read_text(encoding="utf-8")
    assert "openReconciliation" in shell_text
    assert "reconciliation: openReconciliation" in shell_text

    api_text = api.read_text(encoding="utf-8")
    assert "/api/paper/reconciliation" in api_text
    assert "paperReconciliation" in api_text

    i18n_text = i18n.read_text(encoding="utf-8")
    assert '"pane.reconciliation"' in i18n_text


def test_pane_never_mutates_files() -> None:
    """DoD F90/F91: la UI nunca reconstruye archivos ni toca órdenes.

    Única acción permitida además del GET: rehydrate (F91), que relee la
    sesión desde disco sin mutar journal/book.
    """
    js = (_static_root() / "js" / "panes" / "reconciliation.js").read_text(encoding="utf-8")
    for verb in ("PUT", "DELETE", "setPaperKill", "paperSubmit", "rebuild_session"):
        assert verb not in js
    allowed = js.count("QLApi.paperReconciliation") + js.count("QLApi.paperRehydrate")
    assert js.count("QLApi.") == allowed
    # El rehydrate pide confirmación explícita al operador.
    assert "confirm(" in js


def test_i18n_locales_have_pane_key() -> None:
    import json

    for locale in ("es", "en"):
        raw = json.loads(
            (_static_root() / "i18n" / f"{locale}.json").read_text(encoding="utf-8")
        )
        assert "pane.reconciliation" in raw
