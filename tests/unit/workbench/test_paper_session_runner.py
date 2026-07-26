"""Tests PaperSessionRunner + API /api/paper/session/* (F26)."""

from __future__ import annotations

import http.client
import json
from datetime import UTC, datetime
from decimal import Decimal
from http.server import ThreadingHTTPServer
from typing import Any

import pytest

from quantlab.brokers.paper.book import PaperBook
from quantlab.brokers.paper.broker import PaperBroker
from quantlab.brokers.types import (
    BrokerAccount,
    BrokerAck,
    BrokerInstrument,
    BrokerPosition,
    BrokerSnapshot,
)
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.orders import OrderIntent
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.paper_session import (
    PaperSessionConfig,
    PaperSessionRunner,
    build_session_strategy,
)
from quantlab.workbench.risk import PaperRiskLimits


class _MdStub:
    """MD stub: snapshot fijo; submit/cancel venue = AssertionError."""

    def __init__(self, symbol: str = "TEST", last: str = "100") -> None:
        self.symbol = symbol
        self.submit_calls = 0
        self.cancel_calls = 0
        self._last = Decimal(last)
        self._snap = BrokerSnapshot(
            symbol=symbol,
            bid=self._last - Decimal("1"),
            ask=self._last + Decimal("1"),
            last=self._last,
            ts=datetime(2024, 6, 1, 12, 0, tzinfo=UTC),
        )

    @property
    def venue_id(self) -> str:
        return "md-stub"

    def connect(self) -> dict[str, object]:
        return {"ok": True}

    def close(self) -> dict[str, object]:
        return {"ok": True}

    def health(self) -> dict[str, object]:
        return {"ok": True}

    def list_instruments(self) -> list[BrokerInstrument]:
        return [
            BrokerInstrument(
                symbol=self.symbol,
                description="t",
                currency="USD",
                status="ACTIVE",
            )
        ]

    def get_snapshot(self, symbol: str) -> BrokerSnapshot:
        return self._snap

    def get_account(self) -> BrokerAccount:
        return BrokerAccount(cash=Decimal("1"), currency="USD")

    def get_positions(self) -> list[BrokerPosition]:
        return []

    def submit(self, intent: OrderIntent) -> BrokerAck:
        self.submit_calls += 1
        raise AssertionError("must never call md submit (LIVE blocked path)")

    def cancel(self, order_id: str) -> BrokerAck:
        self.cancel_calls += 1
        raise AssertionError("must never call md cancel")


def _runner(
    *,
    risk: PaperRiskLimits | None = None,
    cash: Decimal = Decimal("100000"),
) -> tuple[PaperSessionRunner, _MdStub, PaperBroker, PaperBook]:
    md = _MdStub()
    book = PaperBook(initial_cash=cash)
    broker = PaperBroker(md, book=book)
    runner = PaperSessionRunner(broker, risk or PaperRiskLimits(), book)
    return runner, md, broker, book


def test_live_blocked_invariant() -> None:
    assert LIVE_BLOCKED is True


def test_runner_rejects_non_paper_broker() -> None:
    """H1 F26: constructor fail-closed si broker no es PaperBroker."""
    md = _MdStub()
    book = PaperBook()
    risk = PaperRiskLimits()
    with pytest.raises(ValidationError, match="PaperBroker"):
        PaperSessionRunner(md, risk, book)  # type: ignore[arg-type]


def test_happy_path_dummy() -> None:
    runner, md, broker, book = _runner()
    status = runner.start(PaperSessionConfig(strategy_id="dummy", symbol="TEST", max_steps=5))
    assert status["running"] is True
    assert status["strategy_id"] == "dummy"
    assert status["live_blocked"] is True

    summary = runner.step()
    assert summary["ok"] is True
    assert summary["step"] == 1
    assert summary["live_routing"] is False
    actions = summary["actions"]
    assert len(actions) >= 1
    assert actions[0]["status"] == "FILLED"
    assert md.submit_calls == 0
    positions = broker.get_positions()
    assert len(positions) == 1
    assert positions[0].symbol == "TEST"


