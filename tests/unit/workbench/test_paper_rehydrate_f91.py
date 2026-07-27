"""F91: rehydrate de sesión post-rebuild CLI (POST /api/paper/reconciliation/rehydrate)."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from quantlab import __version__
from quantlab.brokers.paper.journal import PaperFillJournal
from quantlab.brokers.types import PaperFill
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import WorkbenchState, handle_post_paper_rehydrate
from quantlab.workbench.api_catalog import build_openapi_schema
from quantlab.workbench.session import WorkbenchSession

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from reconcile_paper_session import rebuild_session  # noqa: E402


def _fill(fill_id: str = "fill-1", order_id: str = "order-1") -> PaperFill:
    return PaperFill(
        fill_id=fill_id,
        order_id=order_id,
        symbol="TEST",
        side="buy",
        quantity=Decimal("2"),
        price=Decimal("11.25"),
        ts=datetime(2026, 7, 26, 12, tzinfo=UTC),
        source="paper_broker",
    )


def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.96.0"
    assert PHASES_SUMMARY == "F19–F104 INTERNAL"
    assert not Path("docs/audit/FASE_91_APPROVED.md").exists()


def test_rehydrate_without_rebuild_stays_blocked(tmp_path: Path) -> None:
    """Journal ahead sin rebuild: rehydrate NO auto-recupera ni muta archivos."""
    session = WorkbenchSession.create_or_load(tmp_path, "blocked")
    PaperFillJournal(session.journal_path).append(_fill())
    journal_before = session.journal_path.read_bytes()
    book_before = session.book_path.read_bytes()

    state = WorkbenchState(session=session, session_parent=tmp_path)
    state.ensure_session()
    assert state.paper_reconciliation is not None
    assert state.paper_reconciliation.status == "rebuild_required"

    payload = handle_post_paper_rehydrate(state)

    assert payload["ok"] is False
    assert payload["status"] == "rebuild_required"
    assert payload["rehydrated"] is True
    assert session.journal_path.read_bytes() == journal_before
    assert session.book_path.read_bytes() == book_before


def test_rehydrate_after_cli_rebuild_unblocks_without_restart(tmp_path: Path) -> None:
    """Loop ops completo: drift → rebuild CLI offline → rehydrate → ok."""
    session = WorkbenchSession.create_or_load(tmp_path, "loop")
    PaperFillJournal(session.journal_path).append(_fill())

    state = WorkbenchState(session=session, session_parent=tmp_path)
    state.ensure_session()
    assert state.paper_reconciliation is not None
    assert state.paper_reconciliation.ok is False

    report, backup = rebuild_session(session.root)
    assert report.ok is True and backup is not None
    journal_after_rebuild = (
        WorkbenchSession.create_or_load(tmp_path, "loop").journal_path.read_bytes()
    )

    payload = handle_post_paper_rehydrate(state)

    assert payload["ok"] is True
    assert payload["status"] == "ok"
    assert payload["rehydrated"] is True
    assert payload["session_id"] == "loop"
    assert state.paper_reconciliation is not None and state.paper_reconciliation.ok is True
    assert report.expected_book is not None
    assert state.ensure_book().cash == Decimal(str(report.expected_book["cash"]))
    # El rehydrate en sí no tocó los archivos que dejó el rebuild.
    assert state.ensure_session().journal_path.read_bytes() == journal_after_rebuild


def test_rehydrate_disconnects_broker_and_reports_it(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "brk")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    state.ensure_session()

    payload = handle_post_paper_rehydrate(state)

    assert payload["broker_connected"] is False
    assert state.broker is None
    assert "rebuild_via" in payload


def test_rehydrate_records_activity(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "act")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    state.ensure_session()

    handle_post_paper_rehydrate(state)

    activity = state.ensure_session().activity_path.read_text(encoding="utf-8")
    assert '"rehydrate"' in activity
    assert "paper.rehydrate" in activity


def test_openapi_declares_rehydrate_post_only() -> None:
    paths = build_openapi_schema()["paths"]
    route = paths["/api/paper/reconciliation/rehydrate"]
    assert "post" in route
    assert "get" not in route


def test_ui_wiring_rehydrate_button() -> None:
    static = (
        Path(__file__).resolve().parents[3] / "src" / "quantlab" / "workbench" / "static"
    )
    pane = (static / "js" / "panes" / "reconciliation.js").read_text(encoding="utf-8")
    assert "QLApi.paperRehydrate" in pane
    assert "recon-rehydrate" in pane
    assert "confirm(" in pane
    api = (static / "js" / "api.js").read_text(encoding="utf-8")
    assert "/api/paper/reconciliation/rehydrate" in api
