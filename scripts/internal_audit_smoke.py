#!/usr/bin/env python3
"""Smoke INTERNAL Zero-Trust — invariantes LIVE + imports workbench/brokers.

Uso:
  uv run python scripts/internal_audit_smoke.py

Exit 0 = all PASS; exit 1 = algún FAIL.
"""

from __future__ import annotations

import sys
import tempfile
from collections.abc import Callable
from pathlib import Path


def _smoke_tmp(name: str) -> Path:
    """Path temporal portable: Windows no tiene /tmp."""
    return Path(tempfile.gettempdir()) / name


def _check(name: str, fn: Callable[[], None]) -> bool:
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — smoke reporta cualquier fallo
        print(f"FAIL  {name}: {exc}")
        return False
    print(f"PASS  {name}")
    return True


def check_live_blocked() -> None:
    from quantlab.execution.live_gate import LIVE_BLOCKED

    assert LIVE_BLOCKED is True, f"LIVE_BLOCKED={LIVE_BLOCKED!r} (expected True)"


def check_live_gate_raises() -> None:
    from quantlab.core.exceptions import ValidationError
    from quantlab.execution.live_gate import assert_live_routing_blocked

    try:
        assert_live_routing_blocked()
    except ValidationError:
        return
    raise AssertionError("assert_live_routing_blocked should raise when LIVE_BLOCKED")


def check_brokers_imports() -> None:
    from quantlab.brokers.mode import REAL_ALIAS, ModeGuard, OperatingMode
    from quantlab.brokers.registry import get_default_registry

    assert REAL_ALIAS is OperatingMode.PAPER
    assert OperatingMode.LIVE in OperatingMode
    _ = ModeGuard
    reg = get_default_registry()
    venues = set(reg.list_venues())
    assert {"a3", "binance", "paper", "generic_csv", "generic_rest"}.issubset(venues), venues


def check_workbench_imports() -> None:
    from quantlab.workbench.api import WorkbenchState
    from quantlab.workbench.launch import main as _launch_main  # noqa: F401
    from quantlab.workbench.server import create_server

    state = WorkbenchState()
    assert state.mode.value in {"tester", "paper"}
    _ = create_server


def check_chat_safe() -> None:
    from quantlab.core.exceptions import ValidationError
    from quantlab.workbench.api import WorkbenchState
    from quantlab.workbench.chat.providers import FakeProvider, build_default_provider
    from quantlab.workbench.chat.tools import ALLOWED_TOOLS, FORBIDDEN_TOOLS, ToolRegistry

    provider = build_default_provider()
    assert isinstance(provider, FakeProvider), type(provider).__name__
    assert "submit_order" not in ALLOWED_TOOLS
    assert "place_order" in FORBIDDEN_TOOLS
    assert "set_live" in FORBIDDEN_TOOLS
    assert ALLOWED_TOOLS.isdisjoint(FORBIDDEN_TOOLS)
    for name in ("get_session_summary", "list_reports", "list_strategies"):
        assert name in ALLOWED_TOOLS

    reg = ToolRegistry(WorkbenchState())
    for bad in ("submit_order", "place_order", "set_live", "flip_live_blocked"):
        try:
            reg.call(bad)
        except ValidationError:
            continue
        raise AssertionError(f"expected reject for {bad}")


def check_f47_chat_context() -> None:
    """F47: chat context tools + FakeProvider ES + LIVE_BLOCKED."""
    import tempfile
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import WorkbenchState
    from quantlab.workbench.chat.providers import FakeProvider
    from quantlab.workbench.chat.tools import ALLOWED_TOOLS, FORBIDDEN_TOOLS, ToolRegistry
    from quantlab.workbench.session import WorkbenchSession
    from quantlab.workbench.strategy_catalog import CANONICAL_STRATEGY_IDS

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"
    assert "get_session_summary" in ALLOWED_TOOLS
    assert "list_reports" in ALLOWED_TOOLS
    assert "list_strategies" in ALLOWED_TOOLS
    assert ALLOWED_TOOLS.isdisjoint(FORBIDDEN_TOOLS)

    root = Path(tempfile.mkdtemp(prefix="quantlab-smoke-f47-"))
    session = WorkbenchSession.create_or_load(root, "smoke47")
    state = WorkbenchState(session=session)
    state.ensure_session()
    reg = ToolRegistry(state)

    summary = reg.call("get_session_summary", {"limit": 5})
    assert summary["ok"] is True
    assert summary["mode"] in {"tester", "paper"}
    assert "book_equity" in summary
    assert summary["positions_count"] >= 0
    assert summary["live_blocked"] is True

    reports = reg.call("list_reports")
    assert reports["ok"] is True
    assert reports["kind"] == "reports"

    strategies = reg.call("list_strategies")
    assert strategies["ok"] is True
    assert strategies["count"] == len(CANONICAL_STRATEGY_IDS)

    for bad in ("submit_order", "place_order", "set_live", "paper_submit"):
        try:
            reg.call(bad)
            raise AssertionError(f"expected reject for {bad}")
        except Exception as exc:  # noqa: BLE001
            assert "rechazada" in str(exc).lower()

    fake = FakeProvider()
    assert "get_session_summary" in fake.complete("¿cómo estoy?", reg).tools_used
    assert "get_session_summary" in fake.complete("resumen sesión", reg).tools_used
    assert "list_reports" in fake.complete("qué reportes hay", reg).tools_used
    assert "list_strategies" in fake.complete("estrategias", reg).tools_used


def check_health_dict() -> None:
    from quantlab import __version__
    from quantlab.infra.health import run_health_checks

    report = run_health_checks().to_dict()
    assert report.get("ok") is True
    assert report.get("live_blocked") is True
    assert report.get("version") == __version__


def check_about_version_matches() -> None:
    """F49: About / health version ≡ quantlab.__version__."""

    from quantlab import __version__
    from quantlab.infra.health import run_health_checks
    from quantlab.workbench.about import PHASES_SUMMARY, build_about_payload
    from quantlab.workbench.api import WorkbenchState, handle_get_about
    from quantlab.workbench.session import WorkbenchSession

    assert __version__ == "0.91.0"
    assert __version__.startswith("0.91")
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    about = build_about_payload()
    assert about["version"] == __version__
    assert about["phases_summary"] == PHASES_SUMMARY
    assert about["live_blocked"] is True

    health = run_health_checks().to_dict()
    assert health.get("version") == __version__

    root = _smoke_tmp("quantlab-smoke-f49-about-ver")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke49")
    state = WorkbenchState(session=session)
    state.ensure_session()
    body = handle_get_about(state)
    assert body["version"] == __version__
    assert body["version"] == about["version"]


def check_version_starts_with_084() -> None:
    """F89: tip version on 0.81.x line."""
    from quantlab import __version__
    from quantlab.workbench.about import PHASES_SUMMARY, build_about_payload

    assert __version__.startswith("0.91")
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"
    about = build_about_payload()
    assert about["version"].startswith("0.91")
    assert about["version"] == __version__
    assert about["live_blocked"] is True


def check_f59_a11y() -> None:
    """F59: index.html aria / role=dialog + palette focus trap."""
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = Path(__file__).resolve().parents[1]
    static = root / "src" / "quantlab" / "workbench" / "static"
    html = (static / "index.html").read_text(encoding="utf-8")
    assert "aria-label" in html
    assert 'role="dialog"' in html
    assert "Ir al contenido" in html
    assert 'aria-label="Menú inicio"' in html
    palette = (static / "js" / "command_palette.js").read_text(encoding="utf-8")
    assert "_trapFocus" in palette
    assert "aria-modal" in palette
    assert not (root / "docs" / "audit" / "FASE_59_APPROVED.md").exists()


def check_f60_i18n() -> None:
    """F60: i18n scaffold es default + en stub + GET /api/i18n/{locale}."""
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import WorkbenchState, handle_get_i18n
    from quantlab.workbench.i18n import DEFAULT_LOCALE, build_i18n_payload, load_messages

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"
    assert DEFAULT_LOCALE == "es"

    es = load_messages("es")
    en = load_messages("en")
    assert es["btn.save"] == "Guardar"
    assert en["btn.save"] == "Save"
    assert set(es.keys()) == set(en.keys())

    payload = build_i18n_payload("es")
    assert payload["ok"] is True
    assert payload["locale"] == "es"
    assert handle_get_i18n(WorkbenchState(), "en")["locale"] == "en"

    root = Path(__file__).resolve().parents[1]
    static = root / "src" / "quantlab" / "workbench" / "static"
    html = (static / "index.html").read_text(encoding="utf-8")
    assert 'src="/static/js/i18n.js"' in html
    assert "data-i18n" in html
    js = (static / "js" / "i18n.js").read_text(encoding="utf-8")
    assert "QLi18n" in js and "applyDom" in js
    shell = (static / "js" / "shell.js").read_text(encoding="utf-8")
    assert "applyLocale" in shell
    assert not (root / "docs" / "audit" / "FASE_60_APPROVED.md").exists()


def check_f61_access_log() -> None:
    """F61: access.jsonl append-only + settings.access_log + GET /api/access-log."""
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.access_log import AccessLog, list_access_log
    from quantlab.workbench.api import WorkbenchState, handle_get_access_log, record_http_access
    from quantlab.workbench.session import WorkbenchSession
    from quantlab.workbench.settings import default_settings

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"
    assert default_settings()["access_log"] is True

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_61_APPROVED.md").exists()

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        session = WorkbenchSession.create_or_load(Path(tmp), "smoke61")
        state = WorkbenchState(session=session)
        state.ensure_session()
        record_http_access(state, method="GET", path="/api/health", status=200, ms=0.4)
        payload = handle_get_access_log(state, "limit=10")
        assert payload["ok"] is True
        assert payload["kind"] == "access_log"
        assert payload["count"] >= 1
        assert payload["access_log_enabled"] is True
        listed = list_access_log(session.access_path, limit=5)
        assert listed["events"][-1]["path"] == "/api/health"
        row = AccessLog(session.access_path).read_tail(1)[0]
        assert "body" not in row and "headers" not in row


def check_f62_access_log_ui() -> None:
    """F62: Access Log panel UI + menú + command palette + auto-refresh."""
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.commands import list_commands

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_62_APPROVED.md").exists()

    payload = list_commands()
    ids = {c["id"] for c in payload["commands"]}
    assert "open.access_log" in ids

    static = root / "src" / "quantlab" / "workbench" / "static"
    index = (static / "index.html").read_text(encoding="utf-8")
    assert 'data-open="access_log"' in index
    assert "panes/access_log.js" in index
    js = (static / "js" / "panes" / "access_log.js").read_text(encoding="utf-8")
    assert "QLApi.getAccessLog" in js
    assert "Auto-refresh" in js
    assert "createAccessLogPane" in js
    shell = (static / "js" / "shell.js").read_text(encoding="utf-8")
    assert "access_log: openAccessLog" in shell


def check_f63_auto_backup() -> None:
    """F63: auto-backup settings + run_auto_backup + GET /api/backups."""
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import WorkbenchState, handle_get_backups
    from quantlab.workbench.auto_backup import MAX_BACKUPS, list_backups, run_auto_backup
    from quantlab.workbench.session import WorkbenchSession
    from quantlab.workbench.settings import default_settings

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"
    assert MAX_BACKUPS == 5
    assert default_settings()["auto_backup_minutes"] == 0

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_63_APPROVED.md").exists()

    import tempfile

    with tempfile.TemporaryDirectory(prefix="ql-f63-") as tmp:
        parent = Path(tmp)
        session = WorkbenchSession.create_or_load(parent, "smoke63")
        session.save_meta({"session_id": session.session_id})
        result = run_auto_backup(session)
        assert result.archive_path.is_file()
        assert "backups" in str(result.archive_path)
        listed = list_backups(session)
        assert listed["count"] >= 1
        state = WorkbenchState(session=session, session_parent=parent)
        api = handle_get_backups(state)
        assert api["ok"] is True
        assert api["kind"] == "backups"
        assert api["live_blocked"] is True


def check_f64_backups_ui() -> None:
    """F64: Backups panel UI + POST /api/backups/run + menú Inicio."""
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import WorkbenchState, handle_post_backups_run
    from quantlab.workbench.commands import list_commands
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_64_APPROVED.md").exists()

    payload = list_commands()
    ids = {c["id"] for c in payload["commands"]}
    assert "open.backups" in ids

    static = root / "src" / "quantlab" / "workbench" / "static"
    index = (static / "index.html").read_text(encoding="utf-8")
    assert 'data-open="backups"' in index
    assert "panes/backups.js" in index
    js = (static / "js" / "panes" / "backups.js").read_text(encoding="utf-8")
    assert "QLApi.getBackups" in js
    assert "QLApi.runBackup" in js
    assert "Backup ahora" in js
    shell = (static / "js" / "shell.js").read_text(encoding="utf-8")
    assert "backups: openBackups" in shell

    import tempfile

    with tempfile.TemporaryDirectory(prefix="ql-f64-") as tmp:
        parent = Path(tmp)
        session = WorkbenchSession.create_or_load(parent, "smoke64")
        session.save_meta({"session_id": session.session_id})
        state = WorkbenchState(session=session, session_parent=parent)
        out = handle_post_backups_run(state)
        assert out["ok"] is True
        assert out["kind"] == "backup_run"
        assert out["count"] >= 1


def check_f65_fills_csv() -> None:
    """F65: GET /api/paper/fills.csv header+rows + UI download buttons."""
    from datetime import UTC, datetime
    from decimal import Decimal
    from pathlib import Path

    from quantlab import __version__
    from quantlab.brokers.paper.journal import FILLS_CSV_COLUMNS
    from quantlab.brokers.types import PaperFill
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import WorkbenchState, handle_get_paper_fills_csv
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_65_APPROVED.md").exists()

    static = root / "src" / "quantlab" / "workbench" / "static"
    blotter = (static / "js" / "panes" / "blotter.js").read_text(encoding="utf-8")
    journal = (static / "js" / "panes" / "journal.js").read_text(encoding="utf-8")
    api = (static / "js" / "api.js").read_text(encoding="utf-8")
    assert "paperFillsCsvUrl" in api
    assert "/api/paper/fills.csv" in api
    assert "Descargar CSV" in blotter
    assert "Descargar CSV" in journal
    assert "QLApi.paperFillsCsvUrl" in blotter
    assert "QLApi.paperFillsCsvUrl" in journal

    import tempfile

    with tempfile.TemporaryDirectory(prefix="ql-f65-") as tmp:
        parent = Path(tmp)
        session = WorkbenchSession.create_or_load(parent, "smoke65")
        session.save_meta({"session_id": session.session_id})
        state = WorkbenchState(session=session, session_parent=parent)
        state.ensure_session()
        assert state.journal is not None
        state.journal.append(
            PaperFill(
                fill_id="smoke-f1",
                order_id="o1",
                symbol="BTC-USD",
                side="buy",
                quantity=Decimal("1"),
                price=Decimal("10"),
                ts=datetime(2026, 7, 26, 12, 0, 0, tzinfo=UTC),
                source="paper_broker",
            )
        )
        body, filename = handle_get_paper_fills_csv(state)
        text = body.decode("utf-8")
        lines = text.strip("\n").split("\n")
        assert lines[0] == ",".join(FILLS_CSV_COLUMNS)
        assert "smoke-f1" in lines[1]
        assert filename.endswith(".csv")


