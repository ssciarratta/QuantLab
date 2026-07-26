"""GET /api/broker/positions, /api/paper/book, /api/session."""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer
from typing import Any

from quantlab.workbench.api import WorkbenchState


def _post_json(
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


def _get_json(conn: http.client.HTTPConnection, path: str) -> tuple[int, dict[str, Any]]:
    conn.request("GET", path)
    resp = conn.getresponse()
    body: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
    return resp.status, body


def test_session_and_book_endpoints(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    conn = http.client.HTTPConnection(host, port, timeout=10)

    status, session_body = _get_json(conn, "/api/session")
    assert status == 200
    assert session_body["ok"] is True
    assert session_body["session"]["session_id"] == state.ensure_session().session_id
    assert session_body["live_blocked"] is True

    status, book_body = _get_json(conn, "/api/paper/book")
    assert status == 200
    assert "cash" in book_body["book"]
    assert book_body["account"]["equity"] is not None

    status, connect_body = _post_json(
        conn,
        "/api/broker/connect",
        {"venue": "binance", "mode": "tester"},
    )
    assert status == 200
    assert connect_body.get("paper_broker") is True

    status, instruments = _get_json(conn, "/api/broker/instruments")
    assert status == 200
    symbol = str(instruments["instruments"][0]["symbol"])

    status, ack_body = _post_json(
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
    assert status == 200
    assert ack_body["ack"]["status"] == "FILLED"
    assert "equity" in ack_body["account"]

    status, pos_body = _get_json(conn, "/api/broker/positions")
    assert status == 200
    positions = pos_body["positions"]
    assert isinstance(positions, list)
    assert any(p["symbol"] == symbol for p in positions)

    status, book_after = _get_json(conn, "/api/paper/book")
    assert status == 200
    assert symbol in book_after["book"]["positions"]
    conn.close()


def test_positions_require_connect(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    conn = http.client.HTTPConnection(host, port, timeout=5)
    status, body = _get_json(conn, "/api/broker/positions")
    conn.close()
    assert status == 400
    assert "conectado" in str(body.get("error", "")).lower()
