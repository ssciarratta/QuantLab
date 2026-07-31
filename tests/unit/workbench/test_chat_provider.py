"""Tests FakeProvider + respuestas deterministas (Fase 22 / F113 memoria)."""

from __future__ import annotations

import pytest

from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.chat.memory import ChatMemory, ChatMessage
from quantlab.workbench.chat.providers import (
    AssistantProvider,
    ChatRequest,
    FakeProvider,
    OptionalEnvProvider,
)
from quantlab.workbench.chat.tools import ToolRegistry


def _req(message: str, **kwargs: object) -> ChatRequest:
    return ChatRequest(message=message, **kwargs)  # type: ignore[arg-type]


def test_fake_provider_salud() -> None:
    tools = ToolRegistry(WorkbenchState())
    turn = FakeProvider().complete(_req("¿cómo está la salud del sistema?"), tools)
    assert turn.provider == "fake"
    assert "get_health" in turn.tools_used
    assert "Salud" in turn.reply or "ok=" in turn.reply.lower()


def test_fake_provider_modo() -> None:
    tools = ToolRegistry(WorkbenchState())
    turn = FakeProvider().complete(_req("cuál es el modo actual"), tools)
    assert "get_mode" in turn.tools_used
    assert "Modo" in turn.reply or "tester" in turn.reply.lower()


def test_fake_provider_backtest() -> None:
    tools = ToolRegistry(WorkbenchState())
    turn = FakeProvider().complete(_req("explicame el backtest momentum"), tools)
    assert "explain_backtest" in turn.tools_used
    assert "backtest" in turn.reply.lower()


def test_fake_provider_scanner() -> None:
    tools = ToolRegistry(WorkbenchState())
    turn = FakeProvider().complete(_req("qué hace el scanner alpha"), tools)
    assert "explain_scanner" in turn.tools_used or "instructor_guide" in turn.tools_used
    assert "scanner" in turn.reply.lower() or "ranking" in turn.reply.lower()


def test_fake_provider_live() -> None:
    tools = ToolRegistry(WorkbenchState())
    turn = FakeProvider().complete(_req("puedo activar live y mandar órdenes?"), tools)
    assert "explain_live_policy" in turn.tools_used
    assert "bloqueado" in turn.reply.lower() or "live_blocked" in turn.reply.lower()


def test_fake_provider_ayuda() -> None:
    tools = ToolRegistry(WorkbenchState())
    turn = FakeProvider().complete(_req("ayuda docs workbench"), tools)
    assert turn.tools_used
    assert any(
        t in turn.tools_used for t in ("search_docs", "list_capabilities", "explain_live_policy")
    )


def test_optional_env_falls_back_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QUANTLAB_LLM_API_KEY", "DISABLED")
    tools = ToolRegistry(WorkbenchState())
    turn = OptionalEnvProvider().complete(_req("salud"), tools)
    assert turn.provider == "fake"
    assert "get_health" in turn.tools_used


def test_assistant_falls_back_when_llm_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QUANTLAB_LLM_API_KEY", "test-invalid-key")
    tools = ToolRegistry(WorkbenchState())
    turn = AssistantProvider().complete(_req("cuál es el modo actual"), tools)
    assert turn.provider in {"fake", "fake_fallback"}
    assert "get_mode" in turn.tools_used


def test_followup_dale_uses_memory() -> None:
    state = WorkbenchState()
    state.chat_instructor_ctx = {"lesson": "alpha_binance"}
    tools = ToolRegistry(state)
    history = (
        ChatMessage(role="user", content="vamos alpha binance"),
        ChatMessage(
            role="assistant",
            content="Paso 1: Ranking alpha Binance en Guided Lab.",
        ),
    )
    turn = FakeProvider().complete(_req("dale", history=history), tools)
    assert "instructor_guide" in turn.tools_used
    assert "inventory_mm" in turn.reply.lower() or "MM" in turn.reply
