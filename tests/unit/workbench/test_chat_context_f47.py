"""Chat context awareness — tools allowlist F47 (read-only)."""

from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.brokers.paper.book import PaperBook
from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.activity import ActivityLog
from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.chat.providers import FakeProvider
from quantlab.workbench.chat.tools import ALLOWED_TOOLS, FORBIDDEN_TOOLS, ToolRegistry
from quantlab.workbench.session import WorkbenchSession
from quantlab.workbench.strategy_catalog import CANONICAL_STRATEGY_IDS


@pytest.fixture
def registry(tmp_path: Path) -> ToolRegistry:
    session = WorkbenchSession.create_or_load(tmp_path, "chat47")
    state = WorkbenchState(session=session)
    state.ensure_session()
    return ToolRegistry(state)


def test_live_blocked_still_true() -> None:
    assert LIVE_BLOCKED is True


def test_phases_summary_f47() -> None:
    assert PHASES_SUMMARY == "F19–F72 INTERNAL"


def test_new_tools_in_allowlist() -> None:
    assert "get_session_summary" in ALLOWED_TOOLS
    assert "list_reports" in ALLOWED_TOOLS
    assert "list_strategies" in ALLOWED_TOOLS
    assert ALLOWED_TOOLS.isdisjoint(FORBIDDEN_TOOLS)
    for bad in ("submit_order", "place_order", "set_live", "flip_live_blocked"):
        assert bad not in ALLOWED_TOOLS


def test_illegal_tools_still_rejected(registry: ToolRegistry) -> None:
    illegal = sorted(FORBIDDEN_TOOLS) + [
        "drop_database",
        "execute_trade",
        "paper_submit",
        "enable_live",
    ]
    for name in illegal:
        with pytest.raises(ValidationError, match="tool rechazada"):
            registry.call(name)


def test_get_session_summary(registry: ToolRegistry) -> None:
    state = registry._state  # noqa: SLF001 — fixture owned
    state.venue = "binance"
    book = state.ensure_book()
    assert isinstance(book, PaperBook)
    ActivityLog(state.ensure_session().activity_path).append(
        "connect", ok=True, message="smoke", op="connect"
    )

    out = registry.call("get_session_summary", {"limit": 5})
    assert out["ok"] is True
    assert out["kind"] == "session_summary"
    assert out["mode"] in {"tester", "paper"}
    assert out["venue"] == "binance"
    assert out["book_equity"]
    assert out["positions_count"] == 0
    assert out["activity_limit"] == 5
    assert out["activity_count"] >= 1
    assert out["live_blocked"] is True
    assert out["live_routing"] is False
    assert out["chat_mutations"] is False


def test_list_reports_empty(registry: ToolRegistry) -> None:
    out = registry.call("list_reports")
    assert out["ok"] is True
    assert out["kind"] == "reports"
    assert out["count"] == 0
    assert out["reports"] == []
    assert out["live_blocked"] is True
    assert out["live_routing"] is False


def test_list_strategies_from_catalog(registry: ToolRegistry) -> None:
    out = registry.call("list_strategies")
    assert out["ok"] is True
    assert out["kind"] == "strategies"
    assert out["count"] == len(CANONICAL_STRATEGY_IDS)
    ids = {s["id"] for s in out["strategies"]}
    assert ids == set(CANONICAL_STRATEGY_IDS)
    assert out["live_blocked"] is True
    assert out["chat_mutations"] is False


def test_fake_provider_como_estoy(registry: ToolRegistry) -> None:
    turn = FakeProvider().complete("¿cómo estoy?", registry)
    assert "get_session_summary" in turn.tools_used
    assert "equity=" in turn.reply or "Resumen" in turn.reply


def test_fake_provider_resumen_sesion(registry: ToolRegistry) -> None:
    turn = FakeProvider().complete("resumen sesión", registry)
    assert "get_session_summary" in turn.tools_used


def test_fake_provider_reportes(registry: ToolRegistry) -> None:
    turn = FakeProvider().complete("qué reportes hay", registry)
    assert "list_reports" in turn.tools_used
    assert "Reportes" in turn.reply or "reportes" in turn.reply.lower()


def test_fake_provider_estrategias(registry: ToolRegistry) -> None:
    turn = FakeProvider().complete("estrategias", registry)
    assert "list_strategies" in turn.tools_used
    assert "momentum" in turn.reply.lower() or "Estrategias" in turn.reply


def test_allowed_tools_still_execute(registry: ToolRegistry) -> None:
    for name in sorted(ALLOWED_TOOLS):
        if name == "search_docs":
            out = registry.call(name, {"query": "workbench LIVE"})
        elif name == "get_session_summary":
            out = registry.call(name, {"limit": 3})
        else:
            out = registry.call(name)
        assert isinstance(out, dict)
