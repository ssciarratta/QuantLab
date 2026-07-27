"""Fees Binance Spot VIP0 para lab/backtest."""

from __future__ import annotations

from decimal import Decimal

from quantlab.brokers.binance.fees import (
    SPOT_VIP0_MAKER_BPS,
    SPOT_VIP0_TAKER_BPS,
    binance_spot_fee_model,
    resolve_binance_spot_fee_schedule,
)
from quantlab.core.types.enums import LiquidityType, OrderSide
from quantlab.workbench.lab_services import run_lab_backtest


def test_binance_spot_vip0_schedule() -> None:
    sched = resolve_binance_spot_fee_schedule(use_bnb_discount=False)
    assert sched.maker_bps == SPOT_VIP0_MAKER_BPS
    assert sched.taker_bps == SPOT_VIP0_TAKER_BPS
    assert sched.use_bnb_discount is False
    d = sched.to_dict()
    assert d["maker_bps"] == "10"
    assert "binance.com" in d["source_url"]


def test_binance_spot_bnb_discount() -> None:
    sched = resolve_binance_spot_fee_schedule(use_bnb_discount=True)
    assert sched.maker_bps == Decimal("7.5")
    assert sched.taker_bps == Decimal("7.5")


def test_fee_model_assess_taker_10bps() -> None:
    model = binance_spot_fee_model(use_bnb_discount=False)
    a = model.assess(
        side=OrderSide.BUY,
        price=Decimal("100"),
        quantity=Decimal("1"),
        liquidity=LiquidityType.TAKER,
    )
    assert a.amount == Decimal("0.10000000")  # 10 bps de 100


def test_lab_backtest_charges_binance_fees() -> None:
    out = run_lab_backtest(strategy_id="buy_once", n_bars=12, experiment_id="fee-bt-1")
    assert out["ok"] is True
    assert out["n_fills"] >= 1
    assert Decimal(out["total_fees"]) > 0
    assert out["fee_schedule"]["schedule_id"] == "binance_spot_vip0"
    assert out["fee_schedule"]["taker_bps"] == "10"
    assert isinstance(out["fills"], list)
    assert len(out["fills"]) >= 1
    assert out["fills"][0]["price"]
    assert out["bar_range"] is not None
    assert out["bar_range"]["n_bars"] == 12
