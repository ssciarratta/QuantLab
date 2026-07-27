"""Tests equity curve snapshot — equity.jsonl + GET /api/paper/equity (F66)."""

from __future__ import annotations

import http.client
import json
import threading
from datetime import UTC, datetime
from decimal import Decimal
from http.server import ThreadingHTTPServer
from pathlib import Path

from quantlab import __version__
from quantlab.brokers.mode import OperatingMode
from quantlab.brokers.paper.book import PaperBook
from quantlab.brokers.paper.broker import PaperBroker
from quantlab.brokers.types import BrokerInstrument, BrokerSnapshot
from quantlab.core.types.enums import IntentType, OrderSide, OrderType
from quantlab.core.types.orders import OrderIntent
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import (
    WorkbenchState,
    handle_get_paper_equity,
    handle_post_broker_connect,
    handle_post_paper_session_start,
    handle_post_paper_session_step,
    handle_post_paper_submit,
)
from quantlab.workbench.equity_curve import EquityCurveLog, clamp_equity_limit, list_equity
from quantlab.workbench.server import make_handler
from quantlab.workbench.session import WorkbenchSession


def _static_root() -> Path:
    return Path(__file__).resolve().parents[3] / "src" / "quantlab" / "workbench" / "static"


class _FakeMd:
    venue_id = "fake-md"

    def connect(self) -> dict[str, object]:
        return {"ok": True}

    def close(self) -> dict[str, object]:
        return {"ok": True}

    def health(self) -> dict[str, object]:
        return {"ok": True, "md_provider": "fake", "md_source": "unit"}

    def list_instruments(self) -> list[BrokerInstrument]:
        return [
            BrokerInstrument(
                symbol="BTC-USD",
                description="t",
                currency="USD",
                status="ACTIVE",
            )
        ]

    def get_snapshot(self, symbol: str) -> BrokerSnapshot:
        return BrokerSnapshot(
            symbol=symbol,
            bid=Decimal("100"),
            ask=Decimal("102"),
            last=Decimal("101"),
            ts=datetime(2026, 7, 26, 12, 0, 0, tzinfo=UTC),
        )

    def get_account(self):  # noqa: ANN201
        raise NotImplementedError

    def get_positions(self):  # noqa: ANN201
        raise NotImplementedError

    def submit(self, intent: OrderIntent):  # noqa: ANN201
        raise AssertionError("venue submit must not be called")

    def cancel(self, order_id: str):  # noqa: ANN201
        raise AssertionError("venue cancel must not be called")


def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.99.0"
    assert PHASES_SUMMARY == "F19–F107 INTERNAL"
    assert not Path("docs/audit/FASE_66_APPROVED.md").exists()


def test_clamp_equity_limit() -> None:
    assert clamp_equity_limit(None) == 200
    assert clamp_equity_limit(50) == 50
    assert clamp_equity_limit(9999) == 2000


def test_equity_curve_append_and_tail(tmp_path: Path) -> None:
    log = EquityCurveLog(tmp_path / "equity.jsonl")
    log.append(
        equity=Decimal("1000"),
        cash=Decimal("1000"),
        ts=datetime(2026, 7, 26, 1, 0, tzinfo=UTC),
    )
    log.append(
        equity=Decimal("990"),
        cash=Decimal("900"),
        ts=datetime(2026, 7, 26, 2, 0, tzinfo=UTC),
    )
    log.append(
        equity=Decimal("1010"),
        cash=Decimal("910"),
        ts=datetime(2026, 7, 26, 3, 0, tzinfo=UTC),
    )
    points = log.read_tail(2)
    assert len(points) == 2
    assert points[0]["equity"] == "990"
    assert points[1]["cash"] == "910"
    payload = list_equity(tmp_path / "equity.jsonl", limit=10)
    assert payload["ok"] is True
    assert payload["kind"] == "equity"
    assert payload["count"] == 3
    assert payload["live_blocked"] is True


