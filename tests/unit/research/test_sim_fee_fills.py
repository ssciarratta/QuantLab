"""Fees venue deben afectar fills del backtest lab."""

from __future__ import annotations

from decimal import Decimal

from quantlab.execution.fees import MakerTakerFeeModel
from quantlab.research.sim.fee_schedules import (
    fee_model_from_schedule,
    get_fee_schedule,
    schedule_to_lab_fee_dict,
)
from quantlab.workbench.lab_services import run_lab_backtest


def test_fee_model_from_schedule_binance_futures() -> None:
    sched = get_fee_schedule("binance", "futures")
    model = fee_model_from_schedule(sched)
    assert isinstance(model, MakerTakerFeeModel)
    assert model.taker_bps == Decimal("5")
    assert "binance_futures" in model.model_id


def test_run_lab_backtest_custom_taker_changes_total_fees() -> None:
    cheap = MakerTakerFeeModel(
        maker_bps=Decimal("0"),
        taker_bps=Decimal("1"),
        model_id="fee.test.cheap",
    )
    expensive = MakerTakerFeeModel(
        maker_bps=Decimal("0"),
        taker_bps=Decimal("50"),
        model_id="fee.test.expensive",
    )
    a = run_lab_backtest(
        strategy_id="buy_once",
        n_bars=24,
        fee_model=cheap,
        fee_schedule_meta=schedule_to_lab_fee_dict(get_fee_schedule("binance", "futures")),
    )
    b = run_lab_backtest(
        strategy_id="buy_once",
        n_bars=24,
        fee_model=expensive,
        fee_schedule_meta={
            "schedule_id": "exp",
            "as_of": "",
            "source_url": "",
            "maker_bps": "0",
            "taker_bps": "50",
            "maker_pct": "0",
            "taker_pct": "0.5",
            "use_bnb_discount": False,
            "note": "test",
        },
    )
    assert Decimal(a["total_fees"]) < Decimal(b["total_fees"])
    assert a["fee_per_side"]["taker_bps"] == "5" or a["fee_schedule"]["taker_bps"] == "5"
    assert b["fee_model"] == "fee.test.expensive"
