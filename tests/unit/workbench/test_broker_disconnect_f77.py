"""Tests POST /api/broker/disconnect + keep last_connect (F77)."""

from __future__ import annotations

from pathlib import Path

import pytest

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import (
    WorkbenchState,
    handle_get_broker_heartbeat,
    handle_post_broker_connect,
    handle_post_broker_disconnect,
    handle_post_broker_reconnect,
)
from quantlab.workbench.broker_reconnect import LAST_CONNECT_META_KEY, load_last_connect
from quantlab.workbench.session import WorkbenchSession


def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.76.0"
    assert PHASES_SUMMARY == "F19–F84 INTERNAL"
    assert not Path("docs/audit/FASE_77_APPROVED.md").exists()


def test_disconnect_idempotent_when_not_connected(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "dc-none")
    state = WorkbenchState(session=session)
    state.ensure_session()
    out = handle_post_broker_disconnect(state, {})
    assert out["ok"] is True
    assert out["disconnect"] is True
    assert out["kind"] == "broker_disconnect"
    assert out["was_connected"] is False
    assert out["connected"] is False
    assert out["has_last_connect"] is False
    assert out["live_blocked"] is True
    assert state.broker is None


def test_disconnect_clears_broker_keeps_last_connect(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "dc-ok")
    state = WorkbenchState(session=session)
    state.ensure_session()
    handle_post_broker_connect(
        state,
        {"venue": "binance", "mode": "tester", "md_source": "fake"},
    )
    assert state.broker is not None
    assert state.venue == "binance"
    cfg_before = load_last_connect(session)
    assert cfg_before is not None
    assert cfg_before["venue"] == "binance"

    out = handle_post_broker_disconnect(state, None)
    assert out["ok"] is True
    assert out["disconnect"] is True
    assert out["was_connected"] is True
    assert out["previous_venue"] == "binance"
    assert out["connected"] is False
    assert out["has_last_connect"] is True
    assert out["last_connect"]["venue"] == "binance"
    assert state.broker is None
    assert state.venue is None
    assert state.md_provider is None
    assert state.md_source is None
    # meta intacta
    meta = session.load_meta()
    assert isinstance(meta.get(LAST_CONNECT_META_KEY), dict)
    cfg_after = load_last_connect(session)
    assert cfg_after == cfg_before


def test_reconnect_after_disconnect(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "dc-rc")
    state = WorkbenchState(session=session)
    state.ensure_session()
    handle_post_broker_connect(
        state,
        {"venue": "binance", "mode": "tester", "md_source": "fake"},
    )
    handle_post_broker_disconnect(state, {})
    assert state.broker is None
    out = handle_post_broker_reconnect(state, {})
    assert out["ok"] is True
    assert out["reconnect"] is True
    assert out["venue"] == "binance"
    assert state.broker is not None
    assert state.venue == "binance"


def test_heartbeat_disconnected_after_disconnect(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "dc-hb")
    state = WorkbenchState(session=session)
    state.ensure_session()
    handle_post_broker_connect(state, {"venue": "binance", "mode": "tester"})
    handle_post_broker_disconnect(state, {})
    hb = handle_get_broker_heartbeat(state)
    assert hb["status"] == "disconnected"
    assert hb["connected"] is False


def test_static_disconnect_hooks_present() -> None:
    root = Path(__file__).resolve().parents[3]
    static = root / "src" / "quantlab" / "workbench" / "static"
    market = (static / "js" / "panes" / "market.js").read_text(encoding="utf-8")
    health = (static / "js" / "panes" / "health.js").read_text(encoding="utf-8")
    api = (static / "js" / "api.js").read_text(encoding="utf-8")
    assert "md-disconnect" in market
    assert "QLApi.disconnect" in market
    assert "hp-disconnect" in health
    assert "QLApi.disconnect" in health
    assert "/api/broker/disconnect" in api
    assert "disconnect" in api


def test_catalog_has_disconnect_route() -> None:
    from quantlab.workbench.api_catalog import API_ROUTES

    paths = {(r.path, r.method) for r in API_ROUTES}
    assert ("/api/broker/disconnect", "POST") in paths


@pytest.mark.parametrize("body", [{}, None])
def test_disconnect_accepts_empty_body(tmp_path: Path, body: dict[str, object] | None) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "dc-body")
    state = WorkbenchState(session=session)
    state.ensure_session()
    handle_post_broker_connect(state, {"venue": "binance", "mode": "paper"})
    out = handle_post_broker_disconnect(state, body)  # type: ignore[arg-type]
    assert out["ok"] is True
    assert out["disconnect"] is True
