"""POST /api/paper/submit vía PaperBroker."""

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


def test_api_paper_submit_and_fills(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    conn = http.client.HTTPConnection(host, port, timeout=10)

    status, connect_body = _post_json(
        conn,
        "/api/broker/connect",
        {"venue": "binance", "mode": "tester"},
    )
    assert status == 200
    assert connect_body.get("paper_broker") is True

    conn.request("GET", "/api/broker/instruments")
    resp = conn.getresponse()
    instruments = json.loads(resp.read().decode("utf-8"))
    assert resp.status == 200
    syms = instruments["instruments"]
    assert isinstance(syms, list) and len(syms) >= 1
    symbol = str(syms[0]["symbol"])

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
    ack = ack_body["ack"]
    assert isinstance(ack, dict)
    assert ack["status"] == "FILLED"

    conn.request("GET", "/api/paper/fills")
    resp = conn.getresponse()
    fills_body = json.loads(resp.read().decode("utf-8"))
    conn.close()
    assert resp.status == 200
    fills = fills_body["fills"]
    assert isinstance(fills, list)
    assert len(fills) >= 1
    assert fills[-1]["symbol"] == symbol


def test_api_paper_submit_requires_connect(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    conn = http.client.HTTPConnection(host, port, timeout=5)
    status, body = _post_json(
        conn,
        "/api/paper/submit",
        {
            "intent_type": "place_order",
            "instrument_id": "X",
            "side": "buy",
            "quantity": "1",
            "order_type": "market",
        },
    )
    conn.close()
    assert status == 400
    err = str(body.get("error", "")).lower()
    assert "conectado" in err or "connect" in err
