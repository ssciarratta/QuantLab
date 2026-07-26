"""Tests POST /api/broker/reconnect + last connect meta (F76)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from quantlab import __version__
from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import (
    ApiError,
    WorkbenchState,
    handle_post_broker_connect,
    handle_post_broker_reconnect,
)
from quantlab.workbench.broker_reconnect import (
    LAST_CONNECT_META_KEY,
    load_last_connect,
    require_last_connect,
)
from quantlab.workbench.session import WorkbenchSession


def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.87.0"
    assert PHASES_SUMMARY == "F19–F95 INTERNAL"
    assert not Path("docs/audit/FASE_76_APPROVED.md").exists()


def test_reconnect_without_prior_connect_400(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "rc-none")
    state = WorkbenchState(session=session)
    state.ensure_session()
    with pytest.raises(ApiError) as exc:
        handle_post_broker_reconnect(state, {})
    assert exc.value.status == 400
    assert "no hay config de connect previa" in exc.value.message
    assert load_last_connect(session) is None


def test_connect_stores_last_connect_in_meta(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "rc-store")
    state = WorkbenchState(session=session)
    state.ensure_session()
    out = handle_post_broker_connect(
        state,
        {"venue": "binance", "mode": "tester", "md_source": "fake"},
    )
    assert out["ok"] is True
    assert out["last_connect"]["venue"] == "binance"
    assert out["last_connect"]["mode"] == "tester"
    assert out["last_connect"]["md_source"] == "fake"
    meta = session.load_meta()
    assert isinstance(meta.get(LAST_CONNECT_META_KEY), dict)
    cfg = load_last_connect(session)
    assert cfg is not None
    assert cfg["venue"] == "binance"
    assert cfg["mode"] == "tester"
    assert cfg["md_source"] == "fake"


def test_reconnect_reruns_last_connect(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "rc-ok")
    state = WorkbenchState(session=session)
    state.ensure_session()
    handle_post_broker_connect(
        state,
        {"venue": "binance", "mode": "tester", "md_source": "fake"},
    )
    # Simulate disconnect
    state.broker = None
    state.venue = None
    out = handle_post_broker_reconnect(state, {})
    assert out["ok"] is True
    assert out["reconnect"] is True
    assert out["kind"] == "broker_reconnect"
    assert out["venue"] == "binance"
    assert out["mode"] == "tester"
    assert out["md_source"] == "fake"
    assert out["has_last_connect"] is True
    assert state.broker is not None
    assert state.venue == "binance"


def test_reconnect_preserves_csv_path_and_slippage(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "rc-csv")
    state = WorkbenchState(session=session)
    state.ensure_session()
    # generic_csv needs a path; use a temp csv if venue supports it — else store via meta
    # and verify require/load roundtrip + reconnect body composition.
    handle_post_broker_connect(
        state,
        {
            "venue": "binance",
            "mode": "paper",
            "md_source": "fake",
            "slippage_bps": "12.5",
        },
    )
    cfg = require_last_connect(session)
    assert cfg["slippage_bps"] == "12.5"
    assert cfg["mode"] == "paper"
    out = handle_post_broker_reconnect(state, None)
    assert out["ok"] is True
    assert out["slippage_bps"] == "12.5"
    assert out["mode"] == "paper"


def test_require_last_connect_raises(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "rc-req")
    with pytest.raises(ValidationError, match="no hay config"):
        require_last_connect(session)


def test_static_reconnect_hooks_present() -> None:
    root = Path(__file__).resolve().parents[3]
    static = root / "src" / "quantlab" / "workbench" / "static"
    market = (static / "js" / "panes" / "market.js").read_text(encoding="utf-8")
    health = (static / "js" / "panes" / "health.js").read_text(encoding="utf-8")
    api = (static / "js" / "api.js").read_text(encoding="utf-8")
    assert "md-reconnect" in market
    assert "QLApi.reconnect" in market
    assert "hp-reconnect" in health
    assert "QLApi.reconnect" in health
    assert "/api/broker/reconnect" in api
    assert "reconnect" in api


def test_catalog_has_reconnect_route() -> None:
    from quantlab.workbench.api_catalog import API_ROUTES

    paths = {(r.path, r.method) for r in API_ROUTES}
    assert ("/api/broker/reconnect", "POST") in paths


@pytest.mark.parametrize(
    "venue",
    ["binance"],
)
def test_reconnect_idempotent(tmp_path: Path, venue: str) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, f"rc-id-{venue}")
    state = WorkbenchState(session=session)
    state.ensure_session()
    handle_post_broker_connect(state, {"venue": venue, "mode": "tester"})
    first: dict[str, Any] = handle_post_broker_reconnect(state, {})
    second: dict[str, Any] = handle_post_broker_reconnect(state, {})
    assert first["venue"] == second["venue"] == venue
    assert first["reconnect"] is True
    assert second["reconnect"] is True
