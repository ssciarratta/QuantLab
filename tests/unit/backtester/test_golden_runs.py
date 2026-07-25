"""Golden runs reproducibles — Fase 6."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from quantlab.backtester import (
    BarBacktestConfig,
    BarBacktester,
    assert_matches_golden,
    build_golden,
    load_golden,
    save_golden,
)
from quantlab.core.types.market import Bar
from quantlab.research.strategies.buy_once import BuyOnceStrategy

GOLDEN_PATH = Path(__file__).resolve().parents[2] / "golden" / "fase6_buy_once.json"


def _bars() -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 5, 1, tzinfo=UTC)
    for i in range(6):
        c = Decimal(100 + i)
        t0 = base + timedelta(minutes=i)
        out.append(
            Bar(
                instrument_id="F6:GOLD",
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


def _run():
    bt = BarBacktester(
        BarBacktestConfig(experiment_id="f6-golden-buy-once", initial_cash=Decimal("10000"))
    )
    return bt.run(BuyOnceStrategy({"quantity": "1", "price": "101"}), _bars())


def test_golden_run_reproducible() -> None:
    result = _run()
    # Si no existe golden, lo materializa (primera vez / regeneración controlada)
    if not GOLDEN_PATH.exists():
        spec = build_golden(
            name="fase6_buy_once",
            simulation=result.simulation,
            metrics=result.metrics,
        )
        save_golden(GOLDEN_PATH, spec)
    golden = load_golden(GOLDEN_PATH)
    assert_matches_golden(
        simulation=result.simulation,
        metrics=result.metrics,
        golden=golden,
    )
    # Segunda corrida idéntica
    result2 = _run()
    assert_matches_golden(
        simulation=result2.simulation,
        metrics=result2.metrics,
        golden=golden,
    )
