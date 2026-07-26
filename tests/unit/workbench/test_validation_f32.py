"""Tests Validation / Walk-Forward Runner UI (F32)."""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import (
    WorkbenchState,
    handle_get_lab_validation,
    handle_post_lab_validation_run,
)
from quantlab.workbench.lab_services import run_lab_validation
from quantlab.workbench.session import WorkbenchSession
from quantlab.workbench.validation_runs import list_validation_runs, persist_validation_run


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


def test_run_includes_indices_and_leakage(tmp_path: Path) -> None:
    root = tmp_path / "validation"
    result = run_lab_validation(n_bars=40, persist=True, validation_root=root)
    assert result["ok"] is True
    assert result["persisted"] is True
    assert result["anti_leakage"]["ok"] is True
    assert result["anti_leakage"]["n_checks"] >= 3
    segs = result["train_val_oos"]["segments"]
    assert segs["train"]["start_idx"] == 0
    assert segs["train"]["end_idx"] == segs["train"]["count"] - 1
    assert segs["validation"]["start_idx"] == segs["train"]["count"]
    assert segs["oos"]["start_idx"] == segs["train"]["count"] + segs["validation"]["count"]
    folds = result["walk_forward"]["folds"]
    assert len(folds) >= 1
    assert folds[0]["train_idx"]["start_idx"] == 0
    assert Path(result["path"]).is_file()
    listed = list_validation_runs(root)
    assert listed["count"] >= 1
    assert listed["latest"] is not None


def test_api_get_preview_then_post_persist(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, state = workbench_server
    status, body = _get(server, "/api/lab/validation")
    assert status == 200
    assert body["ok"] is True
    assert body["kind"] == "validation"
    assert body["train_val_oos"]["train"] > 0
    assert body["walk_forward"]["n_folds"] >= 1
    assert "anti_leakage" in body
    assert body["persisted"] is False

    st2, run = _post(
        server,
        "/api/lab/validation/run",
        {"n_bars": 40, "train_size": 10, "test_size": 5},
    )
    assert st2 == 200
    assert run["ok"] is True
    assert run["kind"] == "validation"
    assert run["persisted"] is True
    assert run["live_blocked"] is True
    assert run["live_routing"] is False
    assert run["anti_leakage"]["ok"] is True
    assert Path(run["path"]).is_file()
    assert state.last_lab_result is not None
    assert state.last_lab_result["persisted"] is True

    st3, listed = _get(server, "/api/lab/validation")
    assert st3 == 200
    assert listed["count"] >= 1
    assert listed["persisted"] is True
    assert listed["run_id"] == run["run_id"]

    st4, got = _get(server, f"/api/lab/validation/{run['run_id']}")
    assert st4 == 200
    assert got["run_id"] == run["run_id"]
    assert got["anti_leakage"]["ok"] is True


def test_api_rejects_external_path(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, body = _post(
        server,
        "/api/lab/validation/run",
        {"n_bars": 40, "validation_root": "/tmp/evil"},
    )
    assert status == 400
    assert body["ok"] is False
    assert "path" in body["error"].lower()


def test_handlers_direct(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "f32direct")
    state = WorkbenchState(session=session)
    empty = handle_get_lab_validation(state)
    assert empty["persisted"] is False
    assert empty["anti_leakage"]["ok"] is True
    run = handle_post_lab_validation_run(state, {"n_bars": 30})
    assert run["persisted"] is True
    listed = handle_get_lab_validation(state)
    assert listed["count"] >= 1
    assert listed["session_id"] == "f32direct"


def test_persist_helper_roundtrip(tmp_path: Path) -> None:
    root = tmp_path / "validation"
    payload = run_lab_validation(n_bars=24, persist=False)
    saved = persist_validation_run(root, payload)
    assert saved["persisted"] is True
    assert (root / saved["run_id"] / "summary.json").is_file()


def test_capabilities_include_validation_run(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, body = _get(server, "/api/lab/capabilities")
    assert status == 200
    ids = {f["id"] for f in body["features"]}
    assert "validation" in ids
    assert "validation_list" in ids
    feat = next(f for f in body["features"] if f["id"] == "validation")
    assert feat["path"] == "/api/lab/validation/run"
    assert feat["method"] == "POST"
