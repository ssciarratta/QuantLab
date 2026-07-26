"""Tests chat allowlist / rechazo de tools ilegales (Fase 22)."""

from __future__ import annotations

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.chat.tools import ALLOWED_TOOLS, FORBIDDEN_TOOLS, ToolRegistry


@pytest.fixture
def registry() -> ToolRegistry:
    return ToolRegistry(WorkbenchState())


def test_allowlist_only(registry: ToolRegistry) -> None:
    names = {t["name"] for t in registry.list_allowlist()}
    assert names == set(ALLOWED_TOOLS)
    assert "submit_order" not in names
    assert "place_order" not in names
    assert "set_live" not in names


def test_allowed_tools_execute(registry: ToolRegistry) -> None:
    for name in sorted(ALLOWED_TOOLS):
        if name == "search_docs":
            out = registry.call(name, {"query": "workbench LIVE"})
        else:
            out = registry.call(name)
        assert isinstance(out, dict)


def test_illegal_tools_rejected(registry: ToolRegistry) -> None:
    illegal = sorted(FORBIDDEN_TOOLS) + [
        "drop_database",
        "execute_trade",
        "set_mode",
        "connect_live",
    ]
    for name in illegal:
        with pytest.raises(ValidationError, match="tool rechazada"):
            registry.call(name)


def test_explain_live_policy_always_blocked(registry: ToolRegistry) -> None:
    assert LIVE_BLOCKED is True
    out = registry.call("explain_live_policy")
    assert out["live_blocked"] is True
    assert out["live_allowed"] is False
    assert out["chat_mutations"] is False
    assert "LIVE" in out["policy"]
