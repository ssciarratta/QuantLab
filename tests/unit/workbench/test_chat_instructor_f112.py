"""Chat instructor — alpha Binance + market making (F112/F113)."""

from __future__ import annotations

from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.chat.memory import ChatMemory
from quantlab.workbench.chat.orchestrator import ChatOrchestrator
from quantlab.workbench.chat.providers import ChatRequest, FakeProvider, format_instructor_reply
from quantlab.workbench.chat.tools import ToolRegistry


def _req(message: str, state: WorkbenchState | None = None) -> ChatRequest:
    return ChatRequest(message=message)


def test_instructor_full_alpha_mm_flow() -> None:
    state = WorkbenchState()
    tools = ToolRegistry(state)
    msg = (
        "vamos a correr alpha en binance y detectar monedas, "
        "luego según market making cuál podemos probar"
    )
    turn = FakeProvider().complete(_req(msg), tools)
    assert "instructor_guide" in turn.tools_used
    assert "Paso 1:" in turn.reply
    assert "inventory_mm" in turn.reply or "Inventory MM" in turn.reply
    assert "Ranking alpha Binance" in turn.reply


def test_instructor_alpha_only() -> None:
    state = WorkbenchState()
    tools = ToolRegistry(state)
    turn = FakeProvider().complete(
        _req("vamos a correr alpha en binance y detectar monedas"), tools
    )
    assert "instructor_guide" in turn.tools_used
    assert "Ranking alpha Binance" in turn.reply


def test_instructor_mm_after_ranking() -> None:
    state = WorkbenchState()
    state.last_lab_result = {
        "kind": "binance_scanner",
        "selected_symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
    }
    tools = ToolRegistry(state)
    turn = FakeProvider().complete(_req("ya tengo el ranking, ¿qué MM probamos?"), tools)
    assert "instructor_guide" in turn.tools_used
    assert "BTCUSDT" in turn.reply
    assert "inventory_mm" in turn.reply


def test_instructor_tool_mm_recommendations() -> None:
    state = WorkbenchState()
    tools = ToolRegistry(state)
    data = tools.call("instructor_guide", {"lesson": "mm_after_alpha"})
    assert data["ok"] is True
    assert len(data["mm_recommendations"]) >= 2
    text = format_instructor_reply(data)
    assert "avellaneda_stoikov" in text


def test_chat_memory_persist_roundtrip(tmp_path) -> None:
    path = tmp_path / "chat_history.json"
    mem = ChatMemory()
    mem.append_user("hola")
    mem.append_assistant("hola, ¿en qué te ayudo?", tools_used=["get_assistant_context"])
    mem.save(path)
    loaded = ChatMemory.load(path)
    assert len(loaded.messages) == 2
    assert loaded.messages[0].role == "user"


def test_orchestrator_memory_turns(tmp_path) -> None:
    state = WorkbenchState()
    state.session_parent = tmp_path
    orch = ChatOrchestrator(state, provider=FakeProvider())
    out = orch.handle_message("cuál es el modo")
    assert out["memory_turns"] >= 2
    hist = orch.history_payload()
    assert hist["count"] >= 2
    orch.clear_history()
    assert orch.history_payload()["count"] == 0


def test_typo_schaner_binance_howto() -> None:
    state = WorkbenchState()
    tools = ToolRegistry(state)
    turn = FakeProvider().complete(
        "quiero correr alpha schaner en binance como hago?",
        tools,
    )
    assert "instructor_guide" in turn.tools_used or "explain_binance_lab" in turn.tools_used
    assert "Ranking alpha" in turn.reply or "Guided Lab" in turn.reply
    assert "backtest, scanner, metrics" not in turn.reply.lower()
