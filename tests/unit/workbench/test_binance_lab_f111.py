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


def test_binance_lab_scanner_interval_5m(binance_universe: dict[str, list[Bar]]) -> None:
    symbols = list(binance_universe.keys())
    with (
        patch(
            "quantlab.brokers.binance.public_md.BinancePublicMdClient.list_spot_symbols",
            return_value=symbols,
        ),
        patch(
            "quantlab.brokers.binance.public_md.fetch_universe_bars",
            return_value=binance_universe,
        ) as fetch_mock,
    ):
        out = lab_services.run_binance_lab_scanner(
            top_n=2,
            symbol_limit=5,
            interval="5m",
            kline_limit=60,
        )
    assert out["ok"] is True
    assert out["interval"] == "5m"
    assert out["kline_limit"] == 60
    assert fetch_mock.call_args.kwargs["interval"] == "5m"
    assert fetch_mock.call_args.kwargs["kline_limit"] == 60


def test_binance_interval_rejects_ticks() -> None:
    from quantlab.core.exceptions import ValidationError

    with pytest.raises(ValidationError, match="interval"):
        lab_services.run_binance_lab_scanner(interval="1s", top_n=2, symbol_limit=5)


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
    assert "verdict" in out
    assert "verdict_es" in out


def test_mm_backtest_cheap_alt_gets_fills() -> None:
    """half_spread absoluto 0.5 no debe dejar fills=0 en alts ~$0.50."""
    from datetime import UTC, datetime, timedelta
    from decimal import Decimal

    base = datetime(2024, 6, 1, tzinfo=UTC)
    bars: list[Bar] = []
    px = Decimal("0.50")
    for i in range(40):
        # oscilación ±2% para que LIMIT dentro del mid toque OHLC
        wobble = Decimal("0.01") if i % 2 == 0 else Decimal("-0.01")
        c = px + wobble
        t0 = base + timedelta(minutes=i)
        bars.append(
            Bar(
                instrument_id="BN:ADAUSDT",
                open=c,
                high=c * Decimal("1.02"),
                low=c * Decimal("0.98"),
                close=c,
                volume=Decimal("1000"),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(minutes=1),
                timeframe="1m",
            )
        )
    for sid in ("inventory_mm", "avellaneda_stoikov", "adaptive_mm"):
        out = lab_services.run_lab_backtest(
            strategy_id=sid,
            bars=bars,
            instrument_id="BN:ADAUSDT",
            data_source="binance_klines",
            experiment_id=f"test-cheap-{sid[:8]}",
            params={"quantity": "1", "half_spread": "0.5", "max_pos": "10"},
        )
        assert out["ok"] is True, sid
        assert out["n_fills"] > 0, (sid, out.get("verdict_es"))
        assert out["verdict"] == "traded", sid


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