def check_f66_equity_curve() -> None:
    """F66: equity.jsonl append + GET /api/paper/equity + Positions sparkline."""
    from pathlib import Path

    from quantlab import __version__
    from quantlab.brokers.mode import OperatingMode
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
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_66_APPROVED.md").exists()

    static = root / "src" / "quantlab" / "workbench" / "static"
    positions = (static / "js" / "panes" / "positions.js").read_text(encoding="utf-8")
    api = (static / "js" / "api.js").read_text(encoding="utf-8")
    assert "paperEquity" in api
    assert "/api/paper/equity" in api
    assert "Equity curve" in positions
    assert "sparklineSvg" in positions
    assert "QLApi.paperEquity" in positions

    import tempfile

    with tempfile.TemporaryDirectory(prefix="ql-f66-") as tmp:
        parent = Path(tmp)
        session = WorkbenchSession.create_or_load(parent, "smoke66")
        state = WorkbenchState(
            session=session, session_parent=parent, mode=OperatingMode.TESTER
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
        filled = handle_get_paper_equity(state, "limit=50")
        assert filled["count"] >= 1
        assert set(filled["points"][-1].keys()) >= {"ts", "equity", "cash"}

        handle_post_paper_session_start(
            state,
            {"strategy_id": "dummy", "symbol": "BTCUSDT", "max_steps": 3},
        )
        before = handle_get_paper_equity(state, "limit=500")["count"]
        handle_post_paper_session_step(state)
        after = handle_get_paper_equity(state, "limit=500")["count"]
        assert after > before


def check_f67_paper_pnl() -> None:
    """F67: GET /api/paper/pnl + Positions/Blotter PnL header."""
    import tempfile
    from datetime import UTC, datetime
    from decimal import Decimal
    from pathlib import Path

    from quantlab import __version__
    from quantlab.brokers.mode import OperatingMode
    from quantlab.brokers.paper.book import PaperBook
    from quantlab.brokers.types import PaperFill
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_paper_pnl,
        handle_post_broker_connect,
        handle_post_paper_submit,
    )
    from quantlab.workbench.api_catalog import openapi_payload
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_67_APPROVED.md").exists()

    static = root / "src" / "quantlab" / "workbench" / "static"
    positions = (static / "js" / "panes" / "positions.js").read_text(encoding="utf-8")
    blotter = (static / "js" / "panes" / "blotter.js").read_text(encoding="utf-8")
    api = (static / "js" / "api.js").read_text(encoding="utf-8")
    assert "paperPnl" in api
    assert "/api/paper/pnl" in api
    assert "pos-pnl-header" in positions
    assert "QLApi.paperPnl" in positions
    assert "formatPnlHeader" in blotter
    assert "QLApi.paperPnl" in blotter
    assert "/api/paper/pnl" in openapi_payload()["paths"]

    book = PaperBook(initial_cash=Decimal("1000"))
    book.apply_fill(
        PaperFill(
            fill_id="s1",
            order_id="o1",
            symbol="TEST",
            side="buy",
            quantity=Decimal("2"),
            price=Decimal("100"),
            ts=datetime(2026, 7, 26, tzinfo=UTC),
        )
    )
    pnl = book.get_pnl(mark_prices={"TEST": Decimal("110")})
    assert pnl["realized"] == Decimal("0")
    assert pnl["unrealized"] == Decimal("20")
    assert pnl["equity"] == Decimal("1020")

    with tempfile.TemporaryDirectory(prefix="ql-f67-") as tmp:
        parent = Path(tmp)
        session = WorkbenchSession.create_or_load(parent, "smoke67")
        state = WorkbenchState(
            session=session, session_parent=parent, mode=OperatingMode.TESTER
        )
        handle_post_broker_connect(
            state, {"venue": "binance", "mode": "tester", "md_source": "fake"}
        )
        empty = handle_get_paper_pnl(state)
        assert empty["ok"] is True
        assert empty["kind"] == "pnl"
        assert empty["realized"] == "0"
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
        filled = handle_get_paper_pnl(state)
        assert filled["marks_source"] == "broker"
        assert set(filled.keys()) >= {
            "realized",
            "unrealized",
            "equity",
            "cash",
            "live_blocked",
        }


def check_f69_risk_utilization() -> None:
    """F69: GET /api/risk/utilization + Risk panel utilization section."""
    import tempfile
    from datetime import UTC, datetime
    from decimal import Decimal
    from pathlib import Path

    from quantlab import __version__
    from quantlab.brokers.paper.book import PaperBook
    from quantlab.brokers.types import PaperFill
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import WorkbenchState, handle_get_risk_utilization
    from quantlab.workbench.api_catalog import openapi_payload
    from quantlab.workbench.risk import PaperRiskLimits
    from quantlab.workbench.risk_utilization import compute_risk_utilization
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_69_APPROVED.md").exists()

    static = root / "src" / "quantlab" / "workbench" / "static"
    risk_js = (static / "js" / "panes" / "risk.js").read_text(encoding="utf-8")
    api_js = (static / "js" / "api.js").read_text(encoding="utf-8")
    assert "riskUtilization" in api_js
    assert "/api/risk/utilization" in api_js
    assert "risk-utilization" in risk_js
    assert "QLApi.riskUtilization" in risk_js
    assert "/api/risk/utilization" in openapi_payload()["paths"]

    book = PaperBook(initial_cash=Decimal("10000"))
    book.apply_fill(
        PaperFill(
            fill_id="s1",
            order_id="o1",
            symbol="TEST",
            side="buy",
            quantity=Decimal("5"),
            price=Decimal("100"),
            ts=datetime(2026, 7, 26, tzinfo=UTC),
        )
    )
    limits = PaperRiskLimits(max_qty=Decimal("10"), max_notional=Decimal("1000"))
    util = compute_risk_utilization(
        book, limits, mark_prices={"TEST": Decimal("110")}
    )
    assert util["used"]["qty"] == "5"
    assert util["used"]["notional"] == "550"
    assert Decimal(util["pct"]["qty"]) == Decimal("50")
    assert Decimal(util["pct"]["notional"]) == Decimal("55")

    with tempfile.TemporaryDirectory(prefix="ql-f69-") as tmp:
        parent = Path(tmp)
        session = WorkbenchSession.create_or_load(parent, "smoke69")
        state = WorkbenchState(
            session=session,
            session_parent=parent,
            risk=PaperRiskLimits(max_qty=Decimal("10"), max_notional=Decimal("5000")),
        )
        empty = handle_get_risk_utilization(state)
        assert empty["ok"] is True
        assert empty["kind"] == "risk_utilization"
        assert empty["used"]["qty"] == "0"
        assert empty["live_blocked"] is True
        state.ensure_book().apply_fill(
            PaperFill(
                fill_id="s2",
                order_id="o2",
                symbol="AAA",
                side="buy",
                quantity=Decimal("2"),
                price=Decimal("100"),
                ts=datetime(2026, 7, 26, tzinfo=UTC),
            )
        )
        filled = handle_get_risk_utilization(state)
        assert filled["session_id"] == "smoke69"
        assert filled["used"]["qty"] == "2"
        assert Decimal(filled["pct"]["qty"]) == Decimal("20")


def check_f70_paper_kill() -> None:
    """F70: paper kill switch — reject submit/step + Risk/Session UI."""
    import tempfile
    from pathlib import Path

    from quantlab import __version__
    from quantlab.brokers.mode import OperatingMode
    from quantlab.core.exceptions import ValidationError
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import (
        ApiError,
        WorkbenchState,
        handle_get_paper_kill,
        handle_post_broker_connect,
        handle_post_paper_kill,
        handle_post_paper_submit,
    )
    from quantlab.workbench.api_catalog import openapi_payload
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_70_APPROVED.md").exists()

    static = root / "src" / "quantlab" / "workbench" / "static"
    risk_js = (static / "js" / "panes" / "risk.js").read_text(encoding="utf-8")
    session_js = (static / "js" / "panes" / "paper_session.js").read_text(encoding="utf-8")
    api_js = (static / "js" / "api.js").read_text(encoding="utf-8")
    assert "ENGAGE KILL" in risk_js
    assert "setPaperKill" in risk_js
    assert "ENGAGE KILL" in session_js
    assert "/api/paper/kill" in api_js
    assert "paperKill" in api_js
    paths = openapi_payload()["paths"]
    assert "/api/paper/kill" in paths
    assert "post" in paths["/api/paper/kill"]
    assert "get" in paths["/api/paper/kill"]

    with tempfile.TemporaryDirectory(prefix="ql-f70-") as tmp:
        parent = Path(tmp)
        session = WorkbenchSession.create_or_load(parent, "smoke70")
        state = WorkbenchState(
            session=session,
            session_parent=parent,
            mode=OperatingMode.TESTER,
        )
        idle = handle_get_paper_kill(state)
        assert idle["engaged"] is False
        assert idle["kind"] == "paper_kill"
        engaged = handle_post_paper_kill(state, {"engaged": True})
        assert engaged["engaged"] is True
        assert state.paper_kill_engaged is True
        assert session.load_meta().get("paper_kill_engaged") is True

        handle_post_broker_connect(
            state, {"venue": "binance", "mode": "tester", "md_source": "fake"}
        )
        try:
            handle_post_paper_submit(
                state,
                {
                    "intent_type": "place_order",
                    "instrument_id": "BTCUSDT",
                    "side": "buy",
                    "quantity": "1",
                    "order_type": "market",
                },
            )
            raise AssertionError("submit should fail when kill engaged")
        except ApiError as exc:
            assert exc.status == 400
            assert "kill switch" in str(exc)
        try:
            state.assert_paper_kill_clear()
            raise AssertionError("assert should raise ValidationError")
        except ValidationError:
            pass

        handle_post_paper_kill(state, {"engaged": False})
        assert state.paper_kill_engaged is False


def check_f71_health_extended() -> None:
    """F71: health/about ops flags + empty-book edge cases · ≥1000 tests milestone."""
    import tempfile
    from decimal import Decimal
    from pathlib import Path

    from quantlab import __version__
    from quantlab.brokers.paper.book import PaperBook
    from quantlab.brokers.paper.journal import FILLS_CSV_COLUMNS, fills_to_csv
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
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
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_71_APPROVED.md").exists()

    health_js = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "panes" / "health.js"
    ).read_text(encoding="utf-8")
    about_js = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "about.js"
    ).read_text(encoding="utf-8")
    assert "paper_kill_engaged" in health_js
    assert "auto_backup_minutes" in health_js
    assert "access_log" in health_js
    assert "paper_kill_engaged" in about_js

    csv_empty = fills_to_csv([])
    assert csv_empty.startswith("ts,fill_id")
    assert csv_empty.strip("\n") == ",".join(FILLS_CSV_COLUMNS)

    with tempfile.TemporaryDirectory(prefix="ql-f71-") as tmp:
        parent = Path(tmp)
        session = WorkbenchSession.create_or_load(parent, "smoke71")
        state = WorkbenchState(session=session, session_parent=parent)
        health = handle_get_health(state)
        about = handle_get_about(state)
        assert health["paper_kill_engaged"] is False
        assert health["auto_backup_minutes"] == 0
        assert health["access_log"] is True
        assert about["paper_kill_engaged"] is False
        assert about["version"] == "0.91.0"

        handle_put_settings(state, {"access_log": False, "auto_backup_minutes": 45})
        handle_post_paper_kill(state, {"engaged": True})
        health2 = handle_get_health(state)
        assert health2["paper_kill_engaged"] is True
        assert health2["auto_backup_minutes"] == 45
        assert health2["access_log"] is False

        state.book = PaperBook(initial_cash=Decimal("1000"))
        pnl = handle_get_paper_pnl(state)
        assert pnl["equity"] == "1000"
        assert pnl["realized"] == "0"
        util = handle_get_risk_utilization(state)
        assert util["used"]["qty"] == "0"
        assert util["positions"] == []
        equity = handle_get_paper_equity(state, "limit=5")
        assert equity["count"] == 0
        backups = handle_get_backups(state)
        assert backups["count"] == 0
        body, _name = handle_get_paper_fills_csv(state)
        assert body.decode("utf-8").strip("\n") == ",".join(FILLS_CSV_COLUMNS)


def check_f72_desktop_notifications() -> None:
    """F72: settings.desktop_notifications default false + roundtrip + JS hooks."""
    import tempfile
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import WorkbenchState, handle_get_settings, handle_put_settings
    from quantlab.workbench.session import WorkbenchSession
    from quantlab.workbench.settings import default_settings

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"
    assert default_settings()["desktop_notifications"] is False

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_72_APPROVED.md").exists()

    toasts = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "toasts.js"
    ).read_text(encoding="utf-8")
    assert "setDesktopNotifications" in toasts
    assert "notifyKillEngage" in toasts
    assert "Notification" in toasts
    api_js = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "api.js"
    ).read_text(encoding="utf-8")
    assert "notifyKillEngage" in api_js
    settings_js = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "panes" / "settings.js"
    ).read_text(encoding="utf-8")
    assert "desktop_notifications" in settings_js
    assert "set-desktop-notif" in settings_js

    with tempfile.TemporaryDirectory(prefix="ql-f72-") as tmp:
        parent = Path(tmp)
        session = WorkbenchSession.create_or_load(parent, "smoke72")
        state = WorkbenchState(session=session, session_parent=parent)
        got = handle_get_settings(state)
        assert got["settings"]["desktop_notifications"] is False
        put = handle_put_settings(state, {"desktop_notifications": True})
        assert put["settings"]["desktop_notifications"] is True
        got2 = handle_get_settings(state)
        assert got2["settings"]["desktop_notifications"] is True
        put2 = handle_put_settings(state, {"desktop_notifications": False})
        assert put2["settings"]["desktop_notifications"] is False


