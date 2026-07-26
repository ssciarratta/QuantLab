"""Tests Health Extended flags + edge cases milestone 1000 (F71)."""

from __future__ import annotations

import http.client
import json
import threading
from decimal import Decimal
from http.server import ThreadingHTTPServer
from pathlib import Path

from quantlab import __version__
from quantlab.brokers.paper.book import PaperBook
from quantlab.brokers.paper.journal import FILLS_CSV_COLUMNS, fills_to_csv
from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY, build_about_payload
from quantlab.workbench.api import (
    WorkbenchState,
    handle_get_about,
    handle_get_backups,
    handle_get_health,
    handle_get_paper_equity,
    handle_get_paper_fills_csv,
    handle_get_paper_pnl,
    handle_get_risk_utilization,
    handle_post_paper_kill,
    handle_put_settings,
)
from quantlab.workbench.equity_curve import list_equity
from quantlab.workbench.paper_kill import KILL_ENGAGED_MSG, raise_if_paper_kill_engaged
from quantlab.workbench.paper_pnl import summarize_paper_pnl
from quantlab.workbench.risk import PaperRiskLimits
from quantlab.workbench.risk_utilization import compute_risk_utilization
from quantlab.workbench.server import make_handler
from quantlab.workbench.session import WorkbenchSession


def _static_root() -> Path:
    return Path(__file__).resolve().parents[3] / "src" / "quantlab" / "workbench" / "static"


def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.63.0"
    assert PHASES_SUMMARY == "F19–F71 INTERNAL"
    assert not Path("docs/audit/FASE_71_APPROVED.md").exists()


def test_build_about_payload_includes_ops_flags_defaults() -> None:
    payload = build_about_payload()
    assert payload["paper_kill_engaged"] is False
    assert payload["auto_backup_minutes"] == 0
    assert payload["access_log"] is True
    assert payload["version"] == "0.63.0"
    assert payload["phases_summary"] == "F19–F71 INTERNAL"


def test_health_ops_flags_defaults(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "hlth71")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    health = handle_get_health(state)
    assert health["ok"] is True
    assert health["live_blocked"] is True
    assert health["version"] == "0.63.0"
    assert health["paper_kill_engaged"] is False
    assert health["auto_backup_minutes"] == 0
    assert health["access_log"] is True


def test_about_ops_flags_defaults(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "about71")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    about = handle_get_about(state)
    assert about["paper_kill_engaged"] is False
    assert about["auto_backup_minutes"] == 0
    assert about["access_log"] is True
    assert about["phases_summary"] == "F19–F71 INTERNAL"


def test_health_reflects_paper_kill_engaged(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "kill71")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    handle_post_paper_kill(state, {"engaged": True})
    health = handle_get_health(state)
    about = handle_get_about(state)
    assert health["paper_kill_engaged"] is True
    assert about["paper_kill_engaged"] is True
    handle_post_paper_kill(state, {"engaged": False})
    assert handle_get_health(state)["paper_kill_engaged"] is False


def test_health_reflects_access_log_and_backup_minutes(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "set71")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    handle_put_settings(state, {"access_log": False, "auto_backup_minutes": 30})
    health = handle_get_health(state)
    about = handle_get_about(state)
    assert health["access_log"] is False
    assert health["auto_backup_minutes"] == 30
    assert about["access_log"] is False
    assert about["auto_backup_minutes"] == 30


def test_kill_switch_edge_clear_then_engaged() -> None:
    raise_if_paper_kill_engaged(engaged=False)
    try:
        raise_if_paper_kill_engaged(engaged=True)
        raise AssertionError("expected ValidationError")
    except ValidationError as exc:
        assert KILL_ENGAGED_MSG in str(exc)


def test_pnl_empty_book() -> None:
    book = PaperBook(initial_cash=Decimal("2500"))
    pnl = book.get_pnl()
    assert pnl["cash"] == Decimal("2500")
    assert pnl["equity"] == Decimal("2500")
    assert pnl["realized"] == Decimal("0")
    assert pnl["unrealized"] == Decimal("0")
    payload = summarize_paper_pnl(book)
    assert payload["kind"] == "pnl"
    assert payload["equity"] == "2500"
    assert payload["marks"] == {}


