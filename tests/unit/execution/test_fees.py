"""Tests FeeModel — Fase 5 Módulo 2."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from quantlab.core.types.enums import FeeType, LiquidityType, OrderSide
from quantlab.core.types.market import Bar
from quantlab.execution import MakerTakerFeeModel, ProportionalFeeModel, ZeroFeeModel
from quantlab.research.strategies.buy_once import BuyOnceStrategy
from quantlab.simulation import BarSimulationEngine, SimulationConfig


def _bar(i: int, close: str = "100") -> Bar:
    t0 = datetime(2024, 1, 1, tzinfo=UTC) + timedelta(minutes=i)
    c = Decimal(close)
    return Bar(
        instrument_id="a3:TEST",
        open=c,
        high=c + Decimal("1"),
        low=c - Decimal("1"),
        close=c,
        volume=Decimal("100"),
        timestamp_open=t0,
        timestamp_close=t0 + timedelta(minutes=1),
        timeframe="1m",
    )


def test_zero_fee() -> None:
    a = ZeroFeeModel().assess(
        side=OrderSide.BUY,
        price=Decimal("100"),
        quantity=Decimal("2"),
        liquidity=LiquidityType.TAKER,
    )
    assert a.amount == Decimal("0")


def test_proportional_fee() -> None:
    model = ProportionalFeeModel(rate=Decimal("0.001"))
    a = model.assess(
        side=OrderSide.BUY,
        price=Decimal("100"),
        quantity=Decimal("2"),
        liquidity=LiquidityType.TAKER,
    )
    assert a.amount == Decimal("0.20000000")
    assert a.fee_type is FeeType.TAKER


def test_maker_taker_differentiated() -> None:
    model = MakerTakerFeeModel(maker_bps=Decimal("1"), taker_bps=Decimal("5"))
    maker = model.assess(
        side=OrderSide.SELL,
        price=Decimal("100"),
        quantity=Decimal("1"),
        liquidity=LiquidityType.MAKER,
    )
    taker = model.assess(
        side=OrderSide.SELL,
        price=Decimal("100"),
        quantity=Decimal("1"),
        liquidity=LiquidityType.TAKER,
    )
    assert maker.amount == Decimal("0.01000000")
    assert taker.amount == Decimal("0.05000000")
    assert maker.fee_type is FeeType.MAKER
    assert taker.fee_type is FeeType.TAKER


def test_engine_maker_taker_fee_on_fill() -> None:
    bars = [_bar(i) for i in range(3)]
    engine = BarSimulationEngine(
        SimulationConfig(experiment_id="fee-1", initial_cash=Decimal("100000")),
        fee_model=MakerTakerFeeModel(maker_bps=Decimal("0"), taker_bps=Decimal("10")),
    )
    result = engine.run(BuyOnceStrategy({"quantity": "1"}), bars)
    assert len(result.fills) == 1
    # limit @ high=101, taker 10 bps → fee = 101 * 1 * 0.001 = 0.101
    assert result.fills[0].fee.amount == Decimal("0.10100000")
    assert result.fills[0].fee.fee_type is FeeType.TAKER
    assert result.metadata["fee_model"] == "fee.maker_taker_bps.v1"
