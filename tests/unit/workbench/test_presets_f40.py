"""Tests workspace presets + API GET/POST /api/presets (F40)."""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import (
    WorkbenchState,
    handle_get_presets,
    handle_post_presets_apply,
)
from quantlab.workbench.layout import load_layout
from quantlab.workbench.presets import (
    PRESET_NAMES,
    apply_preset,
    get_preset,
    layout_for_preset,
    list_presets,
)
from quantlab.workbench.session import WorkbenchSession


def test_live_blocked_still_true() -> None:
    assert LIVE_BLOCKED is True


def test_builtin_preset_names() -> None:
    assert PRESET_NAMES == ("research", "trading_paper", "ops")
    catalog = list_presets()
    assert catalog["ok"] is True
    assert catalog["count"] == 3
    assert catalog["live_blocked"] is True
    assert catalog["live_routing"] is False
    assert catalog["research_safe"] is True
    names = {p["name"] for p in catalog["presets"]}
    assert names == set(PRESET_NAMES)


def test_research_windows() -> None:
    preset = get_preset("research")
    assert set(preset["window_ids"]) == {"health", "backtest", "reports", "chat"}


def test_trading_paper_windows() -> None:
    preset = get_preset("trading_paper")
    assert set(preset["window_ids"]) == {
        "market",
        "blotter",
        "positions",
        "paper_session",
        "risk",
    }


def test_ops_windows() -> None:
    preset = get_preset("ops")
    assert set(preset["window_ids"]) == {"health", "settings", "docs", "catalog"}


def test_unknown_preset_rejected() -> None:
    with pytest.raises(ValidationError, match="preset desconocido"):
        get_preset("live_desk")


def test_apply_writes_layout_json(tmp_path: Path) -> None:
    path = tmp_path / "layout.json"
    # Seed unrelated windows — apply must replace entirely.
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "windows": {"scanner": {"x": 1, "y": 1, "w": 300, "h": 200}},
            }
        ),
        encoding="utf-8",
    )
    result = apply_preset(path, "research")
    assert result["ok"] is True
    assert result["live_blocked"] is True
    assert result["preset"]["name"] == "research"
    loaded = load_layout(path)
    assert set(loaded["windows"].keys()) == {"health", "backtest", "reports", "chat"}
    assert "scanner" not in loaded["windows"]
    assert loaded["windows"]["health"]["w"] == 420


def test_layout_for_preset_version() -> None:
    layout = layout_for_preset("ops")
    assert layout["version"] == 1
    assert "settings" in layout["windows"]


def test_api_handlers(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "preset-api")
    state = WorkbenchState(session=session)
    state.ensure_session()

    listed = handle_get_presets(state)
    assert listed["ok"] is True
    assert listed["session_id"] == "preset-api"
    assert listed["count"] == 3

    applied = handle_post_presets_apply(state, {"name": "trading_paper"})
    assert applied["ok"] is True
    assert applied["live_blocked"] is True
    assert applied["preset"]["name"] == "trading_paper"
    assert set(applied["layout"]["windows"].keys()) == {
        "market",
        "blotter",
        "positions",
        "paper_session",
        "risk",
    }
    assert session.layout_path.is_file()


def test_api_apply_missing_name(tmp_path: Path) -> None:
    from quantlab.workbench.api import ApiError

    session = WorkbenchSession.create_or_load(tmp_path, "preset-bad")
    state = WorkbenchState(session=session)
    state.ensure_session()
    with pytest.raises(ApiError) as exc:
        handle_post_presets_apply(state, {})
    assert exc.value.status == 400


def test_api_apply_unknown(tmp_path: Path) -> None:
    from quantlab.workbench.api import ApiError

    session = WorkbenchSession.create_or_load(tmp_path, "preset-unk")
    state = WorkbenchState(session=session)
    state.ensure_session()
    with pytest.raises(ApiError) as exc:
        handle_post_presets_apply(state, {"name": "not_a_preset"})
    assert exc.value.status == 400


def test_http_get_post_presets(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)

    conn = http.client.HTTPConnection(host, port, timeout=5)
    conn.request("GET", "/api/presets")
    resp = conn.getresponse()
    listed = json.loads(resp.read().decode("utf-8"))
    assert resp.status == 200
    assert listed["ok"] is True
    assert listed["count"] == 3
    assert listed["live_blocked"] is True

    body = json.dumps({"name": "ops"}).encode("utf-8")
    conn.request(
        "POST",
        "/api/presets/apply",
        body=body,
        headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
    )
    resp = conn.getresponse()
    applied = json.loads(resp.read().decode("utf-8"))
    conn.close()
    assert resp.status == 200
    assert applied["ok"] is True
    assert applied["preset"]["name"] == "ops"
    assert set(applied["layout"]["windows"].keys()) == {
        "health",
        "settings",
        "docs",
        "catalog",
    }
    layout_path = state.ensure_session().layout_path
    assert layout_path.is_file()
    loaded = load_layout(layout_path)
    assert "docs" in loaded["windows"]


def test_http_apply_invalid(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    body = json.dumps({"name": "live"}).encode("utf-8")
    conn = http.client.HTTPConnection(host, port, timeout=5)
    conn.request(
        "POST",
        "/api/presets/apply",
        body=body,
        headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
    )
    resp = conn.getresponse()
    payload = json.loads(resp.read().decode("utf-8"))
    conn.close()
    assert resp.status == 400
    assert payload["ok"] is False
