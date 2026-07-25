"""Tests BarBacktester 5A — Fase 6."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from quantlab.backtester import BarBacktestConfig, BarBacktester
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.execution.fees import ProportionalFeeModel
from quantlab.research.strategies.buy_once import BuyOnceStrategy
from quantlab.research.strategies.simple_momentum import SimpleMomentumStrategy


def _bars(n: int = 8, *, start: int = 100) -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 5, 1, tzinfo=UTC)
    for i in range(n):
        c = Decimal(start + i)
        t0 = base + timedelta(minutes=i)
        out.append(
            Bar(
                instrument_id="F6:TEST",
                open=c,
                high=c + Decimal("1"),
                low=c - Decimal("1"),
                close=c,
                volume=Decimal("100"),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(minutes=1),
                timeframe="1m",
            )
        )
    return out


def test_bar_backtester_buy_once_accounting() -> None:
    bt = BarBacktester(BarBacktestConfig(experiment_id="f6-buy", initial_cash=Decimal("10000")))
    result = bt.run(BuyOnceStrategy({"quantity": "2"}), _bars())
    assert result.accounting.ok
    assert len(result.simulation.fills) == 1
    assert "sharpe" in result.metrics.metrics
    assert "sortino" in result.metrics.metrics


def test_bar_backtester_with_fees_still_balances() -> None:
    bt = BarBacktester(
        BarBacktestConfig(experiment_id="f6-fee", initial_cash=Decimal("10000")),
        fee_model=ProportionalFeeModel(rate=Decimal("0.001")),
    )
    result = bt.run(BuyOnceStrategy({"quantity": "1"}), _bars())
    assert result.accounting.ok
    assert result.accounting.total_fees > 0


def test_simple_momentum_produces_trade() -> None:
    # Closes estrictamente crecientes → buy tras lookback
    bars = _bars(10, start=50)
    bt = BarBacktester(BarBacktestConfig(experiment_id="f6-mom", initial_cash=Decimal("50000")))
    result = bt.run(SimpleMomentumStrategy({"lookback": 2, "quantity": "1"}), bars)
    assert result.accounting.ok
    assert len(result.simulation.fills) >= 1


def test_rejects_empty_and_short_timeframe() -> None:
    bt = BarBacktester(BarBacktestConfig(experiment_id="f6-bad"))
    with pytest.raises(ValidationError):
        bt.run(BuyOnceStrategy(), [])
    bad = _bars(2)
    # acortar duración de la primera barra
    short = Bar(
        instrument_id=bad[0].instrument_id,
        open=bad[0].open,
        high=bad[0].high,
        low=bad[0].low,
        close=bad[0].close,
        volume=bad[0].volume,
        timestamp_open=bad[0].timestamp_open,
        timestamp_close=bad[0].timestamp_open + timedelta(seconds=30),
        timeframe="1m",
    )
    with pytest.raises(ValidationError):
        bt.run(BuyOnceStrategy(), [short, bad[1]])