def check_f73_sound_alerts() -> None:
    """F73: settings.sound_alerts default false + roundtrip + WebAudio hooks."""
    import tempfile
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import WorkbenchState, handle_get_settings, handle_put_settings
    from quantlab.workbench.session import WorkbenchSession
    from quantlab.workbench.settings import default_settings

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"
    assert default_settings()["sound_alerts"] is False

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_73_APPROVED.md").exists()

    toasts = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "toasts.js"
    ).read_text(encoding="utf-8")
    assert "setSoundAlerts" in toasts
    assert "playBeep" in toasts
    assert "AudioContext" in toasts
    assert "notifyKillEngage" in toasts
    settings_js = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "panes" / "settings.js"
    ).read_text(encoding="utf-8")
    assert "sound_alerts" in settings_js
    assert "set-sound-alerts" in settings_js
    shell = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "shell.js"
    ).read_text(encoding="utf-8")
    assert "setSoundAlerts" in shell

    with tempfile.TemporaryDirectory(prefix="ql-f73-") as tmp:
        parent = Path(tmp)
        session = WorkbenchSession.create_or_load(parent, "smoke73")
        state = WorkbenchState(session=session, session_parent=parent)
        got = handle_get_settings(state)
        assert got["settings"]["sound_alerts"] is False
        put = handle_put_settings(state, {"sound_alerts": True})
        assert put["settings"]["sound_alerts"] is True
        got2 = handle_get_settings(state)
        assert got2["settings"]["sound_alerts"] is True
        put2 = handle_put_settings(state, {"sound_alerts": False})
        assert put2["settings"]["sound_alerts"] is False


def check_f74_clock_timezone() -> None:
    """F74: settings.timezone default UTC + roundtrip + status bar clock hooks."""
    import tempfile
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import WorkbenchState, handle_get_settings, handle_put_settings
    from quantlab.workbench.session import WorkbenchSession
    from quantlab.workbench.settings import default_settings

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"
    assert default_settings()["timezone"] == "UTC"

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_74_APPROVED.md").exists()

    settings_js = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "panes" / "settings.js"
    ).read_text(encoding="utf-8")
    assert "timezone" in settings_js
    assert "set-timezone" in settings_js
    shell = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "shell.js"
    ).read_text(encoding="utf-8")
    assert "setClockTimezone" in shell
    assert "clockTimezone" in shell
    assert "timeZone" in shell

    with tempfile.TemporaryDirectory(prefix="ql-f74-") as tmp:
        parent = Path(tmp)
        session = WorkbenchSession.create_or_load(parent, "smoke74")
        state = WorkbenchState(session=session, session_parent=parent)
        got = handle_get_settings(state)
        assert got["settings"]["timezone"] == "UTC"
        assert got["allowed_timezones"] == ["UTC", "local"]
        put = handle_put_settings(state, {"timezone": "local"})
        assert put["settings"]["timezone"] == "local"
        got2 = handle_get_settings(state)
        assert got2["settings"]["timezone"] == "local"
        put2 = handle_put_settings(state, {"timezone": "UTC"})
        assert put2["settings"]["timezone"] == "UTC"


def check_f75_broker_heartbeat() -> None:
    """F75: GET /api/broker/heartbeat + status bar poll hooks."""
    import tempfile
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import (
        HEARTBEAT_POLL_SECONDS,
        WorkbenchState,
        handle_get_broker_heartbeat,
        handle_post_broker_connect,
    )
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"
    assert HEARTBEAT_POLL_SECONDS == 5

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_75_APPROVED.md").exists()

    static = root / "src" / "quantlab" / "workbench" / "static"
    html = (static / "index.html").read_text(encoding="utf-8")
    assert "sb-heartbeat" in html
    shell = (static / "js" / "shell.js").read_text(encoding="utf-8")
    assert "pollBrokerHeartbeat" in shell
    assert "brokerHeartbeat" in shell
    api = (static / "js" / "api.js").read_text(encoding="utf-8")
    assert "/api/broker/heartbeat" in api

    with tempfile.TemporaryDirectory(prefix="ql-f75-") as tmp:
        parent = Path(tmp)
        session = WorkbenchSession.create_or_load(parent, "smoke75")
        state = WorkbenchState(session=session, session_parent=parent)
        disc = handle_get_broker_heartbeat(state)
        assert disc["status"] == "disconnected"
        assert disc["ok"] is False
        assert disc["poll_seconds"] == 5
        handle_post_broker_connect(state, {"venue": "binance", "mode": "tester"})
        ok = handle_get_broker_heartbeat(state)
        assert ok["status"] == "ok"
        assert ok["ok"] is True
        assert ok["connected"] is True
        assert isinstance(ok["health"], dict)


def check_f76_broker_reconnect() -> None:
    """F76: POST /api/broker/reconnect + last_broker_connect meta + UI hooks."""
    import tempfile
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import (
        ApiError,
        WorkbenchState,
        handle_post_broker_connect,
        handle_post_broker_reconnect,
    )
    from quantlab.workbench.broker_reconnect import LAST_CONNECT_META_KEY, load_last_connect
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_76_APPROVED.md").exists()

    static = root / "src" / "quantlab" / "workbench" / "static"
    market = (static / "js" / "panes" / "market.js").read_text(encoding="utf-8")
    health = (static / "js" / "panes" / "health.js").read_text(encoding="utf-8")
    api = (static / "js" / "api.js").read_text(encoding="utf-8")
    assert "md-reconnect" in market
    assert "hp-reconnect" in health
    assert "/api/broker/reconnect" in api

    with tempfile.TemporaryDirectory(prefix="ql-f76-") as tmp:
        parent = Path(tmp)
        session = WorkbenchSession.create_or_load(parent, "smoke76")
        state = WorkbenchState(session=session, session_parent=parent)
        try:
            handle_post_broker_reconnect(state, {})
            raise AssertionError("reconnect without connect should fail")
        except ApiError as exc:
            assert exc.status == 400
        handle_post_broker_connect(
            state, {"venue": "binance", "mode": "tester", "md_source": "fake"}
        )
        cfg = load_last_connect(session)
        assert cfg is not None
        assert cfg["venue"] == "binance"
        assert LAST_CONNECT_META_KEY in session.load_meta()
        state.broker = None
        out = handle_post_broker_reconnect(state, {})
        assert out["ok"] is True
        assert out["reconnect"] is True
        assert out["venue"] == "binance"
        assert state.broker is not None


def check_f77_broker_disconnect() -> None:
    """F77: POST /api/broker/disconnect + keep last_connect + UI hooks."""
    import tempfile
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_broker_heartbeat,
        handle_post_broker_connect,
        handle_post_broker_disconnect,
        handle_post_broker_reconnect,
    )
    from quantlab.workbench.broker_reconnect import LAST_CONNECT_META_KEY, load_last_connect
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_77_APPROVED.md").exists()

    static = root / "src" / "quantlab" / "workbench" / "static"
    market = (static / "js" / "panes" / "market.js").read_text(encoding="utf-8")
    health = (static / "js" / "panes" / "health.js").read_text(encoding="utf-8")
    api = (static / "js" / "api.js").read_text(encoding="utf-8")
    assert "md-disconnect" in market
    assert "hp-disconnect" in health
    assert "/api/broker/disconnect" in api
    assert "QLApi.disconnect" in market

    with tempfile.TemporaryDirectory(prefix="ql-f77-") as tmp:
        parent = Path(tmp)
        session = WorkbenchSession.create_or_load(parent, "smoke77")
        state = WorkbenchState(session=session, session_parent=parent)
        # idempotent when not connected
        idle = handle_post_broker_disconnect(state, {})
        assert idle["ok"] is True
        assert idle["was_connected"] is False
        handle_post_broker_connect(
            state, {"venue": "binance", "mode": "tester", "md_source": "fake"}
        )
        assert state.broker is not None
        out = handle_post_broker_disconnect(state, {})
        assert out["ok"] is True
        assert out["disconnect"] is True
        assert out["was_connected"] is True
        assert out["previous_venue"] == "binance"
        assert out["has_last_connect"] is True
        assert state.broker is None
        assert LAST_CONNECT_META_KEY in session.load_meta()
        cfg = load_last_connect(session)
        assert cfg is not None
        assert cfg["venue"] == "binance"
        hb = handle_get_broker_heartbeat(state)
        assert hb["status"] == "disconnected"
        rc = handle_post_broker_reconnect(state, {})
        assert rc["ok"] is True
        assert rc["reconnect"] is True
        assert state.broker is not None


def check_f79_watchlist_io() -> None:
    """F79: GET /api/watchlist/export + POST /api/watchlist/import merge/replace."""
    import json
    import tempfile
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_watchlist_export,
        handle_post_watchlist_import,
        handle_put_watchlist,
    )
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_79_APPROVED.md").exists()

    static = root / "src" / "quantlab" / "workbench" / "static"
    universe = (static / "js" / "panes" / "universe.js").read_text(encoding="utf-8")
    api = (static / "js" / "api.js").read_text(encoding="utf-8")
    assert "un-export" in universe
    assert "un-import" in universe
    assert "/api/watchlist/export" in api
    assert "/api/watchlist/import" in api
    assert "watchlistExportUrl" in api
    assert "importWatchlist" in api

    with tempfile.TemporaryDirectory(prefix="ql-f79-") as tmp:
        parent = Path(tmp)
        session = WorkbenchSession.create_or_load(parent, "smoke79")
        state = WorkbenchState(session=session, session_parent=parent)
        state.ensure_session()
        handle_put_watchlist(state, {"symbols": ["SMOKE"]})
        body, filename = handle_get_watchlist_export(state)
        assert filename.endswith(".json")
        data = json.loads(body.decode("utf-8"))
        assert data["symbols"] == ["SMOKE"]
        merged = handle_post_watchlist_import(
            state, {"symbols": ["QLAB"], "mode": "merge"}
        )
        assert merged["ok"] is True
        assert "SMOKE" in merged["symbols"] and "QLAB" in merged["symbols"]
        replaced = handle_post_watchlist_import(
            state, {"symbols": ["ONLY"], "mode": "replace"}
        )
        assert replaced["symbols"] == ["ONLY"]


def check_f80_custom_presets() -> None:
    """F80: POST /api/presets/save + GET includes custom + apply custom."""
    import tempfile
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_presets,
        handle_post_presets_apply,
        handle_post_presets_save,
    )
    from quantlab.workbench.layout import save_layout
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_80_APPROVED.md").exists()

    static = root / "src" / "quantlab" / "workbench" / "static"
    html = (static / "index.html").read_text(encoding="utf-8")
    api = (static / "js" / "api.js").read_text(encoding="utf-8")
    shell = (static / "js" / "shell.js").read_text(encoding="utf-8")
    assert 'id="btn-preset-save"' in html
    assert 'id="custom-presets"' in html
    assert "/api/presets/save" in api
    assert "savePreset" in api
    assert "saveCurrentAsPreset" in shell

    with tempfile.TemporaryDirectory(prefix="ql-f80-") as tmp:
        parent = Path(tmp)
        session = WorkbenchSession.create_or_load(parent, "smoke80")
        state = WorkbenchState(session=session, session_parent=parent)
        state.ensure_session()
        save_layout(
            session.layout_path,
            {
                "version": 1,
                "windows": {
                    "health": {"x": 10, "y": 10, "w": 400, "h": 300, "z": 1},
                },
            },
        )
        saved = handle_post_presets_save(state, {"name": "smoke_desk"})
        assert saved["ok"] is True
        assert saved["preset"]["custom"] is True
        assert (session.presets_dir / "smoke_desk.json").is_file()
        listed = handle_get_presets(state)
        assert listed["custom_count"] == 1
        assert "smoke_desk" in listed["names"]
        applied = handle_post_presets_apply(state, {"name": "smoke_desk"})
        assert applied["ok"] is True
        assert applied["preset"]["custom"] is True
        assert "health" in applied["layout"]["windows"]


def check_f81_preset_delete() -> None:
    """F81: DELETE /api/presets/{name} custom only; builtins protected."""
    import tempfile
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import (
        ApiError,
        WorkbenchState,
        handle_delete_presets,
        handle_get_presets,
        handle_post_presets_save,
    )
    from quantlab.workbench.layout import save_layout
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_81_APPROVED.md").exists()

    static = root / "src" / "quantlab" / "workbench" / "static"
    api = (static / "js" / "api.js").read_text(encoding="utf-8")
    shell = (static / "js" / "shell.js").read_text(encoding="utf-8")
    assert "deletePreset" in api
    assert "/api/presets/" in api
    assert "deleteCustomPreset" in shell
    assert "data-preset-delete" in shell

    with tempfile.TemporaryDirectory(prefix="ql-f81-") as tmp:
        parent = Path(tmp)
        session = WorkbenchSession.create_or_load(parent, "smoke81")
        state = WorkbenchState(session=session, session_parent=parent)
        state.ensure_session()
        save_layout(
            session.layout_path,
            {
                "version": 1,
                "windows": {
                    "market": {"x": 10, "y": 10, "w": 400, "h": 300, "z": 1},
                },
            },
        )
        saved = handle_post_presets_save(state, {"name": "smoke_del"})
        assert saved["ok"] is True
        assert (session.presets_dir / "smoke_del.json").is_file()
        deleted = handle_delete_presets(state, "smoke_del")
        assert deleted["ok"] is True
        assert deleted["kind"] == "preset_deleted"
        assert not (session.presets_dir / "smoke_del.json").exists()
        listed = handle_get_presets(state)
        assert listed["custom_count"] == 0
        for builtin in ("research", "trading_paper", "ops"):
            try:
                handle_delete_presets(state, builtin)
                raise AssertionError(f"builtin {builtin} should not delete")
            except ApiError as exc:
                assert exc.status == 400
                assert "built-in" in exc.message


def check_f83_minimize_all() -> None:
    """F83: minimizeAll/restoreAll + commands + menu persist layout."""
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.commands import list_commands

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_83_APPROVED.md").exists()

    payload = list_commands()
    ids = {c["id"] for c in payload["commands"]}
    assert "action.minimize_all" in ids
    assert "action.restore_all" in ids

    wm = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "wm.js"
    ).read_text(encoding="utf-8")
    assert "minimizeAll" in wm
    assert "restoreAll" in wm
    assert "WindowManager.prototype.minimizeAll" in wm
    assert "WindowManager.prototype.restoreAll" in wm
    assert "scheduleSave()" in wm

    palette = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "command_palette.js"
    ).read_text(encoding="utf-8")
    assert "minimize_all" in palette
    assert "restore_all" in palette

    index = (
        root / "src" / "quantlab" / "workbench" / "static" / "index.html"
    ).read_text(encoding="utf-8")
    assert 'data-wm-action="minimize_all"' in index
    assert 'data-wm-action="restore_all"' in index


