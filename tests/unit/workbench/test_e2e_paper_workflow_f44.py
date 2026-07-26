"""F44 — E2E Paper Workflow Integration (API workbench, sin browser).

Flujo completo en un thread de servidor loopback:
  boot → mode paper → connect binance tester → submit → positions/book →
  paper session buy_once + step → backtest + reports → validation +
  optimize + mc (mini) → export HB → session zip → LIVE still blocked.
"""

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


def _get(conn: http.client.HTTPConnection, path: str) -> tuple[int, dict[str, Any] | bytes, str]:
    conn.request("GET", path)
    resp = conn.getresponse()
    raw = resp.read()
    ctype = resp.getheader("Content-Type") or ""
    if "json" in ctype or path.startswith("/api/") and "download" not in path:
        try:
            return resp.status, json.loads(raw.decode("utf-8")), ctype
        except json.JSONDecodeError:
            return resp.status, raw, ctype
    return resp.status, raw, ctype


def _post(
    conn: http.client.HTTPConnection, path: str, payload: dict[str, Any]
) -> tuple[int, dict[str, Any]]:
    raw = json.dumps(payload).encode("utf-8")
    conn.request(
        "POST",
        path,
        body=raw,
        headers={"Content-Type": "application/json"},
    )
    resp = conn.getresponse()
    body: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
    return resp.status, body


def test_live_blocked_invariant_f44() -> None:
    assert LIVE_BLOCKED is True


