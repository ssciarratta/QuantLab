"""Tests paper PnL summary — GET /api/paper/pnl (F67)."""

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
from quantlab.brokers.types import BrokerInstrument, BrokerSnapshot, PaperFill
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import (
    WorkbenchState,
    handle_get_paper_pnl,
    handle_post_broker_connect,
    handle_post_paper_submit,
)
from quantlab.workbench.paper_pnl import pnl_from_book, summarize_paper_pnl
from quantlab.workbench.server import make_handler
from quantlab.workbench.session import WorkbenchSession


def _static_root() -> Path:
    return Path(__file__).resolve().parents[3] / "src" / "quantlab" / "workbench" / "static"


def _fill(
    *,
    side: str,
    qty: str,
    price: str,
    symbol: str = "TEST",
) -> PaperFill:
    return PaperFill(
        fill_id="f1",
        order_id="o1",
        symbol=symbol,
        side=side,
        quantity=Decimal(qty),
        price=Decimal(price),
        ts=datetime(2026, 7, 26, tzinfo=UTC),
    )


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
                symbol="BTCUSDT",
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

    def submit(self, intent):  # noqa: ANN201
        raise AssertionError("venue submit must not be called")

    def cancel(self, order_id: str):  # noqa: ANN201
        raise AssertionError("venue cancel must not be called")


def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.88.0"
    assert PHASES_SUMMARY == "F19–F96 INTERNAL"
    assert not Path("docs/audit/FASE_67_APPROVED.md").exists()


def test_book_pnl_open_position_unrealized() -> None:
    book = PaperBook(initial_cash=Decimal("1000"))
    book.apply_fill(_fill(side="buy", qty="2", price="100"))
    pnl = book.get_pnl(mark_prices={"TEST": Decimal("110")})
    assert pnl["cash"] == Decimal("800")
    assert pnl["realized"] == Decimal("0")
    assert pnl["unrealized"] == Decimal("20")
    assert pnl["equity"] == Decimal("1020")
    assert pnl["equity"] == book.initial_cash + pnl["realized"] + pnl["unrealized"]


def test_book_pnl_realized_after_close() -> None:
    book = PaperBook(initial_cash=Decimal("1000"))
    book.apply_fill(_fill(side="buy", qty="5", price="10"))
    book.apply_fill(_fill(side="sell", qty="5", price="12"))
    pnl = book.get_pnl()
    assert pnl["cash"] == Decimal("1010")
    assert pnl["realized"] == Decimal("10")
    assert pnl["unrealized"] == Decimal("0")
    assert pnl["equity"] == Decimal("1010")


def test_summarize_paper_pnl_strings() -> None:
    book = PaperBook(initial_cash=Decimal("1000"))
    book.apply_fill(_fill(side="buy", qty="1", price="100"))
    payload = summarize_paper_pnl(
        book, mark_prices={"TEST": Decimal("105")}, marks_source="test"
    )
    assert payload["ok"] is True
    assert payload["kind"] == "pnl"
    assert payload["realized"] == "0"
    assert payload["unrealized"] == "5"
    assert payload["equity"] == "1005"
    assert payload["cash"] == "900"
    assert payload["marks"]["TEST"] == "105"
    assert payload["live_blocked"] is True
    flat = pnl_from_book(book)
    assert flat["unrealized"] == "0"
    assert flat["marks_source"] == "avg"


def test_handle_get_paper_pnl_no_broker(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "pnl67")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    state.ensure_session()
    book = PaperBook(initial_cash=Decimal("5000"))
    fill = _fill(side="buy", qty="1", price="100", symbol="AAA")
    state.ensure_journal().append(fill)
    book.apply_fill(fill)
    state.book = book
    state.persist_book()
    out = handle_get_paper_pnl(state)
    assert out["ok"] is True
    assert out["kind"] == "pnl"
    assert out["session_id"] == "pnl67"
    assert out["cash"] == "4900"
    assert out["realized"] == "0"
    assert out["unrealized"] == "0"
    assert out["equity"] == "5000"
    assert out["marks_source"] == "avg"


def test_handle_get_paper_pnl_with_broker_marks(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "pnl67b")
    state = WorkbenchState(
        session=session,
        session_parent=tmp_path,
        mode=OperatingMode.TESTER,
        initial_cash=Decimal("100000"),
    )
    handle_post_broker_connect(
        state, {"venue": "binance", "mode": "tester", "md_source": "fake"}
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
    out = handle_get_paper_pnl(state)
    assert out["ok"] is True
    assert out["marks_source"] == "broker"
    assert "BTCUSDT" in out["marks"] or out["unrealized"] is not None
    assert Decimal(out["equity"]) == Decimal(out["initial_cash"]) + Decimal(
        out["realized"]
    ) + Decimal(out["unrealized"])
    assert isinstance(state.broker, PaperBroker)
    broker_pnl = state.broker.get_pnl()
    assert str(broker_pnl["cash"]) == out["cash"]


def test_http_get_paper_pnl(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "http67")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    state.ensure_session()
    book = PaperBook(initial_cash=Decimal("1000"))
    fill = _fill(side="buy", qty="1", price="100")
    state.ensure_journal().append(fill)
    book.apply_fill(fill)
    state.book = book
    state.persist_book()

    handler = make_handler(state)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        conn = http.client.HTTPConnection(str(host), int(port), timeout=30)
        conn.request("GET", "/api/paper/pnl")
        resp = conn.getresponse()
        raw = resp.read()
        conn.close()
        assert resp.status == 200
        payload = json.loads(raw.decode("utf-8"))
        assert payload["ok"] is True
        assert payload["kind"] == "pnl"
        assert payload["cash"] == "900"
        assert set(payload.keys()) >= {
            "realized",
            "unrealized",
            "equity",
            "cash",
            "live_blocked",
        }
    finally:
        server.shutdown()


def test_static_pnl_ui() -> None:
    root = _static_root()
    positions = (root / "js" / "panes" / "positions.js").read_text(encoding="utf-8")
    blotter = (root / "js" / "panes" / "blotter.js").read_text(encoding="utf-8")
    api = (root / "js" / "api.js").read_text(encoding="utf-8")
    assert "paperPnl" in api
    assert "/api/paper/pnl" in api
    assert "pos-pnl-header" in positions
    assert "QLApi.paperPnl" in positions
    assert "realized" in positions
    assert "unrealized" in positions
    assert "formatPnlHeader" in blotter
    assert "QLApi.paperPnl" in blotter
    assert "Cuenta / PnL" in blotter


def test_openapi_includes_paper_pnl() -> None:
    from quantlab.workbench.api_catalog import openapi_payload

    schema = openapi_payload()
    paths = schema["paths"]
    assert "/api/paper/pnl" in paths
    assert "get" in paths["/api/paper/pnl"]
