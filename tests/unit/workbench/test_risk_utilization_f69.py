"""Tests risk utilization — GET /api/risk/utilization (F69)."""

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
from quantlab.brokers.types import BrokerInstrument, BrokerSnapshot, PaperFill
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import (
    WorkbenchState,
    handle_get_risk_utilization,
    handle_post_broker_connect,
    handle_post_paper_submit,
)
from quantlab.workbench.risk import PaperRiskLimits
from quantlab.workbench.risk_utilization import (
    compute_risk_utilization,
    utilization_from_book,
)
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
    assert __version__ == "0.99.0"
    assert PHASES_SUMMARY == "F19–F107 INTERNAL"
    assert not Path("docs/audit/FASE_69_APPROVED.md").exists()


def test_compute_utilization_empty_book() -> None:
    book = PaperBook(initial_cash=Decimal("1000"))
    limits = PaperRiskLimits(max_qty=Decimal("10"), max_notional=Decimal("1000"))
    out = compute_risk_utilization(book, limits)
    assert out["ok"] is True
    assert out["kind"] == "risk_utilization"
    assert out["used"]["qty"] == "0"
    assert out["used"]["notional"] == "0"
    assert out["used"]["symbols"] == 0
    assert out["pct"]["qty"] == "0"
    assert out["pct"]["notional"] == "0"
    assert out["positions"] == []
    assert out["live_blocked"] is True


def test_compute_utilization_peak_qty_and_gross_notional() -> None:
    book = PaperBook(initial_cash=Decimal("100000"))
    book.apply_fill(_fill(side="buy", qty="5", price="100", symbol="AAA"))
    book.apply_fill(_fill(side="buy", qty="2", price="50", symbol="BBB"))
    limits = PaperRiskLimits(max_qty=Decimal("10"), max_notional=Decimal("1000"))
    out = compute_risk_utilization(
        book, limits, mark_prices={"AAA": Decimal("110"), "BBB": Decimal("40")}
    )
    # peak |qty| = 5; gross notional = 5*110 + 2*40 = 630
    assert out["used"]["qty"] == "5"
    assert out["used"]["notional"] == "630"
    assert out["used"]["symbols"] == 2
    assert Decimal(out["pct"]["qty"]) == Decimal("50")
    assert Decimal(out["pct"]["notional"]) == Decimal("63")
    assert out["marks"]["AAA"] == "110"
    by_sym = {p["symbol"]: p for p in out["positions"]}
    assert Decimal(by_sym["AAA"]["pct_qty"]) == Decimal("50")
    assert by_sym["AAA"]["notional"] == "550"
    assert Decimal(by_sym["BBB"]["pct_qty"]) == Decimal("20")
    assert by_sym["BBB"]["notional"] == "80"


def test_utilization_from_book_avg_marks() -> None:
    book = PaperBook(initial_cash=Decimal("1000"))
    book.apply_fill(_fill(side="buy", qty="1", price="200"))
    limits = PaperRiskLimits(max_qty=Decimal("4"), max_notional=Decimal("1000"))
    out = utilization_from_book(book, limits)
    assert out["marks_source"] == "avg"
    assert out["used"]["qty"] == "1"
    assert out["used"]["notional"] == "200"
    assert Decimal(out["pct"]["qty"]) == Decimal("25")
    assert Decimal(out["pct"]["notional"]) == Decimal("20")


def test_handle_get_risk_utilization_no_broker(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "util69")
    state = WorkbenchState(
        session=session,
        session_parent=tmp_path,
        risk=PaperRiskLimits(max_qty=Decimal("10"), max_notional=Decimal("5000")),
    )
    state.ensure_session()
    book = PaperBook(initial_cash=Decimal("5000"))
    fill = _fill(side="buy", qty="2", price="100", symbol="AAA")
    state.ensure_journal().append(fill)
    book.apply_fill(fill)
    state.book = book
    state.persist_book()
    out = handle_get_risk_utilization(state)
    assert out["ok"] is True
    assert out["session_id"] == "util69"
    assert out["used"]["qty"] == "2"
    assert out["used"]["notional"] == "200"
    assert Decimal(out["pct"]["qty"]) == Decimal("20")
    assert Decimal(out["pct"]["notional"]) == Decimal("4")
    assert out["live_blocked"] is True


def test_handle_get_risk_utilization_with_broker(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "util69b")
    state = WorkbenchState(
        session=session,
        session_parent=tmp_path,
        mode=OperatingMode.TESTER,
        risk=PaperRiskLimits(max_qty=Decimal("100"), max_notional=Decimal("100000")),
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
    out = handle_get_risk_utilization(state)
    assert out["ok"] is True
    assert out["marks_source"] == "broker"
    assert out["used"]["symbols"] == 1
    assert Decimal(out["used"]["qty"]) == Decimal("0.01")
    assert Decimal(out["used"]["notional"]) > 0


def test_http_get_risk_utilization(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "http69")
    state = WorkbenchState(
        session=session,
        session_parent=tmp_path,
        risk=PaperRiskLimits(max_qty=Decimal("8"), max_notional=Decimal("800")),
    )
    state.ensure_session()
    book = PaperBook(initial_cash=Decimal("10000"))
    fill = _fill(side="buy", qty="4", price="50")
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
        conn.request("GET", "/api/risk/utilization")
        resp = conn.getresponse()
        body = json.loads(resp.read().decode("utf-8"))
        conn.close()
        assert resp.status == 200
        assert body["ok"] is True
        assert body["kind"] == "risk_utilization"
        assert body["used"]["qty"] == "4"
        assert Decimal(body["pct"]["qty"]) == Decimal("50")
        assert body["used"]["notional"] == "200"
        assert Decimal(body["pct"]["notional"]) == Decimal("25")
    finally:
        server.shutdown()


def test_ui_risk_pane_has_utilization() -> None:
    static = _static_root()
    risk_js = (static / "js" / "panes" / "risk.js").read_text(encoding="utf-8")
    api_js = (static / "js" / "api.js").read_text(encoding="utf-8")
    assert "riskUtilization" in api_js
    assert "/api/risk/utilization" in api_js
    assert "risk-utilization" in risk_js
    assert "QLApi.riskUtilization" in risk_js
    assert "pct_qty" in risk_js
    assert "Utilización" in risk_js


def test_openapi_includes_risk_utilization() -> None:
    from quantlab.workbench.api_catalog import openapi_payload

    schema = openapi_payload()
    paths = schema["paths"]
    assert "/api/risk/utilization" in paths
    assert "get" in paths["/api/risk/utilization"]
