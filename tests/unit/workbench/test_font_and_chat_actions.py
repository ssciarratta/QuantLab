"""Font scale settings + chat open/run actions."""

from __future__ import annotations

from unittest.mock import patch

from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.chat.providers import FakeProvider
from quantlab.workbench.chat.tools import ALLOWED_TOOLS, ToolRegistry
from quantlab.workbench.settings import default_settings, normalize_settings, parse_ui_font_scale


def test_ui_font_scale_default() -> None:
    s = default_settings()
    assert s["ui_font_scale"] == 1.18
    assert parse_ui_font_scale(1.3) == 1.3
    out = normalize_settings({**default_settings(), "ui_font_scale": 1.45})
    assert out["ui_font_scale"] == 1.45


def test_open_pane_tool() -> None:
    tools = ToolRegistry(WorkbenchState())
    out = tools.call("open_pane", {"pane": "guided_lab"})
    assert out["ok"] is True
    assert out["ui_actions"][0]["type"] == "open_pane"
    assert "open_pane" in ALLOWED_TOOLS


def test_chat_open_intent() -> None:
    tools = ToolRegistry(WorkbenchState())
    turn = FakeProvider().complete("abrí Guided Lab", tools)
    assert "open_pane" in turn.tools_used
    assert turn.actions
    assert turn.actions[0]["pane"] == "guided_lab"


def test_chat_run_alpha_imperative() -> None:
    state = WorkbenchState()
    tools = ToolRegistry(state)
    fake = {
        "ok": True,
        "kind": "binance_scanner",
        "selected_symbols": ["BTCUSDT", "ETHUSDT"],
        "n_symbols_fetched": 2,
        "scores": [{"instrument_id": "BN:BTCUSDT", "composite": 1.0}],
        "top_n": 5,
        "live_routing": False,
        "read_only": True,
    }
    with patch(
        "quantlab.workbench.lab_services.run_binance_lab_scanner",
        return_value=fake,
    ):
        turn = FakeProvider().complete("Corré alpha en Binance", tools)
    assert "run_binance_alpha" in turn.tools_used
    assert any(a.get("type") == "open_pane" for a in turn.actions)
    assert "BTCUSDT" in turn.reply


def test_chat_howto_does_not_auto_run() -> None:
    tools = ToolRegistry(WorkbenchState())
    turn = FakeProvider().complete(
        "quiero correr alpha scanner en binance como hago?",
        tools,
    )
    assert "run_binance_alpha" not in turn.tools_used
    assert "instructor_guide" in turn.tools_used or "explain_binance_lab" in turn.tools_used