def test_handle_get_paper_equity(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "eq66")
    session.save_meta({"session_id": session.session_id})
    state = WorkbenchState(session=session, session_parent=tmp_path)
    state.ensure_session()
    EquityCurveLog(session.equity_path).append(equity="100", cash="100")
    EquityCurveLog(session.equity_path).append(equity="105", cash="95")
    out = handle_get_paper_equity(state, "limit=1")
    assert out["ok"] is True
    assert out["count"] == 1
    assert out["points"][0]["equity"] == "105"
    assert out["session_id"] == "eq66"


def test_fill_appends_equity_point(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "fill66")
    state = WorkbenchState(
        session=session,
        session_parent=tmp_path,
        mode=OperatingMode.PAPER,
        initial_cash=Decimal("10000"),
    )
    state.ensure_session()
    book = PaperBook(initial_cash=Decimal("10000"))
    state.book = book

    def _on_book_change(updated: PaperBook) -> None:
        state.book = updated
        state.persist_book()
        EquityCurveLog(session.equity_path).append(
            equity=updated.get_account().equity or updated.cash,
            cash=updated.cash,
        )

    broker = PaperBroker(
        _FakeMd(), journal=state.journal, book=book, on_book_change=_on_book_change
    )
    state.broker = broker
    intent = OrderIntent(
        intent_id="i1",
        intent_type=IntentType.PLACE_ORDER,
        instrument_id="BTC-USD",
        side=OrderSide.BUY,
        quantity=Decimal("1"),
        order_type=OrderType.MARKET,
    )
    ack = broker.submit(intent)
    assert ack.status == "FILLED"
    points = EquityCurveLog(session.equity_path).read_tail(10)
    assert len(points) >= 1
    assert "equity" in points[-1]
    assert "cash" in points[-1]


def test_connect_submit_records_equity(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "api66")
    state = WorkbenchState(session=session, session_parent=tmp_path, mode=OperatingMode.TESTER)
    handle_post_broker_connect(
        state,
        {"venue": "binance", "mode": "tester", "md_source": "fake"},
    )
    handle_post_paper_submit(
        state,
        {
            "intent_type": "place_order",
            "instrument_id": "BTCUSDT",
            "side": "buy",
            "quantity": "0.01",
            "order_type": "market",
        },
    )
    out = handle_get_paper_equity(state, "limit=50")
    assert out["count"] >= 1
    assert out["points"][-1]["equity"]
    assert out["points"][-1]["cash"]
    lines = session.equity_path.read_text(encoding="utf-8").strip().splitlines()
    last = json.loads(lines[-1])
    assert set(last.keys()) == {"ts", "equity", "cash"}


def test_paper_session_step_appends_equity(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "step66")
    state = WorkbenchState(session=session, session_parent=tmp_path, mode=OperatingMode.TESTER)
    handle_post_broker_connect(
        state, {"venue": "binance", "mode": "tester", "md_source": "fake"}
    )
    handle_post_paper_session_start(
        state,
        {"strategy_id": "dummy", "symbol": "BTCUSDT", "max_steps": 3},
    )
    before = handle_get_paper_equity(state, "limit=500")["count"]
    handle_post_paper_session_step(state)
    after = handle_get_paper_equity(state, "limit=500")["count"]
    assert after > before


def test_http_get_paper_equity(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "http66")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    state.ensure_session()
    EquityCurveLog(session.equity_path).append(equity="42", cash="40")

    handler = make_handler(state)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        conn = http.client.HTTPConnection(str(host), int(port), timeout=30)
        conn.request("GET", "/api/paper/equity?limit=10")
        resp = conn.getresponse()
        raw = resp.read()
        conn.close()
        assert resp.status == 200
        payload = json.loads(raw.decode("utf-8"))
        assert payload["ok"] is True
        assert payload["kind"] == "equity"
        assert payload["count"] == 1
        assert payload["points"][0]["equity"] == "42"
    finally:
        server.shutdown()


def test_static_positions_equity_ui() -> None:
    root = _static_root()
    positions = (root / "js" / "panes" / "positions.js").read_text(encoding="utf-8")
    api = (root / "js" / "api.js").read_text(encoding="utf-8")
    assert "paperEquity" in api
    assert "/api/paper/equity" in api
    assert "Equity curve" in positions
    assert "pos-equity-spark" in positions
    assert "sparklineSvg" in positions
    assert "QLApi.paperEquity" in positions
    assert "polyline" in positions
