"""Tests paper kill switch — POST/GET /api/paper/kill (F70)."""

from __future__ import annotations

import http.client
import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from quantlab import __version__
from quantlab.brokers.mode import OperatingMode
from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import (
    ApiError,
    WorkbenchState,
    handle_get_paper_kill,
    handle_post_broker_connect,
    handle_post_paper_kill,
    handle_post_paper_session_start,
    handle_post_paper_session_step,
    handle_post_paper_submit,
)
from quantlab.workbench.paper_kill import (
    KILL_ENGAGED_MSG,
    is_paper_kill_engaged,
    raise_if_paper_kill_engaged,
)
from quantlab.workbench.server import make_handler
from quantlab.workbench.session import WorkbenchSession


def _static_root() -> Path:
    return Path(__file__).resolve().parents[3] / "src" / "quantlab" / "workbench" / "static"



def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.64.0"
    assert PHASES_SUMMARY == "F19–F72 INTERNAL"
    assert not Path("docs/audit/FASE_70_APPROVED.md").exists()


def test_raise_if_paper_kill_engaged_raises() -> None:
    raise_if_paper_kill_engaged(engaged=False)
    with pytest.raises(ValidationError, match="kill switch engaged"):
        raise_if_paper_kill_engaged(engaged=True)


def test_meta_persistence_and_hydrate(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "kill70")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    assert state.paper_kill_engaged is False
    status = handle_post_paper_kill(state, {"engaged": True})
    assert status["engaged"] is True
    assert state.paper_kill_engaged is True
    meta = session.load_meta()
    assert is_paper_kill_engaged(meta) is True
    assert "paper_kill_updated_at" in meta

    # Rehydrate via new state
    state2 = WorkbenchState(session=None, session_parent=tmp_path)
    state2.switch_session("kill70")
    assert state2.paper_kill_engaged is True
    got = handle_get_paper_kill(state2)
    assert got["engaged"] is True
    assert got["kind"] == "paper_kill"
    assert got["live_blocked"] is True

    handle_post_paper_kill(state2, {"engaged": False})
    assert state2.paper_kill_engaged is False
    assert is_paper_kill_engaged(session.load_meta()) is False


def test_submit_and_step_rejected_when_engaged(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "killblock")
    state = WorkbenchState(
        session=session,
        session_parent=tmp_path,
        mode=OperatingMode.TESTER,
    )
    handle_post_broker_connect(
        state,
        {"venue": "binance", "mode": "tester", "md_source": "fake"},
    )
    handle_post_paper_kill(state, {"engaged": True})

    with pytest.raises(ApiError) as exc_submit:
        handle_post_paper_submit(
            state,
            {
                "intent_type": "place_order",
                "instrument_id": "BTCUSDT",
                "side": "buy",
                "quantity": "1",
                "order_type": "market",
            },
        )
    assert exc_submit.value.status == 400
    assert "kill switch" in str(exc_submit.value)

    # Direct ValidationError from WorkbenchState
    with pytest.raises(ValidationError, match="kill switch"):
        state.assert_paper_kill_clear()

    handle_post_paper_session_start(
        state,
        {
            "strategy_id": "buy_once",
            "symbol": "BTCUSDT",
            "max_steps": 5,
        },
    )
    with pytest.raises(ApiError) as exc_step:
        handle_post_paper_session_step(state)
    assert exc_step.value.status == 400
    assert "kill switch" in str(exc_step.value)

    # Disengage allows submit again
    handle_post_paper_kill(state, {"engaged": False})
    out = handle_post_paper_submit(
        state,
        {
            "intent_type": "place_order",
            "instrument_id": "BTCUSDT",
            "side": "buy",
            "quantity": "1",
            "order_type": "market",
        },
    )
    assert out["ack"]["status"] == "FILLED"


def test_http_paper_kill_roundtrip(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "killhttp")
    state = WorkbenchState(
        session=session,
        session_parent=tmp_path,
        mode=OperatingMode.TESTER,
    )
    handler = make_handler(state)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    conn = http.client.HTTPConnection(str(host), int(port), timeout=10)
    try:
        conn.request("GET", "/api/paper/kill")
        resp = conn.getresponse()
        body: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
        assert resp.status == 200
        assert body["engaged"] is False

        raw = json.dumps({"engaged": True}).encode("utf-8")
        conn.request(
            "POST",
            "/api/paper/kill",
            body=raw,
            headers={"Content-Type": "application/json"},
        )
        resp = conn.getresponse()
        body = json.loads(resp.read().decode("utf-8"))
        assert resp.status == 200
        assert body["engaged"] is True

        # Connect + blocked submit
        raw = json.dumps({"venue": "binance", "mode": "tester"}).encode("utf-8")
        conn.request(
            "POST",
            "/api/broker/connect",
            body=raw,
            headers={"Content-Type": "application/json"},
        )
        assert conn.getresponse().read()  # drain

        raw = json.dumps(
            {
                "intent_type": "place_order",
                "instrument_id": "BTCUSDT",
                "side": "buy",
                "quantity": "1",
                "order_type": "market",
            }
        ).encode("utf-8")
        conn.request(
            "POST",
            "/api/paper/submit",
            body=raw,
            headers={"Content-Type": "application/json"},
        )
        resp = conn.getresponse()
        err = json.loads(resp.read().decode("utf-8"))
        assert resp.status == 400
        assert "kill switch" in err.get("error", "")
        assert KILL_ENGAGED_MSG.split("—")[0].strip() in err.get("error", "") or "kill" in err.get(
            "error", ""
        )
    finally:
        conn.close()
        server.shutdown()


def test_ui_contains_kill_button() -> None:
    static = _static_root()
    risk_js = (static / "js" / "panes" / "risk.js").read_text(encoding="utf-8")
    session_js = (static / "js" / "panes" / "paper_session.js").read_text(encoding="utf-8")
    api_js = (static / "js" / "api.js").read_text(encoding="utf-8")
    css = (static / "css" / "workbench.css").read_text(encoding="utf-8")
    assert "ENGAGE KILL" in risk_js
    assert "setPaperKill" in risk_js
    assert "ENGAGE KILL" in session_js
    assert "/api/paper/kill" in api_js
    assert "button.btn.danger" in css
