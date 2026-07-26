"""F52 — Graceful shutdown + paper session safety.

SIGINT/SIGTERM / POST /api/shutdown (loopback) detienen paper runner,
flushean layout/settings y marcan shutdown_requested.
"""

from __future__ import annotations

import contextlib
import http.client
import json
import threading
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from quantlab import __version__
from quantlab.brokers.paper.book import PaperBook
from quantlab.brokers.paper.broker import PaperBroker
from quantlab.brokers.types import (
    BrokerAccount,
    BrokerAck,
    BrokerInstrument,
    BrokerPosition,
    BrokerSnapshot,
)
from quantlab.core.types.orders import OrderIntent
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import ApiError, WorkbenchState, handle_post_shutdown
from quantlab.workbench.layout import load_layout, save_layout
from quantlab.workbench.paper_session import PaperSessionConfig, PaperSessionRunner
from quantlab.workbench.risk import PaperRiskLimits
from quantlab.workbench.server import create_server
from quantlab.workbench.session import WorkbenchSession
from quantlab.workbench.settings import load_settings
from quantlab.workbench.shutdown import (
    flush_layout_settings,
    is_loopback_client,
    perform_graceful_shutdown,
    stop_paper_session_if_running,
)


class _MdStub:
    def __init__(self, symbol: str = "TEST", last: str = "100") -> None:
        self.symbol = symbol
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
        raise AssertionError("must never call md submit")

    def cancel(self, order_id: str) -> BrokerAck:
        raise AssertionError("must never call md cancel")


def _attach_running_paper(state: WorkbenchState) -> PaperSessionRunner:
    md = _MdStub()
    book = PaperBook(initial_cash=Decimal("10000"))
    broker = PaperBroker(md, book=book)  # type: ignore[arg-type]
    state.broker = broker
    state.book = book
    state.venue = "binance"
    runner = PaperSessionRunner(
        broker,
        PaperRiskLimits(),
        book,
        on_book_persist=state.persist_book,
    )
    runner.start(
        PaperSessionConfig(strategy_id="buy_once", symbol="TEST", max_steps=50)
    )
    assert runner.status()["running"] is True
    state.paper_session = runner
    return runner


def test_live_blocked_invariant_f52() -> None:
    assert LIVE_BLOCKED is True


def test_version_and_phases_f52() -> None:
    assert __version__ == "0.57.0"
    assert PHASES_SUMMARY == "F19–F65 INTERNAL"


def test_is_loopback_client() -> None:
    assert is_loopback_client("127.0.0.1") is True
    assert is_loopback_client("::1") is True
    assert is_loopback_client("localhost") is True
    assert is_loopback_client("::ffff:127.0.0.1") is True
    assert is_loopback_client("8.8.8.8") is False
    assert is_loopback_client("10.0.0.1") is False


def test_stop_session_on_shutdown_hook(tmp_path: Path) -> None:
    """DoD F52: shutdown hook detiene paper session si running."""
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "shut-hook")
    state = WorkbenchState(session=session, slippage_bps=Decimal("5"))
    state.ensure_session()
    runner = _attach_running_paper(state)
    assert state.paper_session is not None
    assert runner.status()["running"] is True

    result = perform_graceful_shutdown(state, reason="test-hook", stop_server=False)

    assert result["ok"] is True
    assert result["paper"]["stopped"] is True
    assert result["paper"]["was_running"] is True
    assert state.paper_session is None
    assert state.shutdown_requested is True
    assert state.shutdown_done is True
    assert result["flushed"]["layout"] is True
    assert result["flushed"]["settings"] is True
    assert session.layout_path.is_file()
    assert session.settings_path.is_file()
    settings = load_settings(session.settings_path)
    assert settings["slippage_bps"] == "5"


def test_shutdown_idempotent(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "shut-idem")
    state = WorkbenchState(session=session)
    state.ensure_session()
    first = perform_graceful_shutdown(state, reason="first", stop_server=False)
    second = perform_graceful_shutdown(state, reason="second", stop_server=False)
    assert first["already_done"] is False
    assert second["already_done"] is True
    assert state.shutdown_reason == "second"


def test_flush_layout_settings_rewrites(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "flush")
    state = WorkbenchState(session=session, slippage_bps=Decimal("12.5"))
    state.ensure_session()
    save_layout(
        session.layout_path,
        {
            "version": 1,
            "windows": {
                "paper_session": {"x": 10, "y": 20, "w": 400, "h": 300, "z": 1},
            },
        },
    )
    out = flush_layout_settings(state)
    assert out["layout"] is True
    assert out["settings"] is True
    layout = load_layout(session.layout_path)
    assert "paper_session" in layout["windows"]
    assert load_settings(session.settings_path)["slippage_bps"] == "12.5"


def test_handle_post_shutdown_rejects_non_loopback(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "nlb")
    state = WorkbenchState(session=session)
    state.ensure_session()
    with pytest.raises(ApiError) as exc:
        handle_post_shutdown(state, client_ip="8.8.8.8", stop_server=False)
    assert exc.value.status == 403
    assert state.shutdown_requested is False


def test_handle_post_shutdown_loopback_stops_paper(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "api-hook")
    state = WorkbenchState(session=session)
    state.ensure_session()
    _attach_running_paper(state)
    body = handle_post_shutdown(state, client_ip="127.0.0.1", stop_server=False)
    assert body["ok"] is True
    assert body["shutdown_requested"] is True
    assert body["paper"]["stopped"] is True
    assert state.paper_session is None


def test_http_api_shutdown_stops_server_and_paper(tmp_path: Path) -> None:
    """POST /api/shutdown loopback: detiene runner y sale serve_forever."""
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "http-shut")
    state = WorkbenchState(session=session)
    state.ensure_session()
    _attach_running_paper(state)
    server = create_server(host="127.0.0.1", port=0, state=state)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    try:
        conn = http.client.HTTPConnection(host, port, timeout=5.0)
        try:
            conn.request(
                "POST",
                "/api/shutdown",
                body=b"{}",
                headers={"Content-Type": "application/json"},
            )
            resp = conn.getresponse()
            raw = resp.read()
            assert resp.status == 200, raw
            payload = json.loads(raw.decode("utf-8"))
            assert payload["ok"] is True
            assert payload["kind"] == "shutdown"
            assert payload["paper"]["stopped"] is True
        finally:
            conn.close()
        thread.join(timeout=3.0)
        assert state.shutdown_requested is True
        assert state.paper_session is None
        assert not thread.is_alive()
    finally:
        with contextlib.suppress(Exception):
            server.shutdown()
        server.server_close()


def test_stop_paper_helper_noop_when_absent(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "noop")
    state = WorkbenchState(session=session)
    state.ensure_session()
    out = stop_paper_session_if_running(state)
    assert out["stopped"] is False
    assert out["was_running"] is False
