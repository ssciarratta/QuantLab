"""Tests Monte Carlo History + Hummingbot Export Wizard (F34)."""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import (
    WorkbenchState,
    handle_get_lab_exports,
    handle_get_lab_montecarlo_history,
    handle_post_lab_export_hb,
    handle_post_lab_montecarlo,
)
from quantlab.workbench.hb_exports import list_hb_exports
from quantlab.workbench.lab_services import run_lab_export_hb, run_lab_montecarlo
from quantlab.workbench.montecarlo_runs import list_montecarlo_runs, persist_montecarlo_run
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


def test_montecarlo_persist_and_ci(tmp_path: Path) -> None:
    root = tmp_path / "montecarlo"
    result = run_lab_montecarlo(
        n_scenarios=4,
        n_bars=16,
        persist=True,
        montecarlo_root=root,
    )
    assert result["ok"] is True
    assert result["persisted"] is True
    assert result["ci_low"] <= result["mean_equity"] <= result["ci_high"]
    assert result["ci_level"] == 0.95
    assert Path(result["path"]).is_file()
    listed = list_montecarlo_runs(root)
    assert listed["count"] >= 1
    assert listed["latest"] is not None
    assert listed["latest"]["ci_low"] == result["ci_low"]


def test_api_montecarlo_history_empty_then_post(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, state = workbench_server
    status, body = _get(server, "/api/lab/montecarlo/history")
    assert status == 200
    assert body["ok"] is True
    assert body["kind"] == "montecarlo_history"
    assert body["count"] == 0
    assert body["persisted"] is False

    st2, run = _post(
        server,
        "/api/lab/montecarlo",
        {"n_scenarios": 3, "n_bars": 12},
    )
    assert st2 == 200
    assert run["ok"] is True
    assert run["kind"] == "montecarlo"
    assert run["persisted"] is True
    assert run["live_blocked"] is True
    assert run["live_routing"] is False
    assert Path(run["path"]).is_file()
    assert state.last_lab_result is not None
    assert state.last_lab_result["persisted"] is True

    st3, listed = _get(server, "/api/lab/montecarlo/history")
    assert st3 == 200
    assert listed["count"] >= 1
    assert listed["persisted"] is True
    assert listed["run_id"] == run["run_id"]
    assert listed["ci_low"] is not None
    assert listed["ci_high"] is not None

    st4, got = _get(server, f"/api/lab/montecarlo/history/{run['run_id']}")
    assert st4 == 200
    assert got["run_id"] == run["run_id"]
    assert got["n_scenarios"] == 3


def test_api_montecarlo_rejects_external_path(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, body = _post(
        server,
        "/api/lab/montecarlo",
        {"n_scenarios": 3, "montecarlo_root": "/tmp/evil"},
    )
    assert status == 400
    assert body["ok"] is False
    assert "path" in body["error"].lower()


def test_export_wizard_and_list(tmp_path: Path) -> None:
    root = tmp_path / "exports"
    result = run_lab_export_hb(root, experiment_id="wb-hb-export", strategy_version="demo-1")
    assert result["ok"] is True
    assert result["live_routing"] is False
    assert result["steps"]["validate"]["ok"] is True
    assert result["steps"]["build"]["ok"] is True
    assert result["steps"]["export"]["ok"] is True
    assert Path(result["path"]).is_file()
    assert Path(result["latest_path"]).is_file()
    assert (root / "wb-hb-export.json").is_file()
    listed = list_hb_exports(root)
    assert listed["count"] >= 2  # hist + latest alias
    assert listed["live_routing"] is False
    assert "live_routing:false" in listed["banner"]
    assert all(e["live_routing"] is False for e in listed["exports"])


def test_api_exports_list(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, empty = _get(server, "/api/lab/exports")
    assert status == 200
    assert empty["ok"] is True
    assert empty["kind"] == "exports"
    assert empty["live_routing"] is False

    st2, run = _post(
        server,
        "/api/lab/export-hb",
        {"experiment_id": "wb-demo-exp", "strategy_version": "v1"},
    )
    assert st2 == 200
    assert run["ok"] is True
    assert run["live_routing"] is False
    assert run["banner"].startswith("live_routing:false")
    assert Path(run["path"]).is_file()

    st3, listed = _get(server, "/api/lab/exports")
    assert st3 == 200
    assert listed["count"] >= 1
    assert listed["live_blocked"] is True
    ids = {e["experiment_id"] for e in listed["exports"]}
    assert "wb-demo-exp" in ids

    st4, got = _get(server, f"/api/lab/exports/{run['export_id']}")
    assert st4 == 200
    assert got["payload"]["live_routing"] is False


def test_handlers_direct(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "f34direct")
    state = WorkbenchState(session=session)
    empty = handle_get_lab_montecarlo_history(state)
    assert empty["persisted"] is False
    assert empty["count"] == 0
    assert "montecarlo" in session.to_dict()
    run = handle_post_lab_montecarlo(state, {"n_scenarios": 3, "n_bars": 12})
    assert run["persisted"] is True
    listed = handle_get_lab_montecarlo_history(state)
    assert listed["count"] >= 1
    assert listed["session_id"] == "f34direct"

    exp = handle_post_lab_export_hb(
        state, {"experiment_id": "wb-hb-export", "strategy_version": "demo-1"}
    )
    assert exp["live_routing"] is False
    exports = handle_get_lab_exports(state)
    assert exports["count"] >= 1
    assert exports["session_id"] == "f34direct"


def test_persist_helper_roundtrip(tmp_path: Path) -> None:
    root = tmp_path / "montecarlo"
    payload = run_lab_montecarlo(n_scenarios=3, n_bars=12, persist=False)
    saved = persist_montecarlo_run(root, payload)
    assert saved["persisted"] is True
    assert (root / saved["run_id"] / "summary.json").is_file()


def test_capabilities_include_mc_history_and_exports(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, body = _get(server, "/api/lab/capabilities")
    assert status == 200
    ids = {f["id"] for f in body["features"]}
    assert "montecarlo" in ids
    assert "montecarlo_history" in ids
    assert "export_hb" in ids
    assert "exports" in ids
    hist = next(f for f in body["features"] if f["id"] == "montecarlo_history")
    assert hist["path"] == "/api/lab/montecarlo/history"
    assert hist["method"] == "GET"
    exports = next(f for f in body["features"] if f["id"] == "exports")
    assert exports["path"] == "/api/lab/exports"
