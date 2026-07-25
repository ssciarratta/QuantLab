"""Fase 18 — Control Total (sin LIVE)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from math import log
from pathlib import Path

from quantlab.backtester.accounting import REALIZED_PNL_CONVENTION
from quantlab.core.types.enums import (
    FeeType,
    LiquidityType,
    OrderSide,
    OrderStatus,
    OrderType,
    TimeInForce,
)
from quantlab.core.types.market import Bar
from quantlab.core.types.orders import Fee, Fill, Order
from quantlab.core.types.results import EquityPoint, SimulationResult
from quantlab.features.store import FeatureStore, _safe_segment
from quantlab.features.transformers import LogReturnTransformer
from quantlab.infra.health import export_ops_snapshot, run_health_checks
from quantlab.ledger import LocalPaperLedger


def _bars() -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 8, 1, tzinfo=UTC)
    for i, c0 in enumerate((100, 110, 121)):
        c = Decimal(c0)
        t0 = base + timedelta(minutes=i)
        out.append(
            Bar(
                instrument_id="F18:X",
                open=c,
                high=c + Decimal("1"),
                low=c - Decimal("1"),
                close=c,
                volume=Decimal("10"),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(minutes=1),
                timeframe="1m",
            )
        )
    return out


def test_safe_segment_no_collision() -> None:
    a = _safe_segment("a/b")
    b = _safe_segment("a_b")
    assert a != b
    assert a.startswith("a_b__")
    assert b.startswith("a_b__")


def test_log_return_decimal_ln() -> None:
    series = LogReturnTransformer().transform(_bars())
    meta = series.points[0].metadata
    assert meta is not None
    assert meta["method"] == "Decimal.ln"
    expected = Decimal("110") / Decimal("100")
    assert series.points[0].value == expected.ln()
    # No float drift vs math.log beyond Decimal quantization
    assert abs(float(series.points[0].value) - log(1.1)) < 1e-12


def test_realized_pnl_convention_documented() -> None:
    assert REALIZED_PNL_CONVENTION == "gross_excluding_fees"


def test_local_paper_ledger(tmp_path: Path) -> None:
    ts = datetime(2024, 1, 1, tzinfo=UTC)
    order = Order(
        order_id="o1",
        client_order_id="c1",
        instrument_id="F18:X",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("1"),
        filled_quantity=Decimal("1"),
        price=Decimal("10"),
        status=OrderStatus.FILLED,
        created_at=ts,
        updated_at=ts,
        time_in_force=TimeInForce.GTC,
    )
    fee = Fee(
        fee_id="f1",
        fill_id="fl1",
        amount=Decimal("0.1"),
        currency="USD",
        fee_type=FeeType.TAKER,
    )
    fill = Fill(
        fill_id="fl1",
        order_id="o1",
        instrument_id="F18:X",
        price=Decimal("10"),
        quantity=Decimal("1"),
        fee=fee,
        timestamp=ts,
        liquidity=LiquidityType.TAKER,
    )
    result = SimulationResult(
        experiment_id="f18-paper",
        equity_curve=(EquityPoint(ts, Decimal("100")),),
        fills=(fill,),
        orders=(order,),
        portfolio_snapshots=(),
        events_log=(),
    )
    ledger = LocalPaperLedger(tmp_path / "paper.sqlite")
    n = ledger.append_simulation(result)
    assert n == 4  # order + fill + equity + simulation_meta
    entries = ledger.list_entries("f18-paper")
    kinds = {e.kind for e in entries}
    assert kinds == {"order", "fill", "equity_end", "simulation_meta"}
    assert ledger.count("f18-paper") == 4
    assert ledger.append_simulation(result) == 0  # idempotente


def test_feature_store_collision_isolated(tmp_path: Path) -> None:
    from quantlab.features import ClosePriceTransformer, build_pipeline

    bars = _bars()
    # dos pipelines con nombres que colisionaban antes
    f1 = build_pipeline(ClosePriceTransformer(), name="a/b").run(bars)
    f2 = build_pipeline(ClosePriceTransformer(), name="a_b").run(bars)
    # forzar instrument_id distinto vía metadata de frame — usar pipeline name
    store = FeatureStore(tmp_path / "fs")
    r1 = store.put(f1, version="v1")
    r2 = store.put(f2, version="v1")
    assert Path(r1.path).parent.parent != Path(r2.path).parent.parent
    assert store.list_versions(f1.instrument_id, "a/b") == ("v1",)
    assert store.list_versions(f2.instrument_id, "a_b") == ("v1",)


def test_health_and_ops_export(tmp_path: Path) -> None:
    report = run_health_checks()
    assert report.ok
    assert report.live_blocked is True
    out = export_ops_snapshot(tmp_path / "ops.json")
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert "live_blocked" in text
