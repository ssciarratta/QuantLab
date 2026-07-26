"""Tests Feature Store Browser + Pipeline Runner UI (F31)."""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.features.store import FeatureStore
from quantlab.workbench.api import (
    WorkbenchState,
    handle_get_lab_features_store,
    handle_post_lab_features,
)
from quantlab.workbench.feature_store_browser import (
    DEFAULT_FEATURES_PATH,
    list_feature_artifacts,
    list_feature_store,
    resolve_feature_store_root,
)
from quantlab.workbench.lab_services import run_lab_features
from quantlab.workbench.session import WorkbenchSession


def _addr(server: ThreadingHTTPServer) -> tuple[str, int]:
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    return host, port


def _get(server: ThreadingHTTPServer, path: str) -> tuple[int, dict[str, Any]]:
    host, port = _addr(server)
    conn = http.client.HTTPConnection(host, port, timeout=30)
    conn.request("GET", path)
    resp = conn.getresponse()
    body = json.loads(resp.read().decode("utf-8"))
    conn.close()
    return resp.status, body


def _post(
    server: ThreadingHTTPServer, path: str, payload: dict[str, Any] | None = None
) -> tuple[int, dict[str, Any]]:
    host, port = _addr(server)
    conn = http.client.HTTPConnection(host, port, timeout=60)
    raw = json.dumps(payload or {}).encode("utf-8")
    conn.request(
        "POST",
        path,
        body=raw,
        headers={"Content-Type": "application/json"},
    )
    resp = conn.getresponse()
    body = json.loads(resp.read().decode("utf-8"))
    conn.close()
    return resp.status, body


def test_live_blocked_still_true() -> None:
    assert LIVE_BLOCKED is True


def test_resolve_prefers_session(tmp_path: Path) -> None:
    root, source = resolve_feature_store_root(session_root=tmp_path / "sid")
    assert source == "session"
    assert root is not None
    assert root.name == "features"


def test_list_empty_session_ok(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "f31empty")
    payload = list_feature_store(session_root=session.root)
    assert payload["ok"] is True
    assert payload["read_only"] is True
    assert payload["live_blocked"] is True
    assert payload["source"] == "session"
    assert payload["artifacts"] == []
    assert payload["count"] == 0
    assert DEFAULT_FEATURES_PATH.name == "features"


def test_run_persists_and_lists(tmp_path: Path) -> None:
    store_root = tmp_path / "features"
    result = run_lab_features(n_bars=12, store_root=store_root, persist=True)
    assert result["ok"] is True
    assert result["persisted"] is True
    assert result["store_ref"] is not None
    assert "close_price" in result["columns"]
    assert "simple_return" in result["columns"]
    assert "log_return" in result["columns"]
    assert FeatureStore(store_root).list_versions(result["instrument_id"], result["pipeline_name"])

    arts = list_feature_artifacts(store_root)
    assert len(arts) == 1
    assert arts[0]["pipeline_name"] == "wb_demo_pipeline"
    assert "log_return" in arts[0]["columns"]


def test_api_store_empty_then_run(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, state = workbench_server
    status, body = _get(server, "/api/lab/features/store")
    assert status == 200
    assert body["ok"] is True
    assert body["live_blocked"] is True
    assert body["read_only"] is True
    assert body["source"] == "session"
    assert isinstance(body["artifacts"], list)

    st2, run = _post(server, "/api/lab/features/run", {"n_bars": 10})
    assert st2 == 200
    assert run["ok"] is True
    assert run["kind"] == "features"
    assert run["persisted"] is True
    assert run["live_blocked"] is True
    assert run["live_routing"] is False
    assert Path(run["store_ref"]["path"]).is_file()
    assert state.last_lab_result is not None
    assert state.last_lab_result["persisted"] is True

    st3, store = _get(server, "/api/lab/features/store")
    assert st3 == 200
    assert store["count"] >= 1
    assert any("log_return" in (a.get("columns") or []) for a in store["artifacts"])
    assert "log_return" in store["columns_union"]


def test_api_features_legacy_alias(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, body = _post(server, "/api/lab/features", {"n_bars": 8})
    assert status == 200
    assert body["persisted"] is True
    assert "close_price" in body["series_summary"]


def test_api_rejects_external_store_path(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, body = _post(
        server,
        "/api/lab/features/run",
        {"n_bars": 8, "store_root": "/tmp/evil"},
    )
    assert status == 400
    assert body["ok"] is False
    assert "path" in body["error"].lower()


def test_handlers_direct(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "f31direct")
    state = WorkbenchState(session=session)
    empty = handle_get_lab_features_store(state)
    assert empty["count"] == 0
    run = handle_post_lab_features(state, {"n_bars": 10})
    assert run["persisted"] is True
    listed = handle_get_lab_features_store(state)
    assert listed["count"] == 1
    assert listed["session_id"] == "f31direct"


def test_capabilities_include_store(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, body = _get(server, "/api/lab/capabilities")
    assert status == 200
    ids = {f["id"] for f in body["features"]}
    assert "features" in ids
    assert "features_store" in ids
    feat = next(f for f in body["features"] if f["id"] == "features")
    assert feat["path"] == "/api/lab/features/run"
