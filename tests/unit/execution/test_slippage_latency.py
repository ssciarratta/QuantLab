"""Tests Slippage / Latency — Fase 5 Módulo 1."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import OrderSide
from quantlab.core.types.market import Bar
from quantlab.execution import (
    FixedLatencyModel,
    FixedSlippageModel,
    NoSlippageModel,
    VolumeShareSlippageModel,
    ZeroLatencyModel,
)
from quantlab.research.strategies.buy_once import BuyOnceStrategy
from quantlab.simulation import BarSimulationEngine, SimulationConfig


def _bar(
    i: int,
    close: str,
    *,
    volume: str = "100",
    instrument_id: str = "a3:TEST",
) -> Bar:
    t0 = datetime(2024, 1, 1, tzinfo=UTC) + timedelta(minutes=i)
    c = Decimal(close)
    return Bar(
        instrument_id=instrument_id,
        open=c,
        high=c + Decimal("1"),
        low=c - Decimal("1"),
        close=c,
        volume=Decimal(volume),
        timestamp_open=t0,
        timestamp_close=t0 + timedelta(minutes=1),
        timeframe="1m",
    )


def test_no_slippage_identity() -> None:
    bar = _bar(0, "100")
    model = NoSlippageModel()
    out = model.apply(side=OrderSide.BUY, price=Decimal("100"), quantity=Decimal("1"), bar=bar)
    assert out == Decimal("100")


def test_fixed_slippage_adverse_buy_and_sell() -> None:
    bar = _bar(0, "100")
    model = FixedSlippageModel(bps=Decimal("10"))  # 10 bps = 0.1%
    buy = model.apply(side=OrderSide.BUY, price=Decimal("100"), quantity=Decimal("1"), bar=bar)
    sell = model.apply(side=OrderSide.SELL, price=Decimal("100"), quantity=Decimal("1"), bar=bar)
    assert buy == Decimal("100.1")
    assert sell == Decimal("99.9")


def test_fixed_slippage_rejects_bps_above_max() -> None:
    with pytest.raises(ValidationError):
        FixedSlippageModel(bps=Decimal("50"), max_slippage_bps=Decimal("10"))


def test_volume_share_caps_at_max() -> None:
    bar = _bar(0, "100", volume="10")
    model = VolumeShareSlippageModel(impact_bps=Decimal("1000"), max_slippage_bps=Decimal("25"))
    # share = 10/10 = 1 → raw 1000 bps → capped 25
    px = model.apply(side=OrderSide.BUY, price=Decimal("100"), quantity=Decimal("10"), bar=bar)
    assert px == Decimal("100.25")


def test_volume_share_zero_volume_uses_max() -> None:
    bar = _bar(0, "100", volume="0")
    model = VolumeShareSlippageModel(impact_bps=Decimal("100"), max_slippage_bps=Decimal("40"))
    px = model.apply(side=OrderSide.SELL, price=Decimal("100"), quantity=Decimal("1"), bar=bar)
    assert px == Decimal("99.6")


def test_zero_latency_same_bar() -> None:
    d = ZeroLatencyModel().resolve(
        submit_index=2, submit_time=datetime(2024, 1, 1, tzinfo=UTC), series_length=5
    )
    assert d.executable and d.effective_index == 2


def test_fixed_latency_beyond_series() -> None:
    model = FixedLatencyModel(bars_delay=3)
    d = model.resolve(submit_index=3, submit_time=datetime(2024, 1, 1, tzinfo=UTC), series_length=5)
    assert not d.executable
    assert d.reason == "latency_beyond_series"


def test_fixed_latency_negative_rejected() -> None:
    with pytest.raises(ValidationError):
        FixedLatencyModel(bars_delay=-1)


def test_engine_default_policies_preserve_fase4_fill() -> None:
    bars = [_bar(i, str(100 + i)) for i in range(5)]
    engine = BarSimulationEngine(SimulationConfig(experiment_id="e-f4"))
    result = engine.run(BuyOnceStrategy({"quantity": "1"}), bars)
    assert len(result.fills) == 1
    assert result.metadata["slippage_model"] == "slippage.none.v1"
    assert result.metadata["latency_model"] == "latency.zero.v1"


def test_engine_with_slippage_worsens_buy_price() -> None:
    bars = [_bar(i, "100") for i in range(3)]
    engine = BarSimulationEngine(
        SimulationConfig(experiment_id="e-slip"),
        slippage_model=FixedSlippageModel(bps=Decimal("100")),  # 1%
    )
    result = engine.run(BuyOnceStrategy({"quantity": "1"}), bars)
    assert len(result.fills) == 1
    # BuyOnce usa bar.high (=101) como límite; fill base 101 + 1% = 102.01
    assert result.fills[0].price == Decimal("102.01")


def test_engine_latency_defers_fill_one_bar() -> None:
    bars = [_bar(i, str(100 + i)) for i in range(4)]
    engine = BarSimulationEngine(
        SimulationConfig(experiment_id="e-lat"),
        latency_model=FixedLatencyModel(bars_delay=1),
    )
    result = engine.run(BuyOnceStrategy({"quantity": "1"}), bars)
    assert len(result.fills) == 1
    # Intent en barra 0 → fill en barra 1 (close path via limit at bar.high of bar1)
    assert result.fills[0].timestamp == bars[1].timestamp_close