def check_f84_cascade_tile() -> None:
    """F84: cascadeWindows/tileWindows + pure helpers + commands + menu."""
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.commands import list_commands
    from quantlab.workbench.window_layout import cascade_rects, tile_rects

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_84_APPROVED.md").exists()

    payload = list_commands()
    ids = {c["id"] for c in payload["commands"]}
    assert "action.cascade_windows" in ids
    assert "action.tile_windows" in ids

    wm = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "wm.js"
    ).read_text(encoding="utf-8")
    assert "function cascadeRects(" in wm
    assert "function tileRects(" in wm
    assert "WindowManager.prototype.cascadeWindows" in wm
    assert "WindowManager.prototype.tileWindows" in wm
    assert "scheduleSave()" in wm
    assert "QLCascadeRects" in wm
    assert "QLTileRects" in wm

    palette = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "command_palette.js"
    ).read_text(encoding="utf-8")
    assert "cascade_windows" in palette
    assert "tile_windows" in palette

    index = (
        root / "src" / "quantlab" / "workbench" / "static" / "index.html"
    ).read_text(encoding="utf-8")
    assert 'data-wm-action="cascade_windows"' in index
    assert 'data-wm-action="tile_windows"' in index

    casc = cascade_rects(3, 800, 600)
    assert len(casc) == 3
    assert casc[0]["x"] == 24 and casc[0]["y"] == 24
    assert casc[1]["x"] == 52 and casc[1]["y"] == 52
    tiled = tile_rects(4, 800, 600)
    assert len(tiled) == 4
    assert tiled[0]["x"] == 4 and tiled[0]["y"] == 4


def check_f85_zorder() -> None:
    """F85: bringToFront/sendToBack + context menu + commands + layout z."""
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.commands import list_commands
    from quantlab.workbench.layout import normalize_layout

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_85_APPROVED.md").exists()

    payload = list_commands()
    ids = {c["id"] for c in payload["commands"]}
    assert "action.bring_to_front" in ids
    assert "action.send_to_back" in ids

    wm = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "wm.js"
    ).read_text(encoding="utf-8")
    assert "WindowManager.prototype.bringToFront" in wm
    assert "WindowManager.prototype.sendToBack" in wm
    assert "_showWindowContextMenu" in wm
    assert "scheduleSave()" in wm

    palette = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "command_palette.js"
    ).read_text(encoding="utf-8")
    assert "bring_to_front" in palette
    assert "send_to_back" in palette

    shell = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "shell.js"
    ).read_text(encoding="utf-8")
    assert "bring_to_front" in shell
    assert "send_to_back" in shell
    assert "g.z" in shell

    index = (
        root / "src" / "quantlab" / "workbench" / "static" / "index.html"
    ).read_text(encoding="utf-8")
    assert 'data-wm-action="bring_to_front"' in index
    assert 'data-wm-action="send_to_back"' in index

    layout = normalize_layout(
        {
            "version": 1,
            "windows": {"health": {"x": 1, "y": 2, "w": 300, "h": 200, "z": 15}},
        }
    )
    assert layout["windows"]["health"]["z"] == 15


def check_f86_maximize() -> None:
    """F86: maximize/restoreFromMaximize + dblclick + commands + layout."""
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.commands import list_commands
    from quantlab.workbench.layout import normalize_layout

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_86_APPROVED.md").exists()

    payload = list_commands()
    ids = {c["id"] for c in payload["commands"]}
    assert "action.maximize_window" in ids
    assert "action.restore_from_maximize" in ids

    wm = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "wm.js"
    ).read_text(encoding="utf-8")
    assert "WindowManager.prototype.maximize" in wm
    assert "WindowManager.prototype.restoreFromMaximize" in wm
    assert "WindowManager.prototype.toggleMaximize" in wm
    assert "rec.preMax" in wm
    assert "scheduleSave()" in wm

    palette = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "command_palette.js"
    ).read_text(encoding="utf-8")
    assert "maximize_window" in palette
    assert "restore_from_maximize" in palette

    shell = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "shell.js"
    ).read_text(encoding="utf-8")
    assert "maximize_window" in shell
    assert "restore_from_maximize" in shell
    assert "g.maximized" in shell

    index = (
        root / "src" / "quantlab" / "workbench" / "static" / "index.html"
    ).read_text(encoding="utf-8")
    assert 'data-wm-action="maximize_window"' in index
    assert 'data-wm-action="restore_from_maximize"' in index

    layout = normalize_layout(
        {
            "version": 1,
            "windows": {
                "health": {
                    "x": 40,
                    "y": 40,
                    "w": 420,
                    "h": 320,
                    "maximized": True,
                }
            },
        }
    )
    assert layout["windows"]["health"]["maximized"] is True


def check_f87_broker_plugin_contract() -> None:
    """F87: versioned plugin spec, one-shot factory and read-only registry."""
    from pathlib import Path

    from quantlab import __version__
    from quantlab.brokers.contracts.v1 import BrokerPluginSpec
    from quantlab.brokers.generic.csv_md import GenericCsvMdBroker
    from quantlab.brokers.mode import OperatingMode
    from quantlab.brokers.port import BrokerPort
    from quantlab.brokers.testing.contract_v1 import run_broker_contract
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"
    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_87_APPROVED.md").exists()

    calls = 0

    def factory(mode: OperatingMode) -> BrokerPort:
        nonlocal calls
        calls += 1
        return GenericCsvMdBroker(mode=mode)

    spec = BrokerPluginSpec(
        api_version="1",
        venue_id="generic_csv",
        capabilities=frozenset({"market_data", "account_read"}),
        factory=factory,
    )
    report = run_broker_contract(spec)
    assert report.passed is True, report.issues
    assert calls == 1
    assert "registry.execution_blocked" in report.checks


def check_f82_window_snap() -> None:
    """F82: snapPosition on drag release + Python mirror + layout persist."""
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.snap_position import (
        DEFAULT_SNAP_THRESHOLD_PX,
        snap_position,
    )

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_82_APPROVED.md").exists()

    wm = (
        root / "src" / "quantlab" / "workbench" / "static" / "js" / "wm.js"
    ).read_text(encoding="utf-8")
    assert "function snapPosition(" in wm
    assert "SNAP_THRESHOLD_PX" in wm
    assert "QLSnapPosition" in wm
    assert "snapped = snapPosition(" in wm
    assert "self.scheduleSave()" in wm

    assert DEFAULT_SNAP_THRESHOLD_PX == 12
    assert snap_position(5, 8, 200, 150, 800, 600, 12) == (0, 0)
    assert snap_position(595, 445, 200, 150, 800, 600, 12) == (600, 450)
    assert snap_position(40, 50, 200, 150, 800, 600, 12) == (40, 50)


def check_paper_book_session() -> None:
    """F23: PaperBook fail-closed + session_id anti-traversal."""
    from decimal import Decimal

    from quantlab.brokers.paper.book import PaperBook
    from quantlab.core.exceptions import ValidationError
    from quantlab.workbench.risk import PaperRiskLimits
    from quantlab.workbench.session import WorkbenchSession, validate_session_id

    book = PaperBook(initial_cash=Decimal("1000"))
    assert book.cash == Decimal("1000")
    assert book.allow_short is False
    try:
        PaperBook(initial_cash=Decimal("100"), cash=Decimal("-1"))
    except ValidationError:
        pass
    else:
        raise AssertionError("negative cash should raise")

    validate_session_id("s1")
    for bad in ("../escape", "a/b", "..", ""):
        try:
            validate_session_id(bad)
        except ValidationError:
            continue
        raise AssertionError(f"expected reject session_id {bad!r}")

    _ = PaperRiskLimits
    _ = WorkbenchSession


def check_f23_book_import() -> None:
    """F23: import surface PaperBook / PaperBroker / journal."""
    from quantlab.brokers.paper import PaperBook, PaperBroker, PaperFillJournal
    from quantlab.brokers.paper.book import DEFAULT_INITIAL_CASH

    assert DEFAULT_INITIAL_CASH > 0
    _ = PaperBook, PaperBroker, PaperFillJournal


def check_f24_plugins() -> None:
    """F24: entry-point loader + generics en registry."""
    from quantlab.brokers.plugins import load_entry_point_brokers
    from quantlab.brokers.registry import BrokerRegistry, get_default_registry

    reg = get_default_registry()
    assert "generic_csv" in reg.list_venues()
    assert "generic_rest" in reg.list_venues()
    # loader no crashea sobre registry vacío
    empty = BrokerRegistry()
    load_entry_point_brokers(empty)


def check_f25_launch_parser() -> None:
    """F25: --allow-non-loopback en parser + is_loopback_host."""
    from quantlab.workbench.launch import build_parser, is_loopback_host

    parser = build_parser()
    ns = parser.parse_args(["--allow-non-loopback", "--host", "0.0.0.0"])
    assert ns.allow_non_loopback is True
    assert is_loopback_host("127.0.0.1") is True
    assert is_loopback_host("0.0.0.0") is False
    # flag presente en help
    help_txt = parser.format_help()
    assert "--allow-non-loopback" in help_txt
    assert "--slippage-bps" in help_txt


def check_f25_ops_desk_invariants() -> None:
    """F25: experiment_id charset + slip adverso + risk payload."""
    from decimal import Decimal

    from quantlab.brokers.paper.broker import apply_paper_slippage
    from quantlab.core.exceptions import ValidationError
    from quantlab.workbench.api import WorkbenchState, handle_get_risk
    from quantlab.workbench.lab_services import validate_experiment_id

    assert validate_experiment_id("wb-ok") == "wb-ok"
    try:
        validate_experiment_id("../evil")
    except ValidationError:
        pass
    else:
        raise AssertionError("expected reject experiment_id traversal")

    assert apply_paper_slippage(Decimal("100"), "BUY", Decimal("100")) == Decimal("101")
    assert apply_paper_slippage(Decimal("100"), "SELL", Decimal("100")) == Decimal("99")

    state = WorkbenchState(slippage_bps=Decimal("3"))
    state.ensure_session()
    risk = handle_get_risk(state)
    assert risk.get("ok") is True
    assert risk.get("live_blocked") is True
    assert risk.get("slippage_bps") == "3"
    assert "max_qty" in risk.get("limits", {})


def check_f26_paper_session() -> None:
    """F26: PaperSessionRunner import + LIVE_BLOCKED + status shape."""
    from datetime import UTC, datetime
    from decimal import Decimal

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
    from quantlab.workbench.paper_session import (
        PaperSessionConfig,
        PaperSessionRunner,
        build_session_strategy,
    )
    from quantlab.workbench.risk import PaperRiskLimits

    assert LIVE_BLOCKED is True
    _ = build_session_strategy("dummy")
    _ = PaperSessionConfig(strategy_id="buy_once", symbol="X", max_steps=2)

    class _Md:
        @property
        def venue_id(self) -> str:
            return "smoke-md"

        def connect(self) -> dict[str, object]:
            return {}

        def close(self) -> dict[str, object]:
            return {}

        def health(self) -> dict[str, object]:
            return {}

        def list_instruments(self) -> list[BrokerInstrument]:
            return []

        def get_snapshot(self, symbol: str) -> BrokerSnapshot:
            return BrokerSnapshot(
                symbol=symbol,
                bid=Decimal("9"),
                ask=Decimal("11"),
                last=Decimal("10"),
                ts=datetime(2024, 1, 1, tzinfo=UTC),
            )

        def get_account(self) -> BrokerAccount:
            return BrokerAccount(cash=Decimal("1"), currency="USD")

        def get_positions(self) -> list[BrokerPosition]:
            return []

        def submit(self, intent: OrderIntent) -> BrokerAck:
            raise AssertionError("no venue submit")

        def cancel(self, order_id: str) -> BrokerAck:
            raise AssertionError("no venue cancel")

    book = PaperBook()
    broker = PaperBroker(_Md(), book=book)
    runner = PaperSessionRunner(broker, PaperRiskLimits(), book)
    st = runner.status()
    assert st["running"] is False
    assert st["live_blocked"] is True

    # Fail-closed: MD/venue stub no es PaperBroker
    try:
        PaperSessionRunner(_Md(), PaperRiskLimits(), book)  # type: ignore[arg-type]
    except Exception as exc:
        assert "PaperBroker" in str(exc)
    else:
        raise AssertionError("expected reject non-PaperBroker")

    runner.start(PaperSessionConfig(strategy_id="buy_once", symbol="X", max_steps=2))
    summary = runner.step()
    assert summary.get("live_routing") is False
    assert summary.get("live_blocked") is True
    runner.stop()


def check_f27_strategy_catalog() -> None:
    """F27: catálogo + MM wire + lab strategies sin LIVE."""
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.lab_services import lab_strategies, run_lab_backtest
    from quantlab.workbench.strategy_catalog import (
        CANONICAL_STRATEGY_IDS,
        build_strategy,
        list_strategy_catalog,
        normalize_strategy_id,
    )

    assert LIVE_BLOCKED is True
    assert "inventory_mm" in CANONICAL_STRATEGY_IDS
    assert "avellaneda_stoikov" in CANONICAL_STRATEGY_IDS
    assert normalize_strategy_id("as") == "avellaneda_stoikov"
    cats = list_strategy_catalog()
    assert len(cats) == len(CANONICAL_STRATEGY_IDS)
    for sid in CANONICAL_STRATEGY_IDS:
        build_strategy(sid).reset()
        result = run_lab_backtest(strategy_id=sid, n_bars=8)
        assert result["ok"] is True
        assert result["live_blocked"] is True
        assert result["live_routing"] is False
    body = lab_strategies()
    assert body["ok"] is True
    assert "inventory_mm" in body["ids"]


def check_f28_layout_journal() -> None:
    """F28: layout save/load + API handlers + LIVE_BLOCKED."""

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import WorkbenchState, handle_get_layout, handle_put_layout
    from quantlab.workbench.layout import load_layout, save_layout
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    root = _smoke_tmp("quantlab-smoke-f28-layout")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke28")
    path = session.layout_path
    saved = save_layout(
        path,
        {"version": 1, "windows": {"health": {"x": 1, "y": 2, "w": 300, "h": 200}}},
    )
    assert load_layout(path) == saved
    state = WorkbenchState(session=session)
    state.ensure_session()
    put = handle_put_layout(
        state,
        {"layout": {"version": 1, "windows": {"journal": {"x": 5, "y": 6, "w": 400, "h": 300}}}},
    )
    assert put["ok"] is True
    assert put["live_blocked"] is True
    got = handle_get_layout(state)
    assert got["layout"]["windows"]["journal"]["w"] == 400


