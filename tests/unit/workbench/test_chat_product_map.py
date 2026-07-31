"""Chat IA — mapa producto, Monte Carlo / Simulador / panes nuevos."""

from __future__ import annotations

from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.chat.context import PRODUCT_MAP, build_system_prompt
from quantlab.workbench.chat.providers import ChatRequest, FakeProvider
from quantlab.workbench.chat.tools import ALLOWED_PANES, ALLOWED_TOOLS, ToolRegistry


def _req(message: str) -> ChatRequest:
    return ChatRequest(message=message)


def test_product_map_in_system_prompt() -> None:
    prompt = build_system_prompt(
        {
            "version": "1.01.0",
            "mode": "tester",
            "venue": "binance",
            "product_map": PRODUCT_MAP,
            "mm_strategies": [],
            "guide_excerpt": "",
            "instructor": {},
            "last_lab": None,
        }
    )
    assert "Simulador" in prompt
    assert "Monte Carlo" in prompt
    assert "LIVE_BLOCKED" in prompt
    assert "explain_montecarlo" in prompt


def test_new_explain_tools_allowlisted() -> None:
    for name in (
        "explain_simulator",
        "explain_montecarlo",
        "explain_scanner",
        "explain_workbench_map",
    ):
        assert name in ALLOWED_TOOLS


def test_new_panes_allowlisted() -> None:
    for pane in ("simulator", "montecarlo", "strategies", "sim_registry"):
        assert pane in ALLOWED_PANES


def test_fake_explains_monte_carlo_with_space() -> None:
    tools = ToolRegistry(WorkbenchState())
    turn = FakeProvider().complete(
        _req("explicame todos los parametros de monte carlo de la estrategia, uno por uno"),
        tools,
    )
    assert "explain_montecarlo" in turn.tools_used
    assert "n_scenarios" in turn.reply or "Escenarios" in turn.reply
    assert "noise_bps" in turn.reply or "Ruido" in turn.reply
    assert "FakeProvider" not in turn.reply
    assert "features=" not in turn.reply


def test_fake_explains_simulator() -> None:
    tools = ToolRegistry(WorkbenchState())
    turn = FakeProvider().complete(_req("cómo uso el Simulador para comparar"), tools)
    assert "explain_simulator" in turn.tools_used
    assert "Comparar" in turn.reply or "exchange" in turn.reply.lower()


def test_fake_opens_simulator() -> None:
    tools = ToolRegistry(WorkbenchState())
    turn = FakeProvider().complete(_req("abrí el Simulador"), tools)
    assert "open_pane" in turn.tools_used
    assert any(
        isinstance(a, dict) and a.get("pane") == "simulator" for a in (turn.actions or [])
    )


def test_fake_opens_montecarlo() -> None:
    tools = ToolRegistry(WorkbenchState())
    turn = FakeProvider().complete(_req("abrí Monte Carlo"), tools)
    assert "open_pane" in turn.tools_used
    assert any(
        isinstance(a, dict) and a.get("pane") == "montecarlo" for a in (turn.actions or [])
    )


def test_fake_map_on_unknown() -> None:
    tools = ToolRegistry(WorkbenchState())
    turn = FakeProvider().complete(_req("asdfqwer zxcv nonsense"), tools)
    assert "explain_workbench_map" in turn.tools_used
    assert "Scanner" in turn.reply or "Simulador" in turn.reply


def test_explain_tools_payload() -> None:
    tools = ToolRegistry(WorkbenchState())
    mc = tools.call("explain_montecarlo", {})
    assert mc.get("not_prediction") is True
    assert "n_scenarios" in (mc.get("params") or [])
    sim = tools.call("explain_simulator", {})
    assert sim.get("panel") == "simulator"
