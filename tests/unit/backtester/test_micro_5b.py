"""Tests Backtester 5B — Fase 7."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from quantlab.backtester import (
    BookSlippageModel,
    InventoryTracker,
    MarketReplay,
    MicroBacktestConfig,
    MicroBacktester,
    PartialFillModel,
    RestingOrder,
)
from quantlab.core.types.enums import IntentType, OrderSide, OrderType, TimeInForce
from quantlab.core.types.market import BookLevel, OrderBookSnapshot, Trade
from quantlab.core.types.orders import OrderIntent
from quantlab.research.strategies.inventory_mm import InventoryMMStrategy


def _ts(i: int) -> datetime:
    return datetime(2024, 8, 1, tzinfo=UTC) + timedelta(seconds=i)


def _trade(i: int, price: str, qty: str = "2", side: OrderSide = OrderSide.SELL) -> Trade:
    return Trade(
        instrument_id="M:X",
        price=Decimal(price),
        quantity=Decimal(qty),
        side=side,
        timestamp=_ts(i),
        trade_id=f"t{i}",
    )


def _book(i: int, bid: str, ask: str) -> OrderBookSnapshot:
    return OrderBookSnapshot(
        instrument_id="M:X",
        timestamp=_ts(i),
        bids=(BookLevel(price=Decimal(bid), quantity=Decimal("10")),),
        asks=(BookLevel(price=Decimal(ask), quantity=Decimal("10")),),
        sequence_id=i,
    )


def test_partial_fill_limit_buy() -> None:
    model = PartialFillModel(max_fill_ratio=Decimal("0.5"))
    intent = OrderIntent(
        intent_id="b1",
        intent_type=IntentType.PLACE_ORDER,
        instrument_id="M:X",
        side=OrderSide.BUY,
        quantity=Decimal("10"),
        price=Decimal("100"),
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.GTC,
    )
    resting = RestingOrder(order_id="o1", intent=intent, remaining=Decimal("10"))
    d = model.match_trade(resting, _trade(1, "99", "4"))
    assert d.filled
    assert d.fill_qty == Decimal("2")  # 50% of 4
    assert d.remaining_qty == Decimal("8")


def test_book_slippage_walks_levels() -> None:
    book = OrderBookSnapshot(
        instrument_id="M:X",
        timestamp=_ts(0),
        bids=(BookLevel(Decimal("99"), Decimal("1")),),
        asks=(
            BookLevel(Decimal("100"), Decimal("1")),
            BookLevel(Decimal("101"), Decimal("5")),
        ),
        sequence_id=0,
    )
    px = BookSlippageModel().apply(side=OrderSide.BUY, quantity=Decimal("3"), book=book)
    # 1@100 + 2@101 = 302/3
    assert px == Decimal("100.66666667")


def test_inventory_skew_and_limit() -> None:
    inv = InventoryTracker(max_abs_position=Decimal("5"))
    inv.apply(OrderSide.BUY, Decimal("2"), Decimal("10"))
    assert inv.position == Decimal("2")
    assert inv.skew_bias() > 0
    assert not inv.can_increase(OrderSide.BUY, Decimal("4"))


def test_market_replay_orders_events() -> None:
    replay = MarketReplay(trades=[_trade(2, "100")], books=[_book(1, "99", "101")])
    assert len(replay) == 2
    events = list(replay)
    assert events[0].event_type.value == "order_book_snapshot"
    assert events[1].trade is not None


def test_micro_backtester_mm_run() -> None:
    books = [_book(i, "99", "101") for i in range(0, 10, 2)]
    # trades que pegan el bid (sell agresivo a 99) luego el ask
    trades = [
        _trade(1, "99", "1", OrderSide.SELL),
        _trade(3, "99", "1", OrderSide.SELL),
        _trade(5, "101", "1", OrderSide.BUY),
        _trade(7, "101", "1", OrderSide.BUY),
        _trade(9, "99", "1", OrderSide.SELL),
    ]
    bt = MicroBacktester(MicroBacktestConfig(experiment_id="f7-mm", initial_cash=Decimal("100000")))
    result = bt.run(
        InventoryMMStrategy({"quantity": "1", "half_spread": "1", "max_pos": "5"}),
        trades=trades,
        books=books,
    )
    assert result.accounting.ok or len(result.simulation.portfolio_snapshots) == 0
    assert result.simulation.metadata["engine"] == "MicroSimulationEngine"
    assert "sharpe" in result.metrics.metrics