def check_f29_reports() -> None:
    """F29: persist report tras backtest + list/get + LIVE_BLOCKED."""

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_lab_report,
        handle_get_lab_reports,
        handle_post_lab_backtest,
    )
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    root = _smoke_tmp("quantlab-smoke-f29-reports")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke29")
    state = WorkbenchState(session=session)
    state.ensure_session()
    body = handle_post_lab_backtest(
        state,
        {"strategy_id": "momentum", "n_bars": 10, "experiment_id": "wb-smoke29"},
    )
    assert body["ok"] is True
    assert body["live_blocked"] is True
    assert body["report_id"]
    listed = handle_get_lab_reports(state)
    assert listed["ok"] is True
    assert listed["count"] >= 1
    detail = handle_get_lab_report(state, body["report_id"])
    assert detail["has_html"] is True
    assert detail["live_routing"] is False


def check_f30_universe_catalog() -> None:
    """F30: watchlist + universe + catalog empty-ok + LIVE_BLOCKED."""

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_catalog,
        handle_get_universe,
        handle_get_watchlist,
        handle_put_watchlist,
    )
    from quantlab.workbench.catalog_browser import list_catalog_datasets
    from quantlab.workbench.session import WorkbenchSession
    from quantlab.workbench.watchlist import load_watchlist, save_watchlist

    assert LIVE_BLOCKED is True
    root = _smoke_tmp("quantlab-smoke-f30-universe")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke30")
    state = WorkbenchState(session=session)
    state.ensure_session()

    saved = save_watchlist(session.watchlist_path, {"version": 1, "symbols": ["SMOKE"]})
    assert load_watchlist(session.watchlist_path) == saved
    put = handle_put_watchlist(state, {"add": ["QLAB"]})
    assert put["ok"] is True
    assert put["live_blocked"] is True
    assert "QLAB" in put["symbols"]
    got = handle_get_watchlist(state)
    assert "SMOKE" in got["symbols"]

    uni = handle_get_universe(state)
    assert uni["ok"] is True
    assert uni["live_blocked"] is True
    assert any(s["symbol"] == "QLAB" for s in uni["symbols"])

    cat = handle_get_catalog(state)
    assert cat["ok"] is True
    assert cat["read_only"] is True
    assert isinstance(cat["datasets"], list)
    # Empty-ok si no hay archivo local (no crea DB).
    offline = list_catalog_datasets(catalog_path=_smoke_tmp("quantlab-no-such-catalog.sqlite"))
    assert offline["available"] is False
    assert offline["datasets"] == []


def check_f31_features_store() -> None:
    """F31: feature store list + pipeline persist + LIVE_BLOCKED."""
    from pathlib import Path

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_lab_features_store,
        handle_post_lab_features,
    )
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    root = _smoke_tmp("quantlab-smoke-f31-features")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke31")
    state = WorkbenchState(session=session)
    state.ensure_session()

    empty = handle_get_lab_features_store(state)
    assert empty["ok"] is True
    assert empty["read_only"] is True
    assert empty["live_blocked"] is True
    assert empty["source"] == "session"
    assert isinstance(empty["artifacts"], list)

    run = handle_post_lab_features(state, {"n_bars": 10})
    assert run["ok"] is True
    assert run["persisted"] is True
    assert run["live_routing"] is False
    assert "log_return" in run["columns"]
    assert Path(run["store_ref"]["path"]).is_file()

    listed = handle_get_lab_features_store(state)
    assert listed["count"] >= 1
    assert listed["live_blocked"] is True


def check_f32_validation_runner() -> None:
    """F32: validation run + persist + anti-leakage + LIVE_BLOCKED."""
    from pathlib import Path

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_lab_validation,
        handle_post_lab_validation_run,
    )
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    root = _smoke_tmp("quantlab-smoke-f32-validation")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke32")
    state = WorkbenchState(session=session)
    state.ensure_session()

    preview = handle_get_lab_validation(state)
    assert preview["ok"] is True
    assert "anti_leakage" in preview
    assert preview["walk_forward"]["n_folds"] >= 1

    run = handle_post_lab_validation_run(state, {"n_bars": 40})
    assert run["ok"] is True
    assert run["persisted"] is True
    assert run["live_routing"] is False
    assert run["anti_leakage"]["ok"] is True
    assert Path(run["path"]).is_file()
    assert run["train_val_oos"]["segments"]["train"]["start_idx"] == 0

    listed = handle_get_lab_validation(state)
    assert listed["count"] >= 1
    assert listed["persisted"] is True
    assert listed["live_blocked"] is True


def check_f33_optimizer_history() -> None:
    """F33: optimize + Pareto + persist history + LIVE_BLOCKED."""
    from pathlib import Path

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_lab_optimize_history,
        handle_post_lab_optimize,
    )
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    root = _smoke_tmp("quantlab-smoke-f33-optimizer")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke33")
    state = WorkbenchState(session=session)
    state.ensure_session()

    empty = handle_get_lab_optimize_history(state)
    assert empty["ok"] is True
    assert empty["kind"] == "optimize_history"

    run = handle_post_lab_optimize(state, {"lookbacks": [2, 3], "quantities": ["1"], "n_bars": 16})
    assert run["ok"] is True
    assert run["persisted"] is True
    assert run["live_routing"] is False
    assert run["pareto"] is not None
    assert run["pareto"]["n_front"] >= 1
    assert Path(run["path"]).is_file()

    listed = handle_get_lab_optimize_history(state)
    assert listed["count"] >= 1
    assert listed["persisted"] is True
    assert listed["live_blocked"] is True


def check_f34_mc_export() -> None:
    """F34: montecarlo history + HB exports list + LIVE_BLOCKED."""
    from pathlib import Path

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_lab_exports,
        handle_get_lab_montecarlo_history,
        handle_post_lab_export_hb,
        handle_post_lab_montecarlo,
    )
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    root = _smoke_tmp("quantlab-smoke-f34-mc-export")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke34")
    state = WorkbenchState(session=session)
    state.ensure_session()

    empty = handle_get_lab_montecarlo_history(state)
    assert empty["ok"] is True
    assert empty["kind"] == "montecarlo_history"

    run = handle_post_lab_montecarlo(state, {"n_scenarios": 3, "n_bars": 12})
    assert run["ok"] is True
    assert run["persisted"] is True
    assert run["live_routing"] is False
    assert run["ci_low"] is not None
    assert Path(run["path"]).is_file()

    listed = handle_get_lab_montecarlo_history(state)
    assert listed["count"] >= 1
    assert listed["persisted"] is True
    assert listed["live_blocked"] is True

    exp = handle_post_lab_export_hb(
        state, {"experiment_id": "wb-hb-export", "strategy_version": "demo-1"}
    )
    assert exp["ok"] is True
    assert exp["live_routing"] is False
    assert Path(exp["path"]).is_file()

    exports = handle_get_lab_exports(state)
    assert exports["ok"] is True
    assert exports["count"] >= 1
    assert exports["live_routing"] is False


def check_f35_commands() -> None:
    """F35: /api/commands registry + LIVE_BLOCKED + no live actions."""

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import WorkbenchState, handle_get_commands
    from quantlab.workbench.commands import PANE_SHORTCUT_ORDER, list_commands
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    payload = list_commands()
    assert payload["ok"] is True
    assert payload["kind"] == "commands"
    assert payload["live_blocked"] is True
    assert payload["live_routing"] is False
    assert payload["count"] >= 20
    assert payload["pane_shortcut_order"] == list(PANE_SHORTCUT_ORDER)
    ids = {c["id"] for c in payload["commands"]}
    assert "open.health" in ids
    assert "action.health_refresh" in ids
    assert "action.close_focused" in ids
    assert "action.minimize_all" in ids
    assert "action.restore_all" in ids
    assert "action.cascade_windows" in ids
    assert "action.tile_windows" in ids
    for cmd in payload["commands"]:
        assert cmd["safe"] is True
        assert cmd["live"] is False

    root = _smoke_tmp("quantlab-smoke-f35-commands")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke35")
    state = WorkbenchState(session=session)
    body = handle_get_commands(state)
    assert body["ok"] is True
    assert body["count"] == len(body["commands"])


def check_f36_settings() -> None:
    """F36: settings.json + GET/PUT /api/settings + LIVE_BLOCKED."""

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_settings,
        handle_put_settings,
    )
    from quantlab.workbench.session import WorkbenchSession
    from quantlab.workbench.settings import default_settings, load_settings, save_settings

    assert LIVE_BLOCKED is True
    defaults = default_settings()
    assert defaults["locale"] == "es"
    assert defaults["theme"] == "slate"

    root = _smoke_tmp("quantlab-smoke-f36-settings")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke36")
    state = WorkbenchState(session=session)
    state.ensure_session()

    got = handle_get_settings(state)
    assert got["ok"] is True
    assert got["kind"] == "settings"
    assert got["live_blocked"] is True
    assert got["live_routing"] is False
    assert got["settings"]["locale"] == "es"

    put = handle_put_settings(
        state,
        {
            "theme": "high-contrast",
            "default_venue": "paper",
            "default_strategy": "momentum",
            "slippage_bps": "7",
            "locale": "es",
        },
    )
    assert put["ok"] is True
    assert put["settings"]["theme"] == "high-contrast"
    assert session.settings_path.is_file()
    loaded = load_settings(session.settings_path)
    assert loaded["default_venue"] == "paper"
    saved = save_settings(session.settings_path, loaded)
    assert saved["locale"] == "es"


def check_f37_onboarding() -> None:
    """F37: onboarding meta + GET/POST /api/onboarding + LIVE_BLOCKED."""

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_onboarding,
        handle_post_onboarding_complete,
    )
    from quantlab.workbench.onboarding import ONBOARDING_STEPS, is_onboarding_done
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert len(ONBOARDING_STEPS) == 4

    root = _smoke_tmp("quantlab-smoke-f37-onboarding")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke37")
    # Reset flag for idempotent smoke reruns
    meta = session.load_meta()
    meta.pop("onboarding_done", None)
    meta.pop("onboarding_completed_at", None)
    session.save_meta(meta)

    state = WorkbenchState(session=session)
    state.ensure_session()
    got = handle_get_onboarding(state)
    assert got["ok"] is True
    assert got["kind"] == "onboarding"
    assert got["onboarding_done"] is False
    assert got["show_wizard"] is True
    assert got["live_blocked"] is True
    assert got["live_routing"] is False

    done = handle_post_onboarding_complete(state, {})
    assert done["onboarding_done"] is True
    assert done["show_wizard"] is False
    assert is_onboarding_done(session.load_meta()) is True


def check_f38_docs_help() -> None:
    """F38: docs list/content + path traversal fail-closed + LIVE_BLOCKED."""

    from quantlab.core.exceptions import ValidationError
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import (
        ApiError,
        WorkbenchState,
        handle_get_docs,
        handle_get_docs_content,
    )
    from quantlab.workbench.commands import list_commands
    from quantlab.workbench.docs_browser import list_docs, read_docs_content
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    listed = list_docs()
    assert listed["ok"] is True
    assert listed["count"] >= 1
    paths = {d["path"] for d in listed["docs"]}
    assert any(p.endswith(".md") and "/" not in p for p in paths)
    assert any(p.startswith("ops/") and p.endswith(".md") for p in paths)

    sample = next(iter(paths))
    content = read_docs_content(sample)
    assert content["ok"] is True
    assert "content" in content

    for bad in ("../pyproject.toml", "audit/INTERNAL_AUDIT_F37.md"):
        try:
            read_docs_content(bad)
        except ValidationError:
            pass
        else:
            raise AssertionError(f"expected ValidationError for {bad!r}")

    root = _smoke_tmp("quantlab-smoke-f38-docs")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke38")
    state = WorkbenchState(session=session)
    state.ensure_session()
    got = handle_get_docs(state)
    assert got["ok"] is True
    assert got["kind"] == "docs"
    assert got["live_blocked"] is True
    assert got["live_routing"] is False

    body = handle_get_docs_content(state, f"path={sample}")
    assert body["ok"] is True
    assert body["path"] == sample

    try:
        handle_get_docs_content(state, "path=../etc/passwd")
    except ApiError:
        pass
    else:
        raise AssertionError("expected ApiError for path traversal")

    cmds = list_commands()
    ids = {c["id"] for c in cmds["commands"]}
    assert "open.docs" in ids


def check_f39_session_zip() -> None:
    """F39: session export/import ZIP + zip-slip fail-closed + LIVE_BLOCKED."""
    import zipfile

    from quantlab.core.exceptions import ValidationError
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_session_export,
        handle_post_session_import,
    )
    from quantlab.workbench.session import WorkbenchSession
    from quantlab.workbench.session_zip import MANIFEST_NAME, export_session, import_session_zip

    assert LIVE_BLOCKED is True
    root = _smoke_tmp("quantlab-smoke-f39-zip")
    if root.exists():
        import shutil

        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke39")
    (session.reports_dir / "smoke.json").write_text('{"ok":true}\n', encoding="utf-8")
    (session.root / ".env").write_text("NO=1\n", encoding="utf-8")

    result = export_session(session)
    assert result.archive_path.is_file()
    with zipfile.ZipFile(result.archive_path, "r") as zf:
        names = set(zf.namelist())
    assert MANIFEST_NAME in names
    assert ".env" not in names

    imported = import_session_zip(
        result.archive_path,
        session_parent=root,
        mode="new",
        session_id="smoke39b",
    )
    assert imported.session_id == "smoke39b"
    assert (imported.session_root / "reports" / "smoke.json").is_file()

    evil = root / "evil.zip"
    with zipfile.ZipFile(evil, "w") as zf:
        zf.writestr(
            MANIFEST_NAME,
            '{"format":"quantlab_session_zip","format_version":1}',
        )
        zf.writestr("../pwn.txt", "x")
    try:
        import_session_zip(evil, session_parent=root, mode="new", session_id="evil39")
    except ValidationError:
        pass
    else:
        raise AssertionError("expected zip-slip ValidationError")

    state = WorkbenchState(session=session)
    state.ensure_session()
    exp = handle_get_session_export(state)
    assert exp["ok"] is True
    assert exp["live_blocked"] is True
    assert exp["live_routing"] is False
    got = handle_post_session_import(
        state,
        {"mode": "new", "session_id": "smoke39c", "zip_path": exp["path"]},
    )
    assert got["ok"] is True
    assert got["session_id"] == "smoke39c"