def test_handle_pnl_empty_book(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "pnl71")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    state.ensure_session()
    state.book = PaperBook(initial_cash=Decimal("1000"))
    out = handle_get_paper_pnl(state)
    assert out["ok"] is True
    assert out["equity"] == "1000"
    assert out["realized"] == "0"
    assert out["unrealized"] == "0"


def test_equity_empty_list(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "eq71")
    session.ensure_layout()
    payload = list_equity(session.equity_path, limit=50)
    assert payload["ok"] is True
    assert payload["kind"] == "equity"
    assert payload["count"] == 0
    assert payload["points"] == []
    state = WorkbenchState(session=session, session_parent=tmp_path)
    out = handle_get_paper_equity(state, "limit=10")
    assert out["count"] == 0
    assert out["points"] == []


def test_risk_util_zero_positions() -> None:
    book = PaperBook(initial_cash=Decimal("5000"))
    limits = PaperRiskLimits(max_qty=Decimal("10"), max_notional=Decimal("10000"))
    out = compute_risk_utilization(book, limits)
    assert out["used"]["qty"] == "0"
    assert out["used"]["notional"] == "0"
    assert out["used"]["symbols"] == 0
    assert out["pct"]["qty"] == "0"
    assert out["pct"]["notional"] == "0"
    assert out["positions"] == []


def test_handle_risk_util_zero_positions(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "risk71")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    state.ensure_session()
    state.book = PaperBook(initial_cash=Decimal("1000"))
    out = handle_get_risk_utilization(state)
    assert out["used"]["qty"] == "0"
    assert out["positions"] == []


def test_backups_empty_list(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "bk71")
    session.save_meta({"session_id": session.session_id})
    state = WorkbenchState(session=session, session_parent=tmp_path)
    payload = handle_get_backups(state)
    assert payload["ok"] is True
    assert payload["kind"] == "backups"
    assert payload["count"] == 0
    assert payload["backups"] == []
    assert payload["auto_backup_enabled"] is False


def test_fills_csv_empty() -> None:
    csv = fills_to_csv([])
    assert csv == ",".join(FILLS_CSV_COLUMNS) + "\n"
    lines = csv.strip("\n").split("\n")
    assert len(lines) == 1
    assert lines[0].startswith("ts,fill_id")


def test_handle_fills_csv_empty_journal(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "csv71")
    session.save_meta({"session_id": session.session_id})
    state = WorkbenchState(session=session, session_parent=tmp_path)
    state.ensure_session()
    body, filename = handle_get_paper_fills_csv(state)
    text = body.decode("utf-8")
    assert filename.endswith(".csv")
    assert text.strip("\n") == ",".join(FILLS_CSV_COLUMNS)


def test_http_health_includes_ops_flags(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "http71")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    handle_put_settings(state, {"access_log": True, "auto_backup_minutes": 15})
    handle_post_paper_kill(state, {"engaged": True})

    handler = make_handler(state)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        conn = http.client.HTTPConnection(str(host), int(port), timeout=30)
        conn.request("GET", "/api/health")
        resp = conn.getresponse()
        health = json.loads(resp.read().decode("utf-8"))
        conn.close()
        assert resp.status == 200
        assert health["paper_kill_engaged"] is True
        assert health["auto_backup_minutes"] == 15
        assert health["access_log"] is True
        assert health["live_blocked"] is True

        conn2 = http.client.HTTPConnection(str(host), int(port), timeout=30)
        conn2.request("GET", "/api/about")
        resp2 = conn2.getresponse()
        about = json.loads(resp2.read().decode("utf-8"))
        conn2.close()
        assert resp2.status == 200
        assert about["paper_kill_engaged"] is True
        assert about["auto_backup_minutes"] == 15
        assert about["version"] == "0.63.0"
    finally:
        server.shutdown()


def test_static_health_and_about_surface_flags() -> None:
    root = _static_root()
    health_js = (root / "js" / "panes" / "health.js").read_text(encoding="utf-8")
    about_js = (root / "js" / "about.js").read_text(encoding="utf-8")
    assert "paper_kill_engaged" in health_js
    assert "auto_backup_minutes" in health_js
    assert "access_log" in health_js
    assert "hp-ops-flags" in health_js
    assert "paper_kill_engaged" in about_js
    assert "Auto-backup" in about_js
