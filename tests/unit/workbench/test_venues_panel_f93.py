"""Tests Venues / Broker Registry panel (F93)."""

from __future__ import annotations

import json
from pathlib import Path

from quantlab import __version__
from quantlab.brokers.contracts.v1 import (
    BROKER_PLUGIN_API_VERSION,
    BROKER_PLUGIN_CAPABILITIES,
)
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import WorkbenchState, handle_get_venues
from quantlab.workbench.commands import list_commands
from quantlab.workbench.session import WorkbenchSession


def _static_root() -> Path:
    return Path(__file__).resolve().parents[3] / "src" / "quantlab" / "workbench" / "static"


def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.94.0"
    assert PHASES_SUMMARY == "F19–F102 INTERNAL"
    assert not Path("docs/audit/FASE_93_APPROVED.md").exists()


def test_venues_payload_enriched(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "venues")
    state = WorkbenchState(session=session, session_parent=tmp_path)

    payload = handle_get_venues(state)

    assert set(payload["venues"]) >= {"a3", "binance", "paper", "generic_csv", "generic_rest"}
    assert isinstance(payload["plugin_venues"], list)
    assert payload["connected_venue"] is None
    assert payload["md_provider"] is None
    assert payload["mode"] in {"tester", "paper", "real"}
    assert payload["live_blocked"] is True

    contract = payload["plugin_contract"]
    assert contract["api_version"] == BROKER_PLUGIN_API_VERSION
    assert contract["allowed_capabilities"] == sorted(BROKER_PLUGIN_CAPABILITIES)
    assert contract["read_only_wrapper"] == "ReadOnlyBrokerPort"
    assert contract["execution"] == "blocked"


def test_command_open_venues() -> None:
    payload = list_commands()
    cmd = next(c for c in payload["commands"] if c["id"] == "open.venues")
    assert cmd["pane_id"] == "venues"
    assert cmd["kind"] == "pane"
    assert cmd["safe"] is True
    assert cmd["live"] is False
    assert "brokers" in cmd["keywords"]


def test_static_venues_pane_present() -> None:
    root = _static_root()
    index_text = (root / "index.html").read_text(encoding="utf-8")
    assert 'data-open="venues"' in index_text
    assert "panes/venues.js" in index_text

    js = (root / "js" / "panes" / "venues.js").read_text(encoding="utf-8")
    assert "createVenuesPane" in js
    assert "QLApi.venues" in js
    assert "plugin_contract" in js

    shell_text = (root / "js" / "shell.js").read_text(encoding="utf-8")
    assert "openVenues" in shell_text
    assert "venues: openVenues" in shell_text

    i18n_text = (root / "js" / "i18n.js").read_text(encoding="utf-8")
    assert '"pane.venues"' in i18n_text


def test_pane_is_strictly_read_only() -> None:
    """DoD F93: el pane solo consulta /api/venues; sin mutaciones."""
    js = (_static_root() / "js" / "panes" / "venues.js").read_text(encoding="utf-8")
    for verb in ("POST", "PUT", "DELETE", "QLApi.connect", "paperSubmit", "setMode"):
        assert verb not in js
    assert js.count("QLApi.") == js.count("QLApi.venues")


def test_i18n_locales_have_pane_key() -> None:
    for locale in ("es", "en"):
        raw = json.loads(
            (_static_root() / "i18n" / f"{locale}.json").read_text(encoding="utf-8")
        )
        assert "pane.venues" in raw