def check_f40_workspace_presets() -> None:
    """F40: presets research/trading_paper/ops + apply → layout.json."""

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_presets,
        handle_post_presets_apply,
    )
    from quantlab.workbench.layout import load_layout
    from quantlab.workbench.presets import PRESET_NAMES, apply_preset, list_presets
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    catalog = list_presets()
    assert catalog["count"] == 3
    assert set(PRESET_NAMES) == {"research", "trading_paper", "ops"}
    assert catalog["live_blocked"] is True

    root = _smoke_tmp("quantlab-smoke-f40-presets")
    if root.exists():
        import shutil

        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke40")
    state = WorkbenchState(session=session)
    state.ensure_session()

    listed = handle_get_presets(state)
    assert listed["ok"] is True
    assert listed["count"] == 3

    applied = handle_post_presets_apply(state, {"name": "research"})
    assert applied["ok"] is True
    assert applied["preset"]["name"] == "research"
    assert set(applied["layout"]["windows"].keys()) == {
        "health",
        "backtest",
        "reports",
        "chat",
    }
    loaded = load_layout(session.layout_path)
    assert "backtest" in loaded["windows"]

    ops = apply_preset(session.layout_path, "ops")
    assert set(ops["layout"]["windows"].keys()) == {
        "health",
        "settings",
        "docs",
        "catalog",
    }


def check_f41_activity_log() -> None:
    """F41: activity.jsonl append-only + GET /api/activity + hooks."""

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.activity import ACTIVITY_EVENT_TYPES, ActivityLog, list_activity
    from quantlab.workbench.api import (
        ApiError,
        WorkbenchState,
        handle_get_activity,
        handle_post_broker_connect,
        handle_post_lab_backtest,
    )
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert {
        "connect",
        "submit",
        "backtest",
        "optimize",
        "export",
        "error",
        "rehydrate",
    } == ACTIVITY_EVENT_TYPES

    root = _smoke_tmp("quantlab-smoke-f41-activity")
    if root.exists():
        import shutil

        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke41")
    state = WorkbenchState(session=session)
    state.ensure_session()
    assert session.activity_path.is_file()

    connected = handle_post_broker_connect(
        state, {"venue": "binance", "mode": "tester", "md_source": "fake"}
    )
    assert connected["ok"] is True

    bt = handle_post_lab_backtest(
        state,
        {"strategy_id": "momentum", "n_bars": 12, "experiment_id": "smoke-f41-bt"},
    )
    assert bt is not None

    try:
        handle_post_broker_connect(state, {"venue": ""})
        raise AssertionError("expected ApiError for empty venue")
    except ApiError:
        pass

    listed = handle_get_activity(state, "limit=100")
    assert listed["ok"] is True
    assert listed["kind"] == "activity"
    assert listed["live_blocked"] is True
    events = {e["event"] for e in listed["events"]}
    assert "connect" in events
    assert "backtest" in events
    assert "error" in events

    # Append-only direct write
    ActivityLog(session.activity_path).append("export", message="smoke-export")
    again = list_activity(session.activity_path, limit=50)
    assert any(e["event"] == "export" for e in again["events"])


def check_f42_ops_metrics() -> None:
    """F42: ops metrics JSON + prometheus text + live_gate.blocked."""

    from quantlab.core.exceptions import ValidationError
    from quantlab.execution.live_gate import LIVE_BLOCKED, assert_live_routing_blocked
    from quantlab.infra.ops_metrics import get_ops_metrics
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_ops_metrics,
        handle_get_ops_prometheus,
    )
    from quantlab.workbench.commands import list_commands
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    metrics = get_ops_metrics()
    metrics.reset()
    metrics.inc("health.runs", 1)
    try:
        assert_live_routing_blocked()
        raise AssertionError("expected ValidationError from live gate")
    except ValidationError:
        pass

    root = _smoke_tmp("quantlab-smoke-f42-ops")
    if root.exists():
        import shutil

        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke42")
    state = WorkbenchState(session=session)
    state.ensure_session()

    payload = handle_get_ops_metrics(state)
    assert payload["ok"] is True
    assert payload["kind"] == "ops_metrics"
    assert payload["live_blocked"] is True
    assert payload["live_routing"] is False
    assert payload["counters"]["health.runs"] >= 1
    assert payload["live_gate_blocked"] >= 1
    assert payload["highlight_live_gate_blocked"] is True

    text = handle_get_ops_prometheus(state)
    assert "live_gate_blocked" in text
    assert "# TYPE" in text

    ids = {c["id"] for c in list_commands()["commands"]}
    assert "open.ops_metrics" in ids
    metrics.reset()


def check_f43_redteam() -> None:
    """F43: zip sandbox, create_server loopback gate, body 2MiB, LIVE reject."""

    from quantlab.core.exceptions import ValidationError
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import ApiError, WorkbenchState, handle_post_mode
    from quantlab.workbench.server import DEFAULT_MAX_BODY_BYTES, create_server
    from quantlab.workbench.session import WorkbenchSession, validate_session_id
    from quantlab.workbench.session_zip import resolve_upload_archive

    assert LIVE_BLOCKED is True
    assert DEFAULT_MAX_BODY_BYTES == 2_000_000

    try:
        validate_session_id("../evil")
        raise AssertionError("session_id traversal should raise")
    except ValidationError:
        pass

    try:
        create_server(host="0.0.0.0", port=0, allow_non_loopback=False)
        raise AssertionError("create_server unbound without flag should raise")
    except ValidationError:
        pass

    root = _smoke_tmp("quantlab-smoke-f43-rt")
    if root.exists():
        import shutil

        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    parent = root / "sessions"
    session = WorkbenchSession.create_or_load(parent, "smoke43")
    state = WorkbenchState(session=session)
    state.ensure_session()

    outside = root / "evil.zip"
    outside.write_bytes(b"PK\x05\x06" + b"\x00" * 18)
    try:
        resolve_upload_archive(
            zip_path=str(outside),
            zip_base64=None,
            work_dir=root / "w",
            allowed_roots=(parent.resolve(),),
        )
        raise AssertionError("zip_path outside sandbox should raise")
    except ValidationError:
        pass

    try:
        handle_post_mode(state, {"mode": "live"})
        raise AssertionError("LIVE mode should be rejected")
    except ApiError as exc:
        assert exc.status == 400


def check_f44_e2e_paper_workflow() -> None:
    """F44: flujo paper E2E vía handlers (sin browser) + LIVE reject."""
    import shutil
    from pathlib import Path

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import (
        ApiError,
        WorkbenchState,
        handle_get_health,
        handle_get_lab_reports,
        handle_get_paper_book,
        handle_get_positions,
        handle_get_session_export,
        handle_post_broker_connect,
        handle_post_lab_backtest,
        handle_post_lab_export_hb,
        handle_post_lab_montecarlo,
        handle_post_lab_optimize,
        handle_post_lab_validation_run,
        handle_post_mode,
        handle_post_paper_session_start,
        handle_post_paper_session_step,
        handle_post_paper_session_stop,
        handle_post_paper_submit,
    )
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True

    root = _smoke_tmp("quantlab-smoke-f44-e2e")
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root / "sessions", "smoke44")
    state = WorkbenchState(session=session)
    state.ensure_session()

    health = handle_get_health(state)
    assert health.get("ok") is True or health.get("live_blocked") is True
    assert health["live_blocked"] is True

    mode = handle_post_mode(state, {"mode": "paper"})
    assert mode["mode"] == "paper"

    connect = handle_post_broker_connect(state, {"venue": "binance", "mode": "tester"})
    assert connect["ok"] is True
    assert connect["paper_broker"] is True

    connect_a3 = handle_post_broker_connect(
        state, {"venue": "a3", "mode": "tester", "md_source": "fake"}
    )
    assert connect_a3["paper_broker"] is True

    # Reconnect binance for submit path
    handle_post_broker_connect(state, {"venue": "binance", "mode": "tester"})
    broker = state.broker
    assert broker is not None
    symbol = broker.list_instruments()[0].symbol

    submit = handle_post_paper_submit(
        state,
        {
            "intent_type": "place_order",
            "instrument_id": symbol,
            "side": "buy",
            "quantity": "1",
            "order_type": "market",
        },
    )
    assert submit["ack"]["status"] == "FILLED"

    positions = handle_get_positions(state)
    assert len(positions["positions"]) >= 1
    book = handle_get_paper_book(state)
    assert "cash" in book["book"]

    start = handle_post_paper_session_start(
        state,
        {"strategy_id": "buy_once", "symbol": symbol, "max_steps": 3},
    )
    assert start["ok"] is True
    step = handle_post_paper_session_step(state)
    assert step["step"] == 1
    handle_post_paper_session_stop(state)

    bt = handle_post_lab_backtest(
        state,
        {
            "strategy_id": "momentum",
            "n_bars": 16,
            "params": {"lookback": 2, "quantity": "1"},
            "experiment_id": "smoke44-bt",
        },
    )
    assert bt["ok"] is True
    reports = handle_get_lab_reports(state)
    assert reports.get("count", 0) >= 1 or len(reports.get("reports", [])) >= 1

    val = handle_post_lab_validation_run(state, {"n_bars": 40, "train_size": 10, "test_size": 5})
    assert val["ok"] is True
    opt = handle_post_lab_optimize(state, {"lookbacks": [2], "quantities": ["1"], "n_bars": 16})
    assert opt["ok"] is True
    mc = handle_post_lab_montecarlo(state, {"n_scenarios": 2, "n_bars": 12, "persist": True})
    assert mc["ok"] is True

    hb = handle_post_lab_export_hb(
        state, {"experiment_id": "smoke44-hb", "strategy_version": "demo"}
    )
    assert hb["ok"] is True

    exported = handle_get_session_export(state)
    assert exported["ok"] is True
    assert Path(str(exported["path"])).is_file()

    try:
        handle_post_mode(state, {"mode": "live"})
        raise AssertionError("LIVE mode should be rejected")
    except ApiError as exc:
        assert exc.status == 400
    assert LIVE_BLOCKED is True


def check_f45_about() -> None:
    """F45: GET /api/about + version badge UI assets + LIVE_BLOCKED."""

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY, build_about_payload
    from quantlab.workbench.api import WorkbenchState, handle_get_about
    from quantlab.workbench.commands import list_commands
    from quantlab.workbench.server import STATIC_ROOT
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = _smoke_tmp("quantlab-smoke-f45-about")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke45")
    state = WorkbenchState(session=session, bind_host="127.0.0.1", allow_non_loopback=False)
    state.ensure_session()

    about = handle_get_about(state)
    assert about["ok"] is True
    assert about["kind"] == "about"
    assert about["version"] == "0.91.0"
    assert about["live_blocked"] is True
    assert about["phases_summary"] == PHASES_SUMMARY
    assert about["python_version"]
    assert about["bind_policy"]["policy"] == "loopback-default"

    built = build_about_payload(bind_host="0.0.0.0", allow_non_loopback=True)
    assert built["bind_policy"]["policy"] == "allow-non-loopback"

    ids = {c["id"] for c in list_commands()["commands"]}
    assert "open.about" in ids

    assert (STATIC_ROOT / "js" / "about.js").is_file()
    html = (STATIC_ROOT / "index.html").read_text(encoding="utf-8")
    assert "about.js" in html
    assert 'data-open="about"' in html
    assert "sb-version" in html
    shell = (STATIC_ROOT / "js" / "shell.js").read_text(encoding="utf-8")
    assert "openAbout" in shell
    assert "refreshVersionBadge" in shell


def check_f46_sessions() -> None:
    """F46: multi-session list/switch/new + UI + LIVE_BLOCKED."""
    import tempfile
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import (
        ApiError,
        WorkbenchState,
        handle_get_sessions,
        handle_post_sessions_new,
        handle_post_sessions_switch,
    )
    from quantlab.workbench.commands import list_commands
    from quantlab.workbench.server import STATIC_ROOT
    from quantlab.workbench.session import WorkbenchSession, list_sessions

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = Path(tempfile.mkdtemp(prefix="quantlab-smoke-f46-"))
    parent = root / "sessions"
    parent.mkdir(parents=True, exist_ok=True)
    s1 = WorkbenchSession.create_or_load(parent, "smoke46a")
    WorkbenchSession.create_or_load(parent, "smoke46b")
    state = WorkbenchState(session=s1, session_parent=parent)
    state.ensure_session()

    listed = handle_get_sessions(state)
    assert listed["ok"] is True
    assert listed["kind"] == "sessions"
    assert listed["count"] >= 2
    assert listed["session_id"] == "smoke46a"
    assert listed["live_blocked"] is True

    ids = {i["session_id"] for i in list_sessions(parent)}
    assert "smoke46a" in ids and "smoke46b" in ids

    switched = handle_post_sessions_switch(state, {"session_id": "smoke46b"})
    assert switched["ok"] is True
    assert switched["session_id"] == "smoke46b"

    created = handle_post_sessions_new(state, {"session_id": "smoke46c"})
    assert created["ok"] is True
    assert created["session_id"] == "smoke46c"

    try:
        handle_post_sessions_switch(state, {"session_id": "../evil"})
        raise AssertionError("path traversal should fail")
    except ApiError as exc:
        assert exc.status == 400

    cmd_ids = {c["id"] for c in list_commands()["commands"]}
    assert "open.sessions" in cmd_ids

    assert (STATIC_ROOT / "js" / "panes" / "sessions.js").is_file()
    html = (STATIC_ROOT / "index.html").read_text(encoding="utf-8")
    assert "sessions.js" in html
    assert 'data-open="sessions"' in html
    shell = (STATIC_ROOT / "js" / "shell.js").read_text(encoding="utf-8")
    assert "openSessions" in shell
    api = (STATIC_ROOT / "js" / "api.js").read_text(encoding="utf-8")
    assert "sessionsList" in api
    assert "/api/sessions/switch" in api


def check_f48_themes() -> None:
    """F48: theme CSS tokens + settings theme roundtrip + data-theme JS."""
    import tempfile
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import WorkbenchState, handle_get_settings, handle_put_settings
    from quantlab.workbench.server import STATIC_ROOT
    from quantlab.workbench.session import WorkbenchSession
    from quantlab.workbench.settings import load_settings

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    css = (STATIC_ROOT / "css" / "workbench.css").read_text(encoding="utf-8")
    for token in (
        "--bg-banner",
        "--bg-status",
        "--bg-taskbar",
        "--bg-desktop-a",
        "--amber-soft",
        "--shadow-modal",
        'html[data-theme="high-contrast"]',
        'html[data-theme="slate"]',
    ):
        assert token in css, token

    html = (STATIC_ROOT / "index.html").read_text(encoding="utf-8")
    assert 'data-theme="slate"' in html

    shell = (STATIC_ROOT / "js" / "shell.js").read_text(encoding="utf-8")
    assert 'document.documentElement.setAttribute("data-theme"' in shell
    settings_js = (STATIC_ROOT / "js" / "panes" / "settings.js").read_text(encoding="utf-8")
    assert 'document.documentElement.setAttribute("data-theme"' in settings_js

    root = Path(tempfile.mkdtemp(prefix="quantlab-smoke-f48-"))
    session = WorkbenchSession.create_or_load(root, "smoke48")
    state = WorkbenchState(session=session)
    state.ensure_session()

    got = handle_get_settings(state)
    assert got["ok"] is True
    assert got["settings"]["theme"] == "slate"

    put = handle_put_settings(state, {"theme": "high-contrast", "locale": "es"})
    assert put["ok"] is True
    assert put["settings"]["theme"] == "high-contrast"
    assert put["live_blocked"] is True
    assert load_settings(session.settings_path)["theme"] == "high-contrast"

    put2 = handle_put_settings(state, {"theme": "slate"})
    assert put2["settings"]["theme"] == "slate"
    assert load_settings(session.settings_path)["theme"] == "slate"


