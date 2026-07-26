"""Tests FakeProvider + respuestas deterministas (Fase 22)."""

from __future__ import annotations

import pytest

from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.chat.providers import FakeProvider, OptionalEnvProvider
from quantlab.workbench.chat.tools import ToolRegistry


def test_fake_provider_salud() -> None:
    tools = ToolRegistry(WorkbenchState())
    turn = FakeProvider().complete("¿cómo está la salud del sistema?", tools)
    assert turn.provider == "fake"
    assert "get_health" in turn.tools_used
    assert "Salud" in turn.reply or "ok=" in turn.reply.lower()


def test_fake_provider_modo() -> None:
    tools = ToolRegistry(WorkbenchState())
    turn = FakeProvider().complete("cuál es el modo actual", tools)
    assert "get_mode" in turn.tools_used
    assert "Modo" in turn.reply or "tester" in turn.reply.lower()


def test_fake_provider_backtest() -> None:
    tools = ToolRegistry(WorkbenchState())
    turn = FakeProvider().complete("explicame el backtest momentum", tools)
    assert "explain_backtest" in turn.tools_used
    assert "backtest" in turn.reply.lower()


def test_fake_provider_scanner() -> None:
    tools = ToolRegistry(WorkbenchState())
    turn = FakeProvider().complete("qué hace el scanner alpha", tools)
    assert "list_capabilities" in turn.tools_used


def test_fake_provider_live() -> None:
    tools = ToolRegistry(WorkbenchState())
    turn = FakeProvider().complete("puedo activar live y mandar órdenes?", tools)
    assert "explain_live_policy" in turn.tools_used
    assert "bloqueado" in turn.reply.lower() or "live_blocked" in turn.reply.lower()


def test_fake_provider_ayuda() -> None:
    tools = ToolRegistry(WorkbenchState())
    turn = FakeProvider().complete("ayuda docs workbench", tools)
    assert turn.tools_used
    assert any(
        t in turn.tools_used for t in ("search_docs", "list_capabilities", "explain_live_policy")
    )


def test_optional_env_falls_back_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QUANTLAB_LLM_API_KEY", "DISABLED")
    tools = ToolRegistry(WorkbenchState())
    turn = OptionalEnvProvider().complete("salud", tools)
    assert turn.provider == "fake"
    assert "get_health" in turn.tools_used


def test_optional_env_annotates_when_key_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QUANTLAB_LLM_API_KEY", "test-placeholder-not-real")
    monkeypatch.setenv("QUANTLAB_LLM_MODEL", "stub")
    tools = ToolRegistry(WorkbenchState())
    turn = OptionalEnvProvider().complete("modo", tools)
    assert turn.provider == "optional_env"
    assert turn.reply.startswith("[optional_env")
    assert "get_mode" in turn.tools_used