def test_happy_path_buy_once() -> None:
    runner, md, _broker, _book = _runner()
    runner.start(PaperSessionConfig(strategy_id="buy_once", symbol="TEST", max_steps=5))
    s1 = runner.step()
    assert any(a.get("status") == "FILLED" for a in s1["actions"])
    s2 = runner.step()
    assert any(a.get("status") == "NO_ACTION" for a in s2["actions"])
    assert md.submit_calls == 0


def test_risk_reject() -> None:
    risk = PaperRiskLimits(max_qty=Decimal("0.001"))
    runner, md, _broker, _book = _runner(risk=risk)
    runner.start(
        PaperSessionConfig(
            strategy_id="dummy",
            symbol="TEST",
            max_steps=3,
            params={"quantity": "1", "price": "100"},
        )
    )
    summary = runner.step()
    assert any(a.get("status") == "RISK_REJECTED" for a in summary["actions"])
    assert runner.status()["last_error"]
    assert md.submit_calls == 0
    assert _broker_positions_empty(runner)


def _broker_positions_empty(runner: PaperSessionRunner) -> bool:
    return len(runner._book.get_positions()) == 0  # noqa: SLF001


def test_stop_cancels_running() -> None:
    runner, _md, _broker, _book = _runner()
    runner.start(PaperSessionConfig(strategy_id="dummy", symbol="TEST", max_steps=10))
    assert runner.status()["running"] is True
    stopped = runner.stop()
    assert stopped["running"] is False
    with pytest.raises(ValidationError, match="detenida"):
        runner.step()


def test_stop_background_cancelable() -> None:
    runner, _md, _broker, _book = _runner()
    runner.start(
        PaperSessionConfig(
            strategy_id="buy_once",
            symbol="TEST",
            max_steps=50,
            interval_ms=200,
        )
    )
    assert runner.status()["background_alive"] is True or runner.status()["running"] is True
    runner.stop()
    st = runner.status()
    assert st["running"] is False
    assert st["background_alive"] is False


def test_build_strategy_unknown() -> None:
    with pytest.raises(ValidationError, match="desconocido"):
        build_session_strategy("nope")


def test_max_steps_stops() -> None:
    runner, _md, _broker, _book = _runner()
    runner.start(PaperSessionConfig(strategy_id="buy_once", symbol="TEST", max_steps=1))
    runner.step()
    assert runner.status()["running"] is False
    with pytest.raises(ValidationError, match="max_steps"):
        runner.step()


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


def test_api_paper_session_flow(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    conn = http.client.HTTPConnection(host, port, timeout=10)

    status, _ = _post_json(conn, "/api/broker/connect", {"venue": "binance", "mode": "tester"})
    assert status == 200

    conn.request("GET", "/api/broker/instruments")
    resp = conn.getresponse()
    instruments = json.loads(resp.read().decode("utf-8"))
    assert resp.status == 200
    symbol = str(instruments["instruments"][0]["symbol"])

    status, start_body = _post_json(
        conn,
        "/api/paper/session/start",
        {"strategy_id": "buy_once", "symbol": symbol, "max_steps": 5},
    )
    assert status == 200
    assert start_body["ok"] is True
    assert start_body["live_blocked"] is True
    assert start_body["status"]["running"] is True

    status, step_body = _post_json(conn, "/api/paper/session/step", {})
    assert status == 200
    assert step_body["step"] == 1
    assert step_body["live_routing"] is False

    conn.request("GET", "/api/paper/session/status")
    resp = conn.getresponse()
    st = json.loads(resp.read().decode("utf-8"))
    assert resp.status == 200
    assert st["steps"] == 1
    assert st["strategy_id"] == "buy_once"

    status, stop_body = _post_json(conn, "/api/paper/session/stop", {})
    assert status == 200
    assert stop_body["status"]["running"] is False
    conn.close()


def test_api_session_requires_broker(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    conn = http.client.HTTPConnection(host, port, timeout=5)
    status, body = _post_json(
        conn,
        "/api/paper/session/start",
        {"strategy_id": "dummy", "symbol": "X"},
    )
    conn.close()
    assert status == 400
    err = str(body.get("error", "")).lower()
    assert "conectado" in err or "connect" in err or "broker" in err