def check_f50_perf_baseline() -> None:
    """F50: workbench API latency baseline p95/max < 500ms (loopback)."""
    import tempfile
    import threading
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import WorkbenchState
    from quantlab.workbench.perf_baseline import (
        DEFAULT_MAX_THRESHOLD_MS,
        DEFAULT_P95_THRESHOLD_MS,
        PERF_ENDPOINTS,
        assert_baseline_within_budget,
        run_perf_baseline,
    )
    from quantlab.workbench.server import create_server
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = Path(tempfile.mkdtemp(prefix="quantlab-smoke-f50-"))
    session = WorkbenchSession.create_or_load(root, "smoke50")
    state = WorkbenchState(session=session)
    state.ensure_session()
    server = create_server(host="127.0.0.1", port=0, state=state)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        report = run_perf_baseline(
            server,
            endpoints=PERF_ENDPOINTS,
            samples=15,
            warmup=2,
            p95_threshold_ms=DEFAULT_P95_THRESHOLD_MS,
            max_threshold_ms=DEFAULT_MAX_THRESHOLD_MS,
            version=__version__,
            live_blocked=True,
        )
        assert_baseline_within_budget(report)
        assert len(report.endpoints) == 5
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)


def check_f51_rate_limit() -> None:
    """F51: soft rate limit in-process; 429 JSON con límite bajo inyectado."""
    import http.client
    import json
    import tempfile
    import threading
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import WorkbenchState
    from quantlab.workbench.rate_limit import (
        DEFAULT_RATE_LIMIT_RPS,
        RateLimitConfig,
    )
    from quantlab.workbench.server import create_server
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"
    assert DEFAULT_RATE_LIMIT_RPS >= 120.0

    root = Path(tempfile.mkdtemp(prefix="quantlab-smoke-f51-"))
    session = WorkbenchSession.create_or_load(root, "smoke51")
    state = WorkbenchState(session=session)
    state.ensure_session()
    state.configure_rate_limit(
        RateLimitConfig(enabled=True, requests_per_second=2.0, burst=2.0)
    )
    server = create_server(host="127.0.0.1", port=0, state=state)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        assert isinstance(host, str)
        assert isinstance(port, int)
        statuses: list[int] = []
        for _ in range(4):
            conn = http.client.HTTPConnection(host, port, timeout=5.0)
            try:
                conn.request("GET", "/api/mode")
                resp = conn.getresponse()
                raw = resp.read()
                statuses.append(resp.status)
                if resp.status == 429:
                    body = json.loads(raw.decode("utf-8"))
                    assert body["ok"] is False
                    assert body["code"] == "rate_limit_exceeded"
                    assert resp.getheader("Retry-After") is not None
            finally:
                conn.close()
        assert statuses.count(200) == 2
        assert statuses.count(429) >= 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)



def check_f52_shutdown() -> None:
    """F52: graceful shutdown stops paper session; /api/shutdown loopback-only."""
    import tempfile
    from datetime import UTC, datetime
    from decimal import Decimal
    from pathlib import Path

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
    from quantlab.workbench.paper_session import PaperSessionConfig, PaperSessionRunner
    from quantlab.workbench.risk import PaperRiskLimits
    from quantlab.workbench.session import WorkbenchSession
    from quantlab.workbench.shutdown import perform_graceful_shutdown

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    class _Md:
        symbol = "TEST"

        @property
        def venue_id(self) -> str:
            return "md"

        def connect(self) -> dict[str, object]:
            return {"ok": True}

        def close(self) -> dict[str, object]:
            return {"ok": True}

        def health(self) -> dict[str, object]:
            return {"ok": True}

        def list_instruments(self) -> list[BrokerInstrument]:
            return [
                BrokerInstrument(
                    symbol="TEST",
                    description="t",
                    currency="USD",
                    status="ACTIVE",
                )
            ]

        def get_snapshot(self, symbol: str) -> BrokerSnapshot:
            return BrokerSnapshot(
                symbol=symbol,
                bid=Decimal("99"),
                ask=Decimal("101"),
                last=Decimal("100"),
                ts=datetime(2024, 1, 1, tzinfo=UTC),
            )

        def get_account(self) -> BrokerAccount:
            return BrokerAccount(cash=Decimal("1"), currency="USD")

        def get_positions(self) -> list[BrokerPosition]:
            return []

        def submit(self, intent: OrderIntent) -> BrokerAck:
            raise AssertionError("no md submit")

        def cancel(self, order_id: str) -> BrokerAck:
            raise AssertionError("no md cancel")

    root = Path(tempfile.mkdtemp(prefix="quantlab-smoke-f52-"))
    session = WorkbenchSession.create_or_load(root, "smoke52")
    state = WorkbenchState(session=session, slippage_bps=Decimal("3"))
    state.ensure_session()
    book = PaperBook(initial_cash=Decimal("10000"))
    broker = PaperBroker(_Md(), book=book)  # type: ignore[arg-type]
    state.broker = broker
    state.book = book
    runner = PaperSessionRunner(broker, PaperRiskLimits(), book)
    runner.start(PaperSessionConfig(strategy_id="buy_once", symbol="TEST", max_steps=10))
    state.paper_session = runner
    assert runner.status()["running"] is True

    try:
        handle_post_shutdown(state, client_ip="8.8.8.8", stop_server=False)
        raise AssertionError("expected 403 for non-loopback")
    except ApiError as exc:
        assert exc.status == 403

    result = perform_graceful_shutdown(state, reason="smoke-f52", stop_server=False)
    assert result["ok"] is True
    assert result["paper"]["stopped"] is True
    assert state.paper_session is None
    assert state.shutdown_requested is True
    assert session.settings_path.is_file()


def check_f53_dockerfile() -> None:
    """F53: Dockerfile.workbench CMD allow-non-loopback / no-browser (parse file)."""
    import re
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = Path(__file__).resolve().parents[1]
    dockerfile = root / "Dockerfile.workbench"
    dockerignore = root / ".dockerignore"
    ops = root / "docs" / "ops" / "DOCKER_WORKBENCH.md"
    assert dockerfile.is_file()
    assert dockerignore.is_file()
    assert ops.is_file()

    text = dockerfile.read_text(encoding="utf-8")
    assert "FROM python:3.12-slim" in text
    assert "uv sync" in text
    assert "EXPOSE 8765" in text
    match = re.search(r"^CMD\s+\[(.+)\]\s*$", text, flags=re.MULTILINE)
    assert match is not None
    tokens = [tok.strip().strip('"').strip("'") for tok in match.group(1).split(",")]
    assert "quantlab-workbench" in tokens
    assert "--allow-non-loopback" in tokens
    assert "--no-browser" in tokens
    assert "0.0.0.0" in tokens
    assert "127.0.0.1:8765:8765" in ops.read_text(encoding="utf-8")
    di = dockerignore.read_text(encoding="utf-8")
    assert ".env" in di
    assert "data/" in di or "data" in di


def check_f54_probes() -> None:
    """F54: /api/livez always alive; /api/readyz LIVE_BLOCKED + writable."""
    import tempfile
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import WorkbenchState, handle_get_livez, handle_get_readyz
    from quantlab.workbench.probes import readyz_payload
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = Path(tempfile.mkdtemp(prefix="quantlab-smoke-f54-"))
    session = WorkbenchSession.create_or_load(root, "smoke54")
    state = WorkbenchState(session=session)
    state.ensure_session()

    live = handle_get_livez(state)
    assert live["ok"] is True
    assert live["alive"] is True
    assert live["status"] == "alive"

    ready = handle_get_readyz(state)
    assert ready["ready"] is True
    assert ready["checks"]["live_blocked"] is True
    assert ready["checks"]["session_root_writable"] is True

    not_ready = readyz_payload(session_root=session.root, live_blocked=False)
    assert not_ready["ready"] is False
    assert not_ready["status"] == "not_ready"

    ops = Path(__file__).resolve().parents[1] / "docs" / "ops" / "DOCKER_WORKBENCH.md"
    ops_text = ops.read_text(encoding="utf-8")
    assert "/api/livez" in ops_text
    assert "/api/readyz" in ops_text


def check_f55_openapi() -> None:
    """F55: OpenAPI catalog has health/livez; no LIVE trading routes."""
    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api_catalog import (
        OPENAPI_PATH,
        assert_no_live_trading_routes,
        build_openapi_schema,
        catalog_routes,
    )

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    routes = catalog_routes()
    paths = {(r.method, r.path) for r in routes}
    assert ("GET", "/api/health") in paths
    assert ("GET", "/api/livez") in paths
    assert ("GET", OPENAPI_PATH) in paths

    schema = build_openapi_schema()
    assert schema["openapi"].startswith("3.")
    assert "/api/health" in schema["paths"]
    assert "/api/livez" in schema["paths"]
    for path in schema["paths"]:
        assert path != "/api/live"
        assert not path.startswith("/api/live/")
    assert_no_live_trading_routes()
    assert schema["x-quantlab"]["live_blocked"] is True
    assert schema["x-quantlab"]["phases_summary"] == PHASES_SUMMARY


def check_f56_security_headers() -> None:
    """F56: security headers + CORS fail-closed (no ACAO *)."""
    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.security_headers import (
        SECURITY_HEADERS,
        cors_allow_origin,
        security_header_items,
        wants_api_no_store,
    )

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"
    assert SECURITY_HEADERS["X-Content-Type-Options"] == "nosniff"
    assert SECURITY_HEADERS["X-Frame-Options"] == "DENY"
    assert SECURITY_HEADERS["Referrer-Policy"] == "no-referrer"
    assert wants_api_no_store("/api/health") is True
    assert cors_allow_origin("*") is None
    assert cors_allow_origin("https://evil.example") is None
    assert cors_allow_origin("http://127.0.0.1:8765") == "http://127.0.0.1:8765"
    items = dict(security_header_items(path="/api/about", origin="https://evil.example"))
    assert items["Cache-Control"] == "no-store"
    assert "Access-Control-Allow-Origin" not in items


def check_f57_csp() -> None:
    """F57: Content-Security-Policy restrictiva (sin unsafe-eval)."""
    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.security_headers import (
        CONTENT_SECURITY_POLICY,
        SECURITY_HEADERS,
        security_header_items,
    )

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"
    csp = CONTENT_SECURITY_POLICY
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "style-src 'self' 'unsafe-inline'" in csp
    assert "connect-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "unsafe-eval" not in csp
    assert SECURITY_HEADERS["Content-Security-Policy"] == csp
    items = dict(security_header_items(path="/", origin=None))
    assert items["Content-Security-Policy"] == csp


def check_f88_paper_reconciliation() -> None:
    """F88: journal autoritativo, book v2 y rebuild sólo CLI."""
    import json
    import tempfile
    from datetime import UTC, datetime
    from decimal import Decimal
    from pathlib import Path

    from quantlab import __version__
    from quantlab.brokers.paper.journal import PaperFillJournal
    from quantlab.brokers.paper.reconciliation import rebuild_book, reconcile_book
    from quantlab.brokers.types import PaperFill
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"
    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_88_APPROVED.md").exists()
    assert (root / "scripts" / "reconcile_paper_session.py").is_file()

    with tempfile.TemporaryDirectory(prefix="quantlab-f88-") as temp:
        session = WorkbenchSession.create_or_load(Path(temp), "smoke88")
        journal = PaperFillJournal(session.journal_path)
        fill = PaperFill(
            fill_id="smoke-f88",
            order_id="smoke-order-f88",
            symbol="TEST",
            side="buy",
            quantity=Decimal("1"),
            price=Decimal("10"),
            ts=datetime.now(tz=UTC),
            source="paper_broker",
        )
        journal.append(fill)
        book = rebuild_book(Decimal("100000"), "USD", False, journal.read_strict())
        session.save_book(book, journal.checkpoint())
        assert reconcile_book(book, journal).ok is True
        envelope = json.loads(session.book_path.read_text(encoding="utf-8"))
        assert envelope["schema_version"] == 2
        assert envelope["journal_checkpoint"]["record_count"] == 1


def check_f89_a3_md_certification() -> None:
    """F89: lane fake PASS; sandbox opt-in/strict y cero writes."""
    from pathlib import Path

    from quantlab import __version__
    from quantlab.brokers.a3.read_contract import (
        A3ReadContractStatus,
        run_fake_read_contract,
    )
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"
    report = run_fake_read_contract()
    assert report.status is A3ReadContractStatus.PASS
    assert report.write_calls == 0
    assert report.live_blocked is True
    root = Path(__file__).resolve().parents[1]
    assert (root / "scripts" / "a3_md_certify.py").is_file()
    assert (root / "docs" / "ops" / "A3_MD_CERTIFICATION.md").is_file()
    assert not (root / "docs" / "audit" / "FASE_89_APPROVED.md").exists()


def check_f90_reconciliation_ui() -> None:
    """F90: panel Reconciliación read-only cableado a GET /api/paper/reconciliation."""
    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.commands import list_commands

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    root = Path(__file__).resolve().parents[1]
    static = root / "src" / "quantlab" / "workbench" / "static"
    pane_js = (static / "js" / "panes" / "reconciliation.js").read_text(encoding="utf-8")
    assert "createReconciliationPane" in pane_js
    assert "QLApi.paperReconciliation" in pane_js
    # La UI nunca reconstruye archivos: solo GET + rehydrate (F91, relee disco).
    allowed = pane_js.count("QLApi.paperReconciliation") + pane_js.count("QLApi.paperRehydrate")
    assert pane_js.count("QLApi.") == allowed
    assert "rebuild_via" in pane_js
    api_js = (static / "js" / "api.js").read_text(encoding="utf-8")
    assert "/api/paper/reconciliation" in api_js
    shell_js = (static / "js" / "shell.js").read_text(encoding="utf-8")
    assert "reconciliation: openReconciliation" in shell_js
    index_html = (static / "index.html").read_text(encoding="utf-8")
    assert 'data-open="reconciliation"' in index_html
    assert "panes/reconciliation.js" in index_html
    for locale in ("es", "en"):
        messages = (static / "i18n" / f"{locale}.json").read_text(encoding="utf-8")
        assert '"pane.reconciliation"' in messages

    ids = {c["id"] for c in list_commands()["commands"]}
    assert "open.reconciliation" in ids
    assert not (root / "docs" / "audit" / "FASE_90_APPROVED.md").exists()


