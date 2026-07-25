"""Regresiones de la auditoría nocturna integral — QuantLab."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import (
    FeeType,
    IntentType,
    LiquidityType,
    OrderSide,
    OrderStatus,
    OrderType,
    TimeInForce,
)
from quantlab.core.types.market import Bar, Trade
from quantlab.core.types.orders import Fee, Fill, Order, OrderIntent
from quantlab.core.types.validation import require_non_negative, require_positive
from quantlab.data.exchanges.a3.exceptions import A3DataError
from quantlab.data.normalization.bars import build_bars_from_trades
from quantlab.data.quality import sanitize_bars, validate_bars
from quantlab.execution.latency import FixedLatencyModel
from quantlab.execution.slippage import FixedSlippageModel
from quantlab.features import ClosePriceTransformer, build_pipeline
from quantlab.features.causal import assert_bars_causal_ready
from quantlab.features.store import FeatureStore, _safe_segment
from quantlab.research.alpha import AlphaScanner, GapPolicy
from quantlab.research.strategies.buy_once import BuyOnceStrategy
from quantlab.simulation import BarSimulationEngine, SimulationConfig
from quantlab.simulation.fill_model import ImmediateBarFillModel
from quantlab.simulation.portfolio_tracker import PortfolioTracker


def _bar(
    i: int,
    close: str,
    *,
    instrument_id: str = "a3:TEST",
    high: str | None = None,
    low: str | None = None,
) -> Bar:
    t0 = datetime(2024, 1, 1, tzinfo=UTC) + timedelta(minutes=i)
    c = Decimal(close)
    return Bar(
        instrument_id=instrument_id,
        open=c,
        high=Decimal(high) if high else c + Decimal("1"),
        low=Decimal(low) if low else c - Decimal("1"),
        close=c,
        volume=Decimal("100"),
        timestamp_open=t0,
        timestamp_close=t0 + timedelta(minutes=1),
        timeframe="1m",
    )


# --- Core ---


def test_require_positive_rejects_infinity_and_nan() -> None:
    with pytest.raises(ValidationError):
        require_positive(Decimal("Infinity"), "x")
    with pytest.raises(ValidationError):
        require_positive(Decimal("NaN"), "x")
    with pytest.raises(ValidationError):
        require_non_negative(Decimal("-Infinity"), "y")


def test_bar_rejects_infinite_ohlc() -> None:
    t0 = datetime(2024, 1, 1, tzinfo=UTC)
    with pytest.raises(ValidationError):
        Bar(
            instrument_id="X",
            open=Decimal("Infinity"),
            high=Decimal("Infinity"),
            low=Decimal("1"),
            close=Decimal("1"),
            volume=Decimal("1"),
            timestamp_open=t0,
            timestamp_close=t0 + timedelta(minutes=1),
            timeframe="1m",
        )


def test_fill_fee_fill_id_must_match() -> None:
    ts = datetime(2024, 1, 1, tzinfo=UTC)
    fee = Fee(
        fee_id="f1",
        fill_id="OTHER",
        amount=Decimal("0"),
        currency="USDT",
        fee_type=FeeType.TAKER,
    )
    with pytest.raises(ValidationError):
        Fill(
            fill_id="fl1",
            order_id="o1",
            instrument_id="x",
            price=Decimal("10"),
            quantity=Decimal("1"),
            fee=fee,
            timestamp=ts,
            liquidity=LiquidityType.TAKER,
        )


def test_order_filled_requires_full_quantity() -> None:
    ts = datetime(2024, 1, 1, tzinfo=UTC)
    with pytest.raises(ValidationError):
        Order(
            order_id="o1",
            client_order_id="c1",
            instrument_id="x",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("2"),
            filled_quantity=Decimal("0"),
            price=Decimal("10"),
            status=OrderStatus.FILLED,
            created_at=ts,
            updated_at=ts,
            time_in_force=TimeInForce.GTC,
        )


# --- Simulation ---


def test_fill_model_rejects_instrument_mismatch() -> None:
    model = ImmediateBarFillModel()
    intent = OrderIntent(
        intent_id="i1",
        intent_type=IntentType.PLACE_ORDER,
        instrument_id="OTHER",
        side=OrderSide.BUY,
        quantity=Decimal("1"),
        price=Decimal("100"),
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.GTC,
    )
    d = model.evaluate(intent, _bar(0, "100"))
    assert not d.filled
    assert d.reason == "instrument_mismatch"


def test_limit_order_price_is_limit_not_slippage() -> None:
    bars = [_bar(i, "100", low="99", high="101") for i in range(3)]
    engine = BarSimulationEngine(
        SimulationConfig(experiment_id="lim-price", initial_cash=Decimal("10000")),
        slippage_model=FixedSlippageModel(bps=Decimal("100")),
    )
    strategy = BuyOnceStrategy({"quantity": "1", "price": "100"})
    result = engine.run(strategy, bars)
    assert result.orders
    assert result.orders[0].order_type is OrderType.LIMIT
    assert result.orders[0].price == Decimal("100")
    assert result.fills[0].price > Decimal("100")


def test_apply_fill_rejects_non_positive() -> None:
    tracker = PortfolioTracker(cash_asset="USDT", cash=Decimal("1000"))
    with pytest.raises(ValueError):
        tracker.apply_fill(
            instrument_id="X",
            side=OrderSide.BUY,
            quantity=Decimal("0"),
            price=Decimal("10"),
            fee=Decimal("0"),
        )
    with pytest.raises(ValueError):
        tracker.apply_fill(
            instrument_id="X",
            side=OrderSide.BUY,
            quantity=Decimal("-1"),
            price=Decimal("10"),
            fee=Decimal("0"),
        )
    assert tracker.cash == Decimal("1000")


def test_latency_fill_visible_same_bar_in_context() -> None:
    """Con bars_delay=1, en la barra efectiva el ctx ya ve la posición."""

    class SpyStrategy(BuyOnceStrategy):
        def __init__(self) -> None:
            super().__init__({"quantity": "1"})
            self.seen_qty: list[Decimal] = []

        def on_bar(self, bar: Bar, context):  # type: ignore[no-untyped-def]
            qty = Decimal("0")
            if context.portfolio_state is not None:
                for p in context.portfolio_state.positions:
                    if p.instrument_id == bar.instrument_id:
                        qty = p.quantity
            self.seen_qty.append(qty)
            return super().on_bar(bar, context)

    bars = [_bar(i, "100") for i in range(4)]
    spy = SpyStrategy()
    engine = BarSimulationEngine(
        SimulationConfig(experiment_id="lat-ctx", initial_cash=Decimal("10000")),
        latency_model=FixedLatencyModel(bars_delay=1),
    )
    engine.run(spy, bars)
    # Barra 0: submit; barra 1: fill due antes de ctx → qty>=1
    assert any(q > 0 for q in spy.seen_qty[1:])


# --- Data ---


def test_validate_bars_multi_instrument_no_false_ooo() -> None:
    a = [_bar(i, "10", instrument_id="A") for i in range(2)]
    b = [_bar(i, "20", instrument_id="B") for i in range(2)]
    interleaved = [a[0], b[0], a[1], b[1]]
    report = validate_bars(interleaved)
    assert not any(i.code == "out_of_order" for i in report.issues)


def test_sanitize_multi_instrument_keeps_both() -> None:
    a = [_bar(i, "10", instrument_id="A") for i in range(2)]
    b = [_bar(i, "20", instrument_id="B") for i in range(2)]
    kept, _ = sanitize_bars([a[0], b[0], a[1], b[1]])
    assert len(kept) == 4


def test_build_bars_rejects_foreign_instrument() -> None:
    ts = datetime(2024, 1, 1, tzinfo=UTC)
    trades = [
        Trade(
            instrument_id="FOREIGN",
            price=Decimal("10"),
            quantity=Decimal("1"),
            side=OrderSide.BUY,
            timestamp=ts,
            trade_id="t1",
        )
    ]
    with pytest.raises(A3DataError):
        build_bars_from_trades(trades, timeframe="1m", instrument_id="TARGET")


# --- Execution ---


def test_slippage_rejects_bps_ge_10000() -> None:
    with pytest.raises(ValidationError):
        FixedSlippageModel(bps=Decimal("10000"))


def test_latency_rejects_unimplemented_min_delay() -> None:
    with pytest.raises(ValidationError):
        FixedLatencyModel(bars_delay=0, min_delay=timedelta(seconds=1))


# --- Features ---


def test_safe_segment_rejects_dotdot() -> None:
    with pytest.raises(ValidationError):
        _safe_segment("..")
    with pytest.raises(ValidationError):
        _safe_segment(".")


def test_feature_store_put_atomic_readable(tmp_path: Path) -> None:
    frame = build_pipeline(ClosePriceTransformer(), name="n").run(
        [_bar(i, str(100 + i)) for i in range(3)]
    )
    store = FeatureStore(tmp_path / "fs")
    ref = store.put(frame, version="v1")
    assert Path(ref.path).exists()
    loaded = store.get(frame.instrument_id, "n", "v1")
    assert loaded.bar_count == 3


def test_causal_rejects_equal_timestamps() -> None:
    b0 = _bar(0, "100")
    b1 = Bar(
        instrument_id=b0.instrument_id,
        open=b0.open,
        high=b0.high,
        low=b0.low,
        close=b0.close,
        volume=b0.volume,
        timestamp_open=b0.timestamp_open + timedelta(seconds=30),
        timestamp_close=b0.timestamp_close,  # equal close
        timeframe="1m",
    )
    with pytest.raises(ValidationError):
        assert_bars_causal_ready([b0, b1], min_lookback=1)


# --- Alpha ---


def test_forward_fill_does_not_inflate_liquidity_over_continuous() -> None:
    continuous = [_bar(i, "10", instrument_id="C", high="10.5", low="9.5") for i in range(6)]
    gapped = [
        _bar(0, "10", instrument_id="G", high="10.5", low="9.5"),
        _bar(1, "10", instrument_id="G", high="10.5", low="9.5"),
        _bar(10, "10", instrument_id="G", high="10.5", low="9.5"),
        _bar(11, "10", instrument_id="G", high="10.5", low="9.5"),
        _bar(12, "10", instrument_id="G", high="10.5", low="9.5"),
        _bar(13, "10", instrument_id="G", high="10.5", low="9.5"),
    ]
    scanner = AlphaScanner(gap_policy=GapPolicy.FORWARD_FILL)
    result = scanner.scan({"C": continuous, "G": gapped}, top_n=2, min_bars=3)
    by_id = {s.instrument_id: s for s in result.scores}
    # Liquidez del gapado no debe superar al continuo equivalente
    assert by_id["G"].liquidity_score <= by_id["C"].liquidity_score * 1.01
