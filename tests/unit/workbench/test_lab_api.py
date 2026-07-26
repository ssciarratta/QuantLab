"""Tests API /api/lab/* — Fase 21 (happy-path + LIVE bloqueado)."""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import WorkbenchState


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


def test_lab_capabilities(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, body = _get(server, "/api/lab/capabilities")
    assert status == 200
    assert body["ok"] is True
    assert body["live_blocked"] is True
    assert body["live_routing"] is False
    assert "backtest" in {f["id"] for f in body["features"]}
    assert "momentum" in body["strategies"]


def test_lab_backtest_momentum(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, state = workbench_server
    status, body = _post(
        server,
        "/api/lab/backtest",
        {"strategy_id": "momentum", "n_bars": 16, "params": {"lookback": 2, "quantity": "1"}},
    )
    assert status == 200
    assert body["ok"] is True
    assert body["kind"] == "backtest"
    assert body["live_routing"] is False
    assert "metrics" in body
    assert body["accounting_ok"] is True
    assert state.last_lab_result is not None
    assert state.last_lab_result["kind"] == "backtest"


def test_lab_scanner(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, body = _post(server, "/api/lab/scanner", {"top_n": 2})
    assert status == 200
    assert body["ok"] is True
    assert body["kind"] == "scanner"
    assert len(body["selected"]) <= 2
    assert len(body["scores"]) >= 1


def test_lab_metrics_empty_then_filled(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, body = _get(server, "/api/lab/metrics")
    assert status == 200
    assert body["has_result"] is False

    st2, _ = _post(server, "/api/lab/features", {"n_bars": 12})
    assert st2 == 200
    status, body = _get(server, "/api/lab/metrics")
    assert status == 200
    assert body["has_result"] is True
    assert body["result"]["kind"] == "features"


def test_lab_experiments_list(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, body = _get(server, "/api/lab/experiments")
    assert status == 200
    assert body["ok"] is True
    assert body["count"] >= 1
    assert any(e["experiment_id"] == "wb-demo-exp" for e in body["experiments"])


def test_lab_optimize(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, body = _post(
        server,
        "/api/lab/optimize",
        {"lookbacks": [2, 3], "quantities": ["1"], "n_bars": 16},
    )
    assert status == 200
    assert body["ok"] is True
    assert body["kind"] == "optimize"
    assert body["n_trials"] == 2
    assert "best" in body
    assert "params" in body["best"]


def test_lab_montecarlo(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, body = _post(
        server,
        "/api/lab/montecarlo",
        {"n_scenarios": 3, "n_bars": 12},
    )
    assert status == 200
    assert body["ok"] is True
    assert body["kind"] == "montecarlo"
    assert body["n_scenarios"] == 3
    assert body["live_blocked"] is True
    assert len(body["final_equities"]) == 3


def test_lab_features(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, body = _post(server, "/api/lab/features", {"n_bars": 15})
    assert status == 200
    assert body["ok"] is True
    assert body["kind"] == "features"
    assert "close_price" in body["series_summary"]
    assert "simple_return" in body["series_summary"]
    assert "log_return" in body["series_summary"]
    assert body["persisted"] is True
    assert body["live_blocked"] is True
    assert isinstance(body["columns"], list)
    assert "log_return" in body["columns"]


def test_lab_export_hb_path_safe(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, body = _post(
        server,
        "/api/lab/export-hb",
        {"experiment_id": "wb-test-hb", "strategy_version": "v1"},
    )
    assert status == 200
    assert body["ok"] is True
    assert body["live_routing"] is False
    assert body["blocked"] is True
    assert Path(body["path"]).is_file()
    exported = json.loads(Path(body["path"]).read_text(encoding="utf-8"))
    assert exported["live_routing"] is False


def test_lab_export_hb_rejects_external_path(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, body = _post(
        server,
        "/api/lab/export-hb",
        {"path": "/tmp/evil.json", "experiment_id": "x"},
    )
    assert status == 400
    assert body["ok"] is False
    assert "path" in body["error"].lower()


def test_lab_validation(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, body = _get(server, "/api/lab/validation")
    assert status == 200
    assert body["ok"] is True
    assert body["kind"] == "validation"
    assert body["train_val_oos"]["train"] > 0
    assert body["walk_forward"]["n_folds"] >= 1


def test_lab_live_still_blocked(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    """Invariante: LIVE_BLOCKED y POST /api/mode live siguen rechazados tras F21."""
    assert LIVE_BLOCKED is True
    server, state = workbench_server
    status, body = _post(server, "/api/mode", {"mode": "live"})
    assert status == 400
    assert body["ok"] is False
    assert "LIVE" in body["error"] or "live" in body["error"].lower()
    assert state.mode.value != "live"

    # Export HB también reporta live_routing false
    st2, hb = _post(server, "/api/lab/export-hb", {})
    assert st2 == 200
    assert hb["live_routing"] is False
    assert hb["live_blocked"] is True