def check_f91_paper_rehydrate() -> None:
    """F91: rehydrate post-rebuild — nunca reconstruye; POST-only; UI con confirm."""
    import tempfile

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import WorkbenchState, handle_post_paper_rehydrate
    from quantlab.workbench.api_catalog import build_openapi_schema
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"

    route = build_openapi_schema()["paths"]["/api/paper/reconciliation/rehydrate"]
    assert "post" in route and "get" not in route

    with tempfile.TemporaryDirectory(prefix="ql-f91-") as tmp:
        parent = Path(tmp)
        session = WorkbenchSession.create_or_load(parent, "smoke91")
        state = WorkbenchState(session=session, session_parent=parent)
        state.ensure_session()
        journal_before = session.journal_path.read_bytes()
        payload = handle_post_paper_rehydrate(state)
        assert payload["rehydrated"] is True
        assert payload["ok"] is True
        assert payload["broker_connected"] is False
        assert session.journal_path.read_bytes() == journal_before

    root = Path(__file__).resolve().parents[1]
    static = root / "src" / "quantlab" / "workbench" / "static"
    pane_js = (static / "js" / "panes" / "reconciliation.js").read_text(encoding="utf-8")
    assert "QLApi.paperRehydrate" in pane_js
    assert "confirm(" in pane_js
    assert not (root / "docs" / "audit" / "FASE_91_APPROVED.md").exists()


def check_f92_milestone_v080_arc() -> None:
    """F92: freeze documental arco v0.71–v0.83 + CHANGELOG sync."""
    from quantlab.execution.live_gate import LIVE_BLOCKED

    assert LIVE_BLOCKED is True

    root = Path(__file__).resolve().parents[1]
    freeze = (root / "docs" / "audit" / "MILESTONE_V080_ARC_FREEZE.md").read_text(
        encoding="utf-8"
    )
    assert "F79–F91" in freeze
    assert "LIVE_BLOCKED=True" in freeze
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    for version in ("0.81.0", "0.82.0", "0.83.0", "0.84.0"):
        assert f"## [{version}]" in changelog, version
    assert not (root / "docs" / "audit" / "FASE_92_APPROVED.md").exists()


def check_f93_venues_panel() -> None:
    """F93: Venues / Broker Registry panel read-only."""
    from quantlab.brokers.contracts.v1 import BROKER_PLUGIN_API_VERSION
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import WorkbenchState, handle_get_venues
    from quantlab.workbench.commands import list_commands
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True

    tmp = Path(_smoke_tmp("quantlab-smoke-f93-"))
    session = WorkbenchSession.create_or_load(tmp, "smoke-f93")
    state = WorkbenchState(session=session, session_parent=tmp)
    payload = handle_get_venues(state)
    assert "paper" in payload["venues"]
    assert payload["live_blocked"] is True
    assert payload["plugin_contract"]["api_version"] == BROKER_PLUGIN_API_VERSION
    assert payload["plugin_contract"]["execution"] == "blocked"

    ids = {c["id"] for c in list_commands()["commands"]}
    assert "open.venues" in ids

    root = Path(__file__).resolve().parents[1]
    static = root / "src" / "quantlab" / "workbench" / "static"
    assert (static / "js" / "panes" / "venues.js").is_file()
    assert 'data-open="venues"' in (static / "index.html").read_text(encoding="utf-8")
    assert not (root / "docs" / "audit" / "FASE_93_APPROVED.md").exists()


def check_f94_api_explorer() -> None:
    """F94: API Explorer panel read-only sobre el catálogo OpenAPI."""
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import openapi_payload
    from quantlab.workbench.commands import list_commands

    assert LIVE_BLOCKED is True

    doc = openapi_payload()
    assert isinstance(doc.get("paths"), dict) and doc["paths"]

    ids = {c["id"] for c in list_commands()["commands"]}
    assert "open.api_explorer" in ids

    root = Path(__file__).resolve().parents[1]
    static = root / "src" / "quantlab" / "workbench" / "static"
    assert (static / "js" / "panes" / "api_explorer.js").is_file()
    assert 'data-open="api_explorer"' in (static / "index.html").read_text(encoding="utf-8")
    assert not (root / "docs" / "audit" / "FASE_94_APPROVED.md").exists()


def check_f95_diagnostics() -> None:
    """F95: Diagnostics snapshot read-only agregado."""
    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import WorkbenchState, handle_get_diagnostics
    from quantlab.workbench.commands import list_commands
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True

    tmp = Path(_smoke_tmp("quantlab-smoke-f95-"))
    session = WorkbenchSession.create_or_load(tmp, "smoke-f95")
    state = WorkbenchState(session=session, session_parent=tmp)
    payload = handle_get_diagnostics(state)
    assert payload["ok"] is True
    assert payload["live_blocked"] is True
    assert payload["live_routing"] is False
    assert payload["version"] == __version__
    assert set(payload["health"]) == {"status", "checks_ok", "checks_total"}

    ids = {c["id"] for c in list_commands()["commands"]}
    assert "open.diagnostics" in ids

    root = Path(__file__).resolve().parents[1]
    static = root / "src" / "quantlab" / "workbench" / "static"
    assert (static / "js" / "panes" / "diagnostics.js").is_file()
    assert 'data-open="diagnostics"' in (static / "index.html").read_text(encoding="utf-8")
    assert not (root / "docs" / "audit" / "FASE_95_APPROVED.md").exists()


def check_f96_diagnostics_download() -> None:
    """F96: descarga del snapshot de diagnóstico como archivo JSON."""
    import json as _json

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import WorkbenchState, handle_get_diagnostics_download
    from quantlab.workbench.api_catalog import API_ROUTES
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert ("/api/diagnostics.json", "GET") in {(r.path, r.method) for r in API_ROUTES}

    tmp = Path(_smoke_tmp("quantlab-smoke-f96-"))
    session = WorkbenchSession.create_or_load(tmp, "smoke-f96")
    state = WorkbenchState(session=session, session_parent=tmp)
    body, filename = handle_get_diagnostics_download(state)
    assert filename.startswith("quantlab-diagnostics-") and filename.endswith(".json")
    payload = _json.loads(body.decode("utf-8"))
    assert payload["kind"] == "diagnostics"
    assert payload["live_blocked"] is True

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_96_APPROVED.md").exists()



def check_f97_support_bundle() -> None:
    """F97: support bundle ZIP read-only."""
    import io
    import json as _json
    import zipfile

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import WorkbenchState, handle_get_support_bundle
    from quantlab.workbench.api_catalog import API_ROUTES
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert ("/api/support-bundle.zip", "GET") in {(r.path, r.method) for r in API_ROUTES}

    tmp = Path(_smoke_tmp("quantlab-smoke-f97-"))
    session = WorkbenchSession.create_or_load(tmp, "smoke-f97")
    state = WorkbenchState(session=session, session_parent=tmp)
    body, filename = handle_get_support_bundle(state)
    assert filename.startswith("quantlab-support-") and filename.endswith(".zip")
    with zipfile.ZipFile(io.BytesIO(body), "r") as zf:
        names = set(zf.namelist())
        assert "diagnostics.json" in names
        assert "about.json" in names
        diag = _json.loads(zf.read("diagnostics.json"))
        assert diag["live_blocked"] is True

    root = Path(__file__).resolve().parents[1]
    assert not (root / "docs" / "audit" / "FASE_97_APPROVED.md").exists()



def check_f98_milestone_v090() -> None:
    """F98: freeze documental arco ops F93–F97 + CHANGELOG tip."""
    from quantlab.execution.live_gate import LIVE_BLOCKED

    assert LIVE_BLOCKED is True

    root = Path(__file__).resolve().parents[1]
    freeze = (root / "docs" / "audit" / "MILESTONE_V090_OPS_ARC_FREEZE.md").read_text(encoding="utf-8")
    assert "F93–F97" in freeze or "F93-F97" in freeze
    assert "LIVE_BLOCKED=True" in freeze
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    for version in ("0.89.0", "0.91.0"):
        assert f"## [{version}]" in changelog, version
    assert not (root / "docs" / "audit" / "FASE_98_APPROVED.md").exists()



def check_f99_guided_lab() -> None:
    """F99: Guided Lab wizard pane paper-only."""
    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.commands import list_commands

    assert LIVE_BLOCKED is True
    assert __version__ == "0.91.0"
    assert PHASES_SUMMARY == "F19–F99 INTERNAL"
    ids = {c["id"] for c in list_commands()["commands"]}
    assert "open.guided_lab" in ids
    root = Path(__file__).resolve().parents[1]
    static = root / "src" / "quantlab" / "workbench" / "static"
    assert (static / "js" / "panes" / "guided_lab.js").is_file()
    assert 'data-open="guided_lab"' in (static / "index.html").read_text(encoding="utf-8")
    assert not (root / "docs" / "audit" / "FASE_99_APPROVED.md").exists()


def main() -> int:
    checks: list[tuple[str, Callable[[], None]]] = [
        ("LIVE_BLOCKED is True", check_live_blocked),
        ("assert_live_routing_blocked raises", check_live_gate_raises),
        ("brokers imports + REAL=PAPER", check_brokers_imports),
        ("workbench imports", check_workbench_imports),
        ("chat allowlist + FakeProvider", check_chat_safe),
        ("quantlab-health live_blocked", check_health_dict),
        ("about version matches __version__", check_about_version_matches),
        ("version starts with 0.84", check_version_starts_with_084),
        ("paper book + session_id fail-closed", check_paper_book_session),
        ("F23 paper book import", check_f23_book_import),
        ("F24 plugins + generics", check_f24_plugins),
        ("F25 launch --allow-non-loopback", check_f25_launch_parser),
        ("F25 ops desk slip/charset/risk", check_f25_ops_desk_invariants),
        ("F26 paper session runner", check_f26_paper_session),
        ("F27 strategy catalog", check_f27_strategy_catalog),
        ("F28 layout + journal API", check_f28_layout_journal),
        ("F29 reports + metrics history", check_f29_reports),
        ("F30 universe watchlist + catalog", check_f30_universe_catalog),
        ("F31 features store + pipeline", check_f31_features_store),
        ("F32 validation walk-forward runner", check_f32_validation_runner),
        ("F33 optimizer history + pareto", check_f33_optimizer_history),
        ("F34 montecarlo history + HB export", check_f34_mc_export),
        ("F35 command palette + /api/commands", check_f35_commands),
        ("F36 settings + status bar", check_f36_settings),
        ("F37 first-run onboarding wizard", check_f37_onboarding),
        ("F38 docs / help browser", check_f38_docs_help),
        ("F39 session export/import ZIP", check_f39_session_zip),
        ("F40 workspace presets", check_f40_workspace_presets),
        ("F41 activity log + toasts API", check_f41_activity_log),
        ("F42 ops metrics panel API", check_f42_ops_metrics),
        ("F43 red-team workbench hardening", check_f43_redteam),
        ("F44 e2e paper workflow integration", check_f44_e2e_paper_workflow),
        ("F45 about dialog + version badge", check_f45_about),
        ("F46 multi-session switcher", check_f46_sessions),
        ("F47 chat context awareness", check_f47_chat_context),
        ("F48 theme CSS slate + high-contrast", check_f48_themes),
        ("F50 workbench API perf baseline", check_f50_perf_baseline),
        ("F51 soft API rate limit", check_f51_rate_limit),
        ("F52 graceful shutdown paper safety", check_f52_shutdown),
        ("F53 Dockerfile workbench opt-in", check_f53_dockerfile),
        ("F54 readiness / liveness probes", check_f54_probes),
        ("F55 OpenAPI / API catalog", check_f55_openapi),
        ("F56 security headers + CORS", check_f56_security_headers),
        ("F57 Content-Security-Policy", check_f57_csp),
        ("F59 a11y basics focus+aria", check_f59_a11y),
        ("F60 i18n scaffold es+en", check_f60_i18n),
        ("F61 access log request jsonl", check_f61_access_log),
        ("F62 access log panel UI", check_f62_access_log_ui),
        ("F63 session auto-backup", check_f63_auto_backup),
        ("F64 backups panel UI", check_f64_backups_ui),
        ("F65 blotter fills CSV export", check_f65_fills_csv),
        ("F66 equity curve snapshot", check_f66_equity_curve),
        ("F67 paper PnL summary", check_f67_paper_pnl),
        ("F69 risk utilization report", check_f69_risk_utilization),
        ("F70 paper kill switch", check_f70_paper_kill),
        ("F71 health extended + 1k tests", check_f71_health_extended),
        ("F72 desktop notifications hook", check_f72_desktop_notifications),
        ("F73 optional sound alerts", check_f73_sound_alerts),
        ("F74 status bar clock timezone", check_f74_clock_timezone),
        ("F75 broker heartbeat status", check_f75_broker_heartbeat),
        ("F76 broker reconnect button", check_f76_broker_reconnect),
        ("F77 broker disconnect button", check_f77_broker_disconnect),
        ("F79 watchlist import/export JSON", check_f79_watchlist_io),
        ("F80 custom preset save", check_f80_custom_presets),
        ("F81 custom preset delete", check_f81_preset_delete),
        ("F82 window snap to edges", check_f82_window_snap),
        ("F83 minimize / restore all", check_f83_minimize_all),
        ("F84 cascade / tile windows", check_f84_cascade_tile),
        ("F85 bring to front / send to back", check_f85_zorder),
        ("F86 maximize / restore window", check_f86_maximize),
        ("F87 broker plugin contract v1", check_f87_broker_plugin_contract),
        ("F88 paper journal reconciliation", check_f88_paper_reconciliation),
        ("F89 A3 MD read-only certification", check_f89_a3_md_certification),
        ("F90 reconciliation panel UI", check_f90_reconciliation_ui),
        ("F91 paper session rehydrate", check_f91_paper_rehydrate),
        ("F92 milestone freeze arco v0.80", check_f92_milestone_v080_arc),
        ("F93 venues / broker registry panel", check_f93_venues_panel),
        ("F94 api explorer panel", check_f94_api_explorer),
        ("F95 diagnostics snapshot", check_f95_diagnostics),
        ("F96 diagnostics download", check_f96_diagnostics_download),
        ("F97 support bundle ZIP", check_f97_support_bundle),
        ("F98 milestone freeze arco ops v0.90", check_f98_milestone_v090),
        ("F99 guided lab wizard", check_f99_guided_lab),
    ]
    ok = True
    for name, fn in checks:
        ok = _check(name, fn) and ok
    print("—" * 40)
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
