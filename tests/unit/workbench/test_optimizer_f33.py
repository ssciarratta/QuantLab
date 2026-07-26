"""Tests Optimizer History + Pareto Panel (F33)."""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import (
    WorkbenchState,
    handle_get_lab_optimize_history,
    handle_post_lab_optimize,
)
from quantlab.workbench.lab_services import run_lab_optimize
from quantlab.workbench.optimizer_runs import list_optimizer_runs, persist_optimizer_run
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


def test_run_includes_pareto_and_persist(tmp_path: Path) -> None:
    root = tmp_path / "optimizer"
    result = run_lab_optimize(
        lookbacks=(2, 3, 4),
        quantities=("1",),
        n_bars=20,
        persist=True,
        optimizer_root=root,
    )
    assert result["ok"] is True
    assert result["persisted"] is True
    assert result["n_trials"] == 3
    assert result["pareto"] is not None
    assert result["pareto"]["n_front"] >= 1
    assert result["pareto"]["objectives"][0]["key"] == "sharpe"
    assert result["pareto"]["objectives"][1]["key"] == "max_drawdown"
    assert "metrics" in result["history"][0]
    assert "max_drawdown" in result["history"][0]["metrics"]
    assert Path(result["path"]).is_file()
    listed = list_optimizer_runs(root)
    assert listed["count"] >= 1
    assert listed["latest"] is not None


def test_api_history_empty_then_post_persist(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, state = workbench_server
    status, body = _get(server, "/api/lab/optimize/history")
    assert status == 200
    assert body["ok"] is True
    assert body["kind"] == "optimize_history"
    assert body["count"] == 0
    assert body["persisted"] is False

    st2, run = _post(
        server,
        "/api/lab/optimize",
        {"lookbacks": [2, 3], "quantities": ["1"], "n_bars": 16},
    )
    assert st2 == 200
    assert run["ok"] is True
    assert run["kind"] == "optimize"
    assert run["persisted"] is True
    assert run["live_blocked"] is True
    assert run["live_routing"] is False
    assert run["pareto"] is not None
    assert run["pareto"]["n_front"] >= 1
    assert Path(run["path"]).is_file()
    assert state.last_lab_result is not None
    assert state.last_lab_result["persisted"] is True

    st3, listed = _get(server, "/api/lab/optimize/history")
    assert st3 == 200
    assert listed["count"] >= 1
    assert listed["persisted"] is True
    assert listed["run_id"] == run["run_id"]
    assert listed["pareto"] is not None

    st4, got = _get(server, f"/api/lab/optimize/history/{run['run_id']}")
    assert st4 == 200
    assert got["run_id"] == run["run_id"]
    assert got["pareto"]["n_front"] >= 1


def test_api_rejects_external_path(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, body = _post(
        server,
        "/api/lab/optimize",
        {"lookbacks": [2], "optimizer_root": "/tmp/evil"},
    )
    assert status == 400
    assert body["ok"] is False
    assert "path" in body["error"].lower()


def test_handlers_direct(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "f33direct")
    state = WorkbenchState(session=session)
    empty = handle_get_lab_optimize_history(state)
    assert empty["persisted"] is False
    assert empty["count"] == 0
    assert "optimizer" in session.to_dict()
    run = handle_post_lab_optimize(state, {"lookbacks": [2, 3], "quantities": ["1"], "n_bars": 16})
    assert run["persisted"] is True
    listed = handle_get_lab_optimize_history(state)
    assert listed["count"] >= 1
    assert listed["session_id"] == "f33direct"


def test_persist_helper_roundtrip(tmp_path: Path) -> None:
    root = tmp_path / "optimizer"
    payload = run_lab_optimize(lookbacks=(2, 3), n_bars=16, persist=False)
    saved = persist_optimizer_run(root, payload)
    assert saved["persisted"] is True
    assert (root / saved["run_id"] / "summary.json").is_file()


def test_capabilities_include_optimize_history(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, body = _get(server, "/api/lab/capabilities")
    assert status == 200
    ids = {f["id"] for f in body["features"]}
    assert "optimize" in ids
    assert "optimize_history" in ids
    hist = next(f for f in body["features"] if f["id"] == "optimize_history")
    assert hist["path"] == "/api/lab/optimize/history"
    assert hist["method"] == "GET"
