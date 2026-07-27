"""F111 — Binance alpha scanner + pipeline scan→backtest."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest

from quantlab.core.types.market import Bar
from quantlab.workbench import lab_services


def _fake_bars(sym: str, n: int = 24, *, drift: int = 1) -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 6, 1, tzinfo=UTC)
    for i in range(n):
        c = Decimal(100 + drift * i)
        t0 = base + timedelta(hours=i)
        out.append(
            Bar(
                instrument_id=f"BN:{sym}",
                open=c,
                high=c + Decimal("1"),
                low=c - Decimal("1"),
                close=c,
                volume=Decimal("1000") + Decimal(i * 10),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(hours=1),
                timeframe="1h",
            )
        )
    return out


@pytest.fixture
def binance_universe() -> dict[str, list[Bar]]:
    return {
        "BTCUSDT": _fake_bars("BTCUSDT", drift=2),
        "ETHUSDT": _fake_bars("ETHUSDT", drift=3),
        "BNBUSDT": _fake_bars("BNBUSDT", drift=1),
        "SOLUSDT": _fake_bars("SOLUSDT", drift=4),
        "XRPUSDT": _fake_bars("XRPUSDT", drift=0),
    }


def test_binance_lab_scanner_mock(binance_universe: dict[str, list[Bar]]) -> None:
    symbols = list(binance_universe.keys())

    with (
        patch(
            "quantlab.brokers.binance.public_md.BinancePublicMdClient.list_spot_symbols",
            return_value=symbols,
        ),
        patch(
            "quantlab.brokers.binance.public_md.fetch_universe_bars",
            return_value=binance_universe,
        ),
    ):
        out = lab_services.run_binance_lab_scanner(top_n=3, symbol_limit=5)

    assert out["ok"] is True
    assert out["kind"] == "binance_scanner"
    assert len(out["selected_symbols"]) == 3
    assert out["live_routing"] is False
    assert out["read_only"] is True


def test_binance_lab_pipeline_mock(binance_universe: dict[str, list[Bar]]) -> None:
    symbols = list(binance_universe.keys())

    with (
        patch(
            "quantlab.brokers.binance.public_md.BinancePublicMdClient.list_spot_symbols",
            return_value=symbols,
        ),
        patch(
            "quantlab.brokers.binance.public_md.fetch_universe_bars",
            return_value=binance_universe,
        ),
    ):
        out = lab_services.run_binance_lab_pipeline(
            strategy_id="momentum",
            top_n=3,
            symbol_limit=5,
            experiment_id_prefix="test-pipe",
        )

    assert out["ok"] is True
    assert out["kind"] == "binance_pipeline"
    batch = out["backtests"]
    assert batch["n_ok"] == 3
    assert batch["live_routing"] is False


def test_run_lab_backtest_with_bars(binance_universe: dict[str, list[Bar]]) -> None:
    bars = binance_universe["BTCUSDT"]
    out = lab_services.run_lab_backtest(
        strategy_id="momentum",
        bars=bars,
        instrument_id="BN:BTCUSDT",
        data_source="binance_klines",
        experiment_id="test-bn-bt",
    )
    assert out["ok"] is True
    assert out["data_source"] == "binance_klines"
    assert out["instrument_id"] == "BN:BTCUSDT"
    assert out["n_bars"] == len(bars)


def test_chat_guided_lab_intent() -> None:
    from quantlab.workbench.api import WorkbenchState
    from quantlab.workbench.chat.providers import FakeProvider
    from quantlab.workbench.chat.tools import ToolRegistry

    state = WorkbenchState()
    tools = ToolRegistry(state)
    turn = FakeProvider().complete("explícame guided lab paso a paso", tools)
    assert "explain_guided_lab" in turn.tools_used
    assert "Guided Lab" in turn.reply


def test_chat_binance_intent() -> None:
    from quantlab.workbench.api import WorkbenchState
    from quantlab.workbench.chat.providers import FakeProvider
    from quantlab.workbench.chat.tools import ToolRegistry

    state = WorkbenchState()
    tools = ToolRegistry(state)
    turn = FakeProvider().complete("cómo hago ranking alpha binance", tools)
    assert "explain_binance_lab" in turn.tools_used
    assert "binance/scanner" in turn.reply.lower() or "scanner" in turn.reply.lower()


def test_chat_suggest_workflow_intent() -> None:
    from quantlab.workbench.api import WorkbenchState
    from quantlab.workbench.chat.providers import FakeProvider
    from quantlab.workbench.chat.tools import ToolRegistry

    state = WorkbenchState()
    tools = ToolRegistry(state)
    turn = FakeProvider().complete("¿cómo empiezo?", tools)
    assert "suggest_workflow" in turn.tools_used
    assert "quantlab-workbench" in turn.reply.lower() or "Guided Lab" in turn.reply
