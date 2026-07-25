"""Tests unitarios de SimpleMomentumStrategy (sin backtester)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from quantlab.core.contracts.strategy import StrategyContext
from quantlab.core.types.enums import (
    ClockMode,
    ClockSpeed,
    EventType,
    IntentType,
    OrderSide,
)
from quantlab.core.types.market import Bar, MarketEvent
from quantlab.core.types.portfolio import (
    Balance,
    PortfolioState,
    Position,
    SimulationClock,
)
from quantlab.research.strategies.simple_momentum import SimpleMomentumStrategy


def _ctx(
    *,
    portfolio: PortfolioState | None = None,
    now: datetime | None = None,
) -> StrategyContext:
    ts = now or datetime(2024, 6, 1, tzinfo=UTC)
    return StrategyContext(
        clock=SimulationClock(
            current_time=ts,
            mode=ClockMode.EVENT_DRIVEN,
            speed=ClockSpeed.ACCELERATED,
        ),
        portfolio_state=portfolio,
    )


def _bar(close: Decimal, *, i: int = 0, instrument_id: str = "MOM:TEST") -> Bar:
    t0 = datetime(2024, 6, 1, tzinfo=UTC) + timedelta(minutes=i)
    return Bar(
        instrument_id=instrument_id,
        open=close,
        high=close + Decimal("1"),
        low=close - Decimal("1"),
        close=close,
        volume=Decimal("10"),
        timestamp_open=t0,
        timestamp_close=t0 + timedelta(minutes=1),
        timeframe="1m",
    )


def _held(qty: Decimal, *, instrument_id: str = "MOM:TEST") -> PortfolioState:
    ts = datetime(2024, 6, 1, tzinfo=UTC)
    return PortfolioState(
        timestamp=ts,
        positions=(
            Position(
                instrument_id=instrument_id,
                quantity=qty,
                avg_entry_price=Decimal("100"),
                unrealized_pnl=Decimal("0"),
                realized_pnl=Decimal("0"),
                updated_at=ts,
            ),
        ),
        balances=(
            Balance(
                asset="USDT",
                available=Decimal("1000"),
                locked=Decimal("0"),
                total=Decimal("1000"),
                updated_at=ts,
            ),
        ),
        total_equity=Decimal("1000"),
        total_realized_pnl=Decimal("0"),
        total_unrealized_pnl=Decimal("0"),
    )


def test_warmup_emits_noop_until_lookback_plus_one() -> None:
    strat = SimpleMomentumStrategy({"lookback": 3, "quantity": "2"})
    ctx = _ctx()
    for i, c in enumerate((Decimal("10"), Decimal("11"), Decimal("12"))):
        intents = strat.on_bar(_bar(c, i=i), ctx)
        assert len(intents) == 1
        assert intents[0].intent_type is IntentType.NO_ACTION
        assert intents[0].intent_id == "noop-warmup"
    assert strat.get_state()["n_closes"] == 3


def test_buy_on_strict_up_window() -> None:
    strat = SimpleMomentumStrategy({"lookback": 2, "quantity": "3"})
    ctx = _ctx()
    closes = (Decimal("50"), Decimal("51"), Decimal("52"))
    for i, c in enumerate(closes[:-1]):
        assert strat.on_bar(_bar(c, i=i), ctx)[0].intent_type is IntentType.NO_ACTION
    buy = strat.on_bar(_bar(closes[-1], i=2), ctx)
    assert len(buy) == 1
    assert buy[0].intent_type is IntentType.PLACE_ORDER
    assert buy[0].side is OrderSide.BUY
    assert buy[0].quantity == Decimal("3")
    assert buy[0].intent_id == "mom-buy-3"
    assert strat.get_state()["position"] == "3"


def test_sell_on_strict_down_when_long() -> None:
    strat = SimpleMomentumStrategy({"lookback": 2, "quantity": "1"})
    # Subida → buy
    for i, c in enumerate((Decimal("100"), Decimal("101"), Decimal("102"))):
        strat.on_bar(_bar(c, i=i), _ctx())
    assert strat.get_state()["position"] == "1"
    # Baja dos pasos más para ventana estrictamente descendente
    noop = strat.on_bar(_bar(Decimal("101"), i=3), _ctx(portfolio=_held(Decimal("1"))))
    assert noop[0].intent_type is IntentType.NO_ACTION
    sell = strat.on_bar(_bar(Decimal("100"), i=4), _ctx(portfolio=_held(Decimal("1"))))
    assert sell[0].intent_type is IntentType.PLACE_ORDER
    assert sell[0].side is OrderSide.SELL
    assert sell[0].quantity == Decimal("1")
    assert sell[0].intent_id == "mom-sell-5"
    assert strat.get_state()["position"] == "0"


def test_long_only_no_short_on_down_without_position() -> None:
    strat = SimpleMomentumStrategy({"lookback": 2, "quantity": "1"})
    ctx = _ctx()
    intents = ()
    for i, c in enumerate((Decimal("90"), Decimal("89"), Decimal("88"))):
        intents = strat.on_bar(_bar(c, i=i), ctx)
    assert intents[0].intent_type is IntentType.NO_ACTION
    assert intents[0].intent_id == "noop"
    assert strat.get_state()["position"] == "0"


def test_reset_clears_closes_and_position() -> None:
    strat = SimpleMomentumStrategy({"lookback": 2, "quantity": "1"})
    for i, c in enumerate((Decimal("10"), Decimal("11"), Decimal("12"))):
        strat.on_bar(_bar(c, i=i), _ctx())
    assert strat.get_state()["n_closes"] == 3
    assert strat.get_state()["position"] == "1"
    strat.reset()
    assert strat.get_state() == {"position": "0", "n_closes": 0}
    # Tras reset vuelve a warmup
    again = strat.on_bar(_bar(Decimal("20"), i=0), _ctx())
    assert again[0].intent_id == "noop-warmup"


def test_on_event_is_noop() -> None:
    strat = SimpleMomentumStrategy()
    event = MarketEvent(
        event_id="e1",
        event_type=EventType.BAR,
        timestamp=datetime(2024, 6, 1, tzinfo=UTC),
        instrument_id="MOM:TEST",
    )
    assert strat.on_event(event, _ctx()) == ()