def test_e2e_paper_workflow_full_api(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    """Integración end-to-end paper vía HTTP loopback (sin browser)."""
    assert LIVE_BLOCKED is True
    server, state = workbench_server
    host, port = _addr(server)
    conn = http.client.HTTPConnection(host, port, timeout=120)

    try:
        # 1) Health / boot
        st, health, _ = _get(conn, "/api/health")
        assert st == 200
        assert isinstance(health, dict)
        assert health.get("ok") is True
        assert health.get("live_blocked") is True

        # 2) Set mode paper
        st, mode_body = _post(conn, "/api/mode", {"mode": "paper"})
        assert st == 200, mode_body
        assert mode_body["mode"] == "paper"
        assert mode_body["live_blocked"] is True
        assert state.mode.value == "paper"

        # 3) Connect venue binance (tester) — PaperBroker
        st, connect = _post(
            conn,
            "/api/broker/connect",
            {"venue": "binance", "mode": "tester"},
        )
        assert st == 200, connect
        assert connect.get("ok") is True or connect.get("paper_broker") is True
        assert connect.get("paper_broker") is True
        assert connect.get("live_blocked", True) is True
        assert connect.get("live_routing", False) is False

        # Venue a3 también resoluble en tester (smoke del registry)
        st_a3, connect_a3 = _post(
            conn,
            "/api/broker/connect",
            {"venue": "a3", "mode": "tester", "md_source": "fake"},
        )
        assert st_a3 == 200, connect_a3
        assert connect_a3.get("paper_broker") is True

        # Reconectar binance para el resto del flujo paper
        st, connect = _post(
            conn,
            "/api/broker/connect",
            {"venue": "binance", "mode": "tester"},
        )
        assert st == 200, connect

        st, instruments, _ = _get(conn, "/api/broker/instruments")
        assert st == 200
        assert isinstance(instruments, dict)
        syms = instruments["instruments"]
        assert isinstance(syms, list) and len(syms) >= 1
        symbol = str(syms[0]["symbol"])

        # 4) Submit paper order
        st, submit = _post(
            conn,
            "/api/paper/submit",
            {
                "intent_type": "place_order",
                "instrument_id": symbol,
                "side": "buy",
                "quantity": "1",
                "order_type": "market",
            },
        )
        assert st == 200, submit
        assert submit["ack"]["status"] == "FILLED"
        assert "account" in submit

        # 5) Positions + book
        st, positions, _ = _get(conn, "/api/broker/positions")
        assert st == 200
        assert isinstance(positions, dict)
        assert isinstance(positions.get("positions"), list)
        assert len(positions["positions"]) >= 1

        st, book, _ = _get(conn, "/api/paper/book")
        assert st == 200
        assert isinstance(book, dict)
        assert "cash" in book["book"]
        assert book["account"]["equity"] is not None

        # 6) Paper session buy_once + step
        st, start = _post(
            conn,
            "/api/paper/session/start",
            {"strategy_id": "buy_once", "symbol": symbol, "max_steps": 5},
        )
        assert st == 200, start
        assert start["ok"] is True
        assert start["live_blocked"] is True
        assert start["live_routing"] is False
        assert start["status"]["running"] is True

        st, step = _post(conn, "/api/paper/session/step", {})
        assert st == 200, step
        assert step["step"] == 1
        assert step.get("live_routing") is False

        st, sess_status, _ = _get(conn, "/api/paper/session/status")
        assert st == 200
        assert isinstance(sess_status, dict)
        assert sess_status["steps"] == 1
        assert sess_status["strategy_id"] == "buy_once"

        st, stop = _post(conn, "/api/paper/session/stop", {})
        assert st == 200, stop
        assert stop["status"]["running"] is False

        # 7) Backtest + list reports
        st, bt = _post(
            conn,
            "/api/lab/backtest",
            {
                "strategy_id": "momentum",
                "n_bars": 16,
                "params": {"lookback": 2, "quantity": "1"},
                "experiment_id": "f44-e2e-bt",
            },
        )
        assert st == 200, bt
        assert bt["ok"] is True
        assert bt["kind"] == "backtest"
        assert bt["live_routing"] is False
        assert "metrics" in bt

        st, reports, _ = _get(conn, "/api/lab/reports")
        assert st == 200
        assert isinstance(reports, dict)
        assert reports.get("count", 0) >= 1 or len(reports.get("reports", [])) >= 1

        # 8) Validation + optimize + mc (mini)
        st, val = _post(
            conn,
            "/api/lab/validation/run",
            {"n_bars": 40, "train_size": 10, "test_size": 5},
        )
        assert st == 200, val
        assert val["ok"] is True
        assert val["kind"] == "validation"
        assert val["live_blocked"] is True
        assert val["live_routing"] is False

        st, opt = _post(
            conn,
            "/api/lab/optimize",
            {
                "lookbacks": [2, 3],
                "quantities": ["1"],
                "n_bars": 16,
                "persist": True,
            },
        )
        assert st == 200, opt
        assert opt["ok"] is True
        assert opt["kind"] == "optimize"
        assert opt["live_routing"] is False

        st, mc = _post(
            conn,
            "/api/lab/montecarlo",
            {
                "n_scenarios": 3,
                "n_bars": 12,
                "noise_bps": 5.0,
                "persist": True,
            },
        )
        assert st == 200, mc
        assert mc["ok"] is True
        assert mc["kind"] == "montecarlo"
        assert mc["live_routing"] is False

        # 9) Export HB
        st, hb = _post(
            conn,
            "/api/lab/export-hb",
            {"experiment_id": "f44-e2e-hb", "strategy_version": "demo-f44"},
        )
        assert st == 200, hb
        assert hb["ok"] is True
        assert hb["kind"] == "export_hb"
        assert hb.get("live_routing", False) is False

        st, exports, _ = _get(conn, "/api/lab/exports")
        assert st == 200
        assert isinstance(exports, dict)
        assert exports.get("count", 0) >= 1 or len(exports.get("exports", [])) >= 1

        # 10) Export session zip
        st, zip_meta, _ = _get(conn, "/api/session/export")
        assert st == 200
        assert isinstance(zip_meta, dict)
        assert zip_meta["ok"] is True
        zip_path = Path(str(zip_meta["path"]))
        assert zip_path.is_file()
        assert zip_path.suffix == ".zip"

        st, zip_raw, ctype = _get(conn, "/api/session/export?download=1")
        assert st == 200
        assert isinstance(zip_raw, (bytes, bytearray))
        assert zip_raw[:2] == b"PK"
        assert "zip" in ctype.lower() or len(zip_raw) > 20

        # 11) LIVE still blocked / mode live rejected
        st, live_rej = _post(conn, "/api/mode", {"mode": "live"})
        assert st == 400, live_rej
        assert live_rej.get("ok") is False
        err = str(live_rej.get("error", "")).lower()
        assert "live" in err
        assert LIVE_BLOCKED is True
        assert state.mode.value != "live"

        st, health2, _ = _get(conn, "/api/health")
        assert st == 200
        assert isinstance(health2, dict)
        assert health2.get("live_blocked") is True
    finally:
        conn.close()
