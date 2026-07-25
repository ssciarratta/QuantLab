"""Tests del MetricsEngine Fase 4."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from quantlab.core.types.enums import (
    FeeType,
    LiquidityType,
    OrderSide,
    OrderStatus,
    OrderType,
    TimeInForce,
)
from quantlab.core.types.orders import Fee, Fill, Order
from quantlab.core.types.results import EquityPoint, SimulationResult
from quantlab.metrics import METRICS_VERSION, MetricsEngine
from quantlab.metrics.engine import calmar_ratio, max_drawdown, sharpe_ratio, sortino_ratio


def test_max_drawdown_and_sharpe() -> None:
    curve = (
        EquityPoint(datetime(2024, 1, 1, tzinfo=UTC), Decimal("100")),
        EquityPoint(datetime(2024, 1, 2, tzinfo=UTC), Decimal("110")),
        EquityPoint(datetime(2024, 1, 3, tzinfo=UTC), Decimal("90")),
        EquityPoint(datetime(2024, 1, 4, tzinfo=UTC), Decimal("95")),
    )
    assert abs(max_drawdown(curve) - (20 / 110)) < 1e-9
    assert isinstance(sharpe_ratio((0.01, -0.02, 0.015, 0.0)), float)
    assert isinstance(sortino_ratio((0.01, -0.02, 0.015, 0.0)), float)
    assert isinstance(calmar_ratio(curve), float)


def test_metrics_engine_from_simulation() -> None:
    ts = datetime(2024, 1, 1, tzinfo=UTC)
    ts2 = datetime(2024, 1, 2, tzinfo=UTC)
    order = Order(
        order_id="o1",
        client_order_id="c1",
        instrument_id="x",
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
        amount=Decimal("0"),
        currency="USDT",
        fee_type=FeeType.TAKER,
    )
    fill = Fill(
        fill_id="fl1",
        order_id="o1",
        instrument_id="x",
        price=Decimal("10"),
        quantity=Decimal("1"),
        fee=fee,
        timestamp=ts,
        liquidity=LiquidityType.TAKER,
    )
    result = SimulationResult(
        experiment_id="e1",
        equity_curve=(
            EquityPoint(ts, Decimal("100")),
            EquityPoint(ts2, Decimal("105")),
        ),
        fills=(fill,),
        orders=(order,),
        portfolio_snapshots=(),
        events_log=(),
        metadata={},
    )
    metrics = MetricsEngine().compute(result)
    assert metrics.metrics_version == METRICS_VERSION
    assert "sharpe" in metrics.metrics
    assert "sortino" in metrics.metrics
    assert "calmar" in metrics.metrics
    assert "max_drawdown" in metrics.metrics
    assert "win_rate" in metrics.metrics
    assert "profit_factor" in metrics.metrics
    # metadata frozen
    with __import__("pytest").raises(TypeError):
        metrics.metrics["sharpe"] = 0  # type: ignore[index]


def test_open_position_mtm_in_win_rate() -> None:
    """Posición abierta BUY se valúa MTM al cierre vía snapshot (unrealized > 0)."""
    from quantlab.core.types.portfolio import Balance, PortfolioState, Position
    from quantlab.metrics.engine import win_rate_and_profit_factor

    ts = datetime(2024, 1, 1, tzinfo=UTC)
    ts2 = datetime(2024, 1, 2, tzinfo=UTC)
    order = Order(
        order_id="o1",
        client_order_id="c1",
        instrument_id="x",
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
        amount=Decimal("0"),
        currency="USDT",
        fee_type=FeeType.TAKER,
    )
    fill = Fill(
        fill_id="fl1",
        order_id="o1",
        instrument_id="x",
        price=Decimal("10"),
        quantity=Decimal("1"),
        fee=fee,
        timestamp=ts,
        liquidity=LiquidityType.TAKER,
    )
    snap = PortfolioState(
        timestamp=ts2,
        positions=(
            Position(
                instrument_id="x",
                quantity=Decimal("1"),
                avg_entry_price=Decimal("10"),
                unrealized_pnl=Decimal("5"),
                realized_pnl=Decimal("0"),
                updated_at=ts2,
            ),
        ),
        balances=(
            Balance(
                asset="USDT",
                available=Decimal("90"),
                locked=Decimal("0"),
                total=Decimal("90"),
                updated_at=ts2,
            ),
        ),
        total_equity=Decimal("105"),
        total_realized_pnl=Decimal("0"),
        total_unrealized_pnl=Decimal("5"),
    )
    result = SimulationResult(
        experiment_id="e-open",
        equity_curve=(
            EquityPoint(ts, Decimal("100")),
            EquityPoint(ts2, Decimal("105")),
        ),
        fills=(fill,),
        orders=(order,),
        portfolio_snapshots=(snap,),
        events_log=(),
    )
    wr, pf = win_rate_and_profit_factor(result)
    assert wr == 1.0
    assert pf == 999.0
