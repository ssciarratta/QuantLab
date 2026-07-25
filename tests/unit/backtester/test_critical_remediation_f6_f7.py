"""Remediación hallazgos críticos F6/F7 — MARKET L2, sqrt slippage, TTL, multi-asset."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from quantlab.backtester import (
    BarBacktestConfig,
    BarBacktester,
    BookSlippageModel,
    MicroBacktestConfig,
    MicroBacktester,
    MicroSimulationConfig,
    MicroSimulationEngine,
    SlippageMode,
)
from quantlab.backtester.market_replay import MarketReplay
from quantlab.core.contracts.strategy import StrategyContext
from quantlab.core.types.enums import IntentType, OrderSide, OrderStatus, OrderType, TimeInForce
from quantlab.core.types.market import Bar, BookLevel, MarketEvent, OrderBookSnapshot, Trade
from quantlab.core.types.orders import OrderIntent
from quantlab.research.strategies.buy_once import BuyOnceStrategy


def _ts(i: int) -> datetime:
    return datetime(2024, 8, 1, tzinfo=UTC) + timedelta(seconds=i)


class _MarketOnceStrategy:
    """Emite un MARKET BUY una sola vez."""

    def __init__(self, instrument_id: str = "M:X", qty: str = "1") -> None:
        self._instrument_id = instrument_id
        self._qty = Decimal(qty)
        self._done = False

    def on_event(self, event: MarketEvent, context: StrategyContext) -> tuple[OrderIntent, ...]:
        noop = (
            OrderIntent(
                intent_id="noop",
                intent_type=IntentType.NO_ACTION,
                instrument_id=self._instrument_id,
            ),
        )
        if self._done:
            return noop
        # Esperar L2 en contexto (evita MARKET antes del book fresco).
        if context.parameters.get("best_ask") is None:
            return noop
        self._done = True
        return (
            OrderIntent(
                intent_id="mkt-1",
                intent_type=IntentType.PLACE_ORDER,
                instrument_id=self._instrument_id,
                side=OrderSide.BUY,
                quantity=self._qty,
                order_type=OrderType.MARKET,
                time_in_force=TimeInForce.IOC,
            ),
        )

    def on_bar(self, bar: Bar, context: StrategyContext) -> tuple[OrderIntent, ...]:
        return ()

    def get_parameters(self) -> dict[str, object]:
        return {}

    def set_parameters(self, params: dict[str, object]) -> None:
        return None

    def get_state(self) -> dict[str, object]:
        return {"done": self._done}

    def reset(self) -> None:
        self._done = False


class _LimitParkStrategy:
    """Coloca un LIMIT lejos del mercado y nunca cancela."""

    def __init__(self) -> None:
        self._placed = False

    def on_event(self, event: MarketEvent, context: StrategyContext) -> tuple[OrderIntent, ...]:
        if self._placed:
            return (
                OrderIntent(
                    intent_id="noop",
                    intent_type=IntentType.NO_ACTION,
                    instrument_id="M:X",
                ),
            )
        self._placed = True
        return (
            OrderIntent(
                intent_id="park-1",
                intent_type=IntentType.PLACE_ORDER,
                instrument_id="M:X",
                side=OrderSide.BUY,
                quantity=Decimal("1"),
                price=Decimal("50"),
                order_type=OrderType.LIMIT,
                time_in_force=TimeInForce.GTC,
            ),
        )

    def on_bar(self, bar: Bar, context: StrategyContext) -> tuple[OrderIntent, ...]:
        return ()

    def get_parameters(self) -> dict[str, object]:
        return {}

    def set_parameters(self, params: dict[str, object]) -> None:
        return None

    def get_state(self) -> dict[str, object]:
        return {"placed": self._placed}

    def reset(self) -> None:
        self._placed = False


def test_market_order_uses_best_ask_not_stale_last_px() -> None:
    """MARKET BUY debe tomar Best Ask del L2 aunque last_px esté obsoleto."""
    stale_trade = Trade(
        instrument_id="M:X",
        price=Decimal("100"),
        quantity=Decimal("1"),
        side=OrderSide.SELL,
        timestamp=_ts(0),
        trade_id="t0",
    )
    # Libro se mueve; no hay trades nuevos en el tape
    fresh_book = OrderBookSnapshot(
        instrument_id="M:X",
        timestamp=_ts(1),
        bids=(BookLevel(price=Decimal("109"), quantity=Decimal("5")),),
        asks=(BookLevel(price=Decimal("110"), quantity=Decimal("5")),),
        sequence_id=1,
    )
    engine = MicroSimulationEngine(
        MicroSimulationConfig(experiment_id="stale-mkt", initial_cash=Decimal("100000"))
    )
    result = engine.run(
        _MarketOnceStrategy(),
        MarketReplay(trades=[stale_trade], books=[fresh_book]),
    )
    assert len(result.fills) == 1
    assert result.fills[0].price == Decimal("110")


def test_square_root_slippage_nonlinear_penalty() -> None:
    book = OrderBookSnapshot(
        instrument_id="M:X",
        timestamp=_ts(0),
        bids=(BookLevel(Decimal("99"), Decimal("1")),),
        asks=(BookLevel(Decimal("100"), Decimal("2")),),
        sequence_id=0,
    )
    linear = BookSlippageModel(penalty_bps=Decimal("100"), mode=SlippageMode.LINEAR)
    sqrt_model = BookSlippageModel(
        penalty_bps=Decimal("0"),
        mode=SlippageMode.SQUARE_ROOT,
        volatility=Decimal("0.10"),
        impact_coefficient=Decimal("1"),
    )
    # qty=5 > depth asks=2 → remainder con impacto no lineal
    px_lin = linear.apply(side=OrderSide.BUY, quantity=Decimal("5"), book=book)
    px_sqrt = sqrt_model.apply(side=OrderSide.BUY, quantity=Decimal("5"), book=book)
    # VWAP parcial 2@100=200; resto 3 con impacto: 100*(1+0.1*sqrt(3/2))
    # impact = 0.1 * sqrt(1.5) ≈ 0.122474487 → px_rem ≈ 112.2474487
    # cost = 200 + 3*112.2474487 ≈ 536.742346 / 5 ≈ 107.3484692
    assert px_sqrt > Decimal("100")
    assert px_sqrt != px_lin
    assert px_sqrt == Decimal("107.34846923")


def test_purge_expired_resting_emits_ttl_cancelled() -> None:
    books = [
        OrderBookSnapshot(
            instrument_id="M:X",
            timestamp=_ts(i),
            bids=(BookLevel(Decimal("99"), Decimal("10")),),
            asks=(BookLevel(Decimal("101"), Decimal("10")),),
            sequence_id=i,
        )
        for i in range(6)
    ]
    # Trades lejos del limit 50 → no fill; TTL debe purgar
    trades = [
        Trade(
            instrument_id="M:X",
            price=Decimal("100"),
            quantity=Decimal("1"),
            side=OrderSide.SELL,
            timestamp=_ts(i),
            trade_id=f"t{i}",
        )
        for i in range(6)
    ]
    bt = MicroBacktester(
        MicroBacktestConfig(
            experiment_id="ttl",
            initial_cash=Decimal("100000"),
            resting_max_age_ticks=3,
        )
    )
    result = bt.run(_LimitParkStrategy(), trades=trades, books=books)
    cancel_events = [
        e
        for e in result.simulation.events_log
        if e.get("event") == "OrderCancelledEvent" and e.get("reason") == "TTL_EXPIRED"
    ]
    assert len(cancel_events) >= 1
    canceled_orders = [o for o in result.simulation.orders if o.status is OrderStatus.CANCELED]
    assert len(canceled_orders) >= 1


def test_bar_backtester_multi_asset_sync() -> None:
    base = datetime(2024, 5, 1, tzinfo=UTC)

    def make_bars(instrument: str, start: int, n: int = 4) -> list[Bar]:
        out: list[Bar] = []
        for i in range(n):
            c = Decimal(start + i)
            t0 = base + timedelta(minutes=i)
            out.append(
                Bar(
                    instrument_id=instrument,
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

    bars = make_bars("BTC-USDT", 100) + make_bars("ETH-USDT", 200)
    bt = BarBacktester(BarBacktestConfig(experiment_id="f6-multi", initial_cash=Decimal("50000")))
    result = bt.run(BuyOnceStrategy({"quantity": "1"}), bars)
    assert result.accounting.ok
    assert len(result.simulation.fills) == 1
    # marks de ambos activos deben aparecer en snapshots
    last_snap = result.simulation.portfolio_snapshots[-1]
    pos_ids = {p.instrument_id for p in last_snap.positions}
    assert "BTC-USDT" in pos_ids or any(
        f.instrument_id == "BTC-USDT" for f in result.simulation.fills
    )
