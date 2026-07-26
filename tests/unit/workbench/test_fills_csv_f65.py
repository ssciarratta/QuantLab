"""Tests GET /api/paper/fills.csv — header + rows (F65)."""

from __future__ import annotations

import http.client
from datetime import UTC, datetime
from decimal import Decimal
from http.server import ThreadingHTTPServer
from pathlib import Path

from quantlab import __version__
from quantlab.brokers.paper.journal import FILLS_CSV_COLUMNS, PaperFillJournal, fills_to_csv
from quantlab.brokers.types import PaperFill
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import WorkbenchState, handle_get_paper_fills_csv
from quantlab.workbench.server import make_handler
from quantlab.workbench.session import WorkbenchSession


def _static_root() -> Path:
    return Path(__file__).resolve().parents[3] / "src" / "quantlab" / "workbench" / "static"


def _sample_fill(*, fill_id: str = "f1", symbol: str = "BTC-USD") -> PaperFill:
    return PaperFill(
        fill_id=fill_id,
        order_id="o1",
        symbol=symbol,
        side="buy",
        quantity=Decimal("1.5"),
        price=Decimal("100.25"),
        ts=datetime(2026, 7, 26, 12, 0, 0, tzinfo=UTC),
        source="paper_broker",
    )


def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.68.0"
    assert PHASES_SUMMARY == "F19–F76 INTERNAL"
    assert not Path("docs/audit/FASE_65_APPROVED.md").exists()


def test_fills_to_csv_header_and_rows() -> None:
    csv = fills_to_csv([_sample_fill(), _sample_fill(fill_id="f2", symbol="ETH,USD")])
    lines = csv.strip("\n").split("\n")
    assert lines[0] == ",".join(FILLS_CSV_COLUMNS)
    assert lines[0].startswith("ts,fill_id,order_id,symbol,side,quantity,price,source")
    assert len(lines) == 3
    assert "f1" in lines[1]
    assert "BTC-USD" in lines[1]
    assert "1.5" in lines[1]
    assert "100.25" in lines[1]
    assert "paper_broker" in lines[1]
    # comma in symbol → quoted
    assert '"ETH,USD"' in lines[2]
    assert csv.endswith("\n")


def test_journal_export_csv(tmp_path: Path) -> None:
    journal = PaperFillJournal(tmp_path / "journal.jsonl")
    journal.append(_sample_fill())
    text = journal.export_csv()
    header, row = text.strip("\n").split("\n", 1)
    assert header == ",".join(FILLS_CSV_COLUMNS)
    assert "f1" in row
    assert "BTC-USD" in row


def test_handle_get_paper_fills_csv(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "csv65")
    session.save_meta({"session_id": session.session_id})
    state = WorkbenchState(session=session, session_parent=tmp_path)
    state.ensure_session()
    assert state.journal is not None
    state.journal.append(_sample_fill(fill_id="fx"))

    body, filename = handle_get_paper_fills_csv(state)
    text = body.decode("utf-8")
    assert filename.endswith(".csv")
    assert "csv65" in filename
    lines = text.strip("\n").split("\n")
    assert lines[0] == ",".join(FILLS_CSV_COLUMNS)
    assert "fx" in lines[1]
    assert len(lines) == 2


def test_http_get_fills_csv(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "http65")
    session.save_meta({"session_id": session.session_id})
    state = WorkbenchState(session=session, session_parent=tmp_path)
    state.ensure_session()
    assert state.journal is not None
    state.journal.append(_sample_fill(fill_id="http-f1"))

    handler = make_handler(state)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = __import__("threading").Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        conn = http.client.HTTPConnection(str(host), int(port), timeout=30)
        conn.request("GET", "/api/paper/fills.csv")
        resp = conn.getresponse()
        raw = resp.read()
        headers = {k.lower(): v for k, v in resp.getheaders()}
        conn.close()
        assert resp.status == 200
        assert "text/csv" in headers.get("content-type", "")
        assert "attachment" in headers.get("content-disposition", "")
        assert ".csv" in headers.get("content-disposition", "")
        text = raw.decode("utf-8")
        lines = text.strip("\n").split("\n")
        assert lines[0] == ",".join(FILLS_CSV_COLUMNS)
        assert "http-f1" in lines[1]
    finally:
        server.shutdown()


def test_static_blotter_journal_download() -> None:
    root = _static_root()
    blotter = (root / "js" / "panes" / "blotter.js").read_text(encoding="utf-8")
    journal = (root / "js" / "panes" / "journal.js").read_text(encoding="utf-8")
    api = (root / "js" / "api.js").read_text(encoding="utf-8")

    assert "paperFillsCsvUrl" in api
    assert "/api/paper/fills.csv" in api
    assert "Descargar CSV" in blotter
    assert "bl-download" in blotter
    assert "QLApi.paperFillsCsvUrl" in blotter
    assert "Descargar CSV" in journal
    assert "jn-download" in journal
    assert "QLApi.paperFillsCsvUrl" in journal
    assert "/api/paper/fills.csv" in journal
