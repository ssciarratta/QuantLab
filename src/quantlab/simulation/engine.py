"""Motor de simulación bar-based / event-driven (Fase 4 + políticas F5 opcionales)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from quantlab.core.contracts.strategy import Strategy, StrategyContext
from quantlab.core.types.enums import (
    ClockMode,
    ClockSpeed,
    EventType,
    IntentType,
    LiquidityType,
    OrderStatus,
    OrderType,
)
from quantlab.core.types.market import Bar, MarketEvent
from quantlab.core.types.orders import Fee, Fill, Order, OrderIntent
from quantlab.core.types.portfolio import PortfolioState, SimulationClock
from quantlab.core.types.results import EquityPoint, SimulationResult
from quantlab.execution.fees import ProportionalFeeModel, ZeroFeeModel
from quantlab.execution.latency import ZeroLatencyModel
from quantlab.execution.protocols import FeeModel, LatencyModel, SlippageModel
from quantlab.execution.slippage import NoSlippageModel
from quantlab.simulation.fill_model import ImmediateBarFillModel
from quantlab.simulation.portfolio_tracker import PortfolioTracker


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    """Parámetros del motor (inmutable)."""

    experiment_id: str
    initial_cash: Decimal = Decimal("100000")
    cash_asset: str = "USDT"
    fee_rate: Decimal = Decimal("0")
    schema_version: str = "1.0"


@dataclass(frozen=True, slots=True)
class _PendingIntent:
    intent: OrderIntent
    effective_index: int


class BarSimulationEngine:
    """Ejecuta Strategy sobre una secuencia de barras y produce SimulationResult."""

    def __init__(
        self,
        config: SimulationConfig,
        *,
        fill_model: ImmediateBarFillModel | None = None,
        slippage_model: SlippageModel | None = None,
        latency_model: LatencyModel | None = None,
        fee_model: FeeModel | None = None,
    ) -> None:
        self._config = config
        self._fill_model = fill_model or ImmediateBarFillModel()
        self._slippage = slippage_model or NoSlippageModel()
        self._latency = latency_model or ZeroLatencyModel()
        if fee_model is not None:
            self._fee = fee_model
        elif config.fee_rate > 0:
            self._fee = ProportionalFeeModel(rate=config.fee_rate)
        else:
            self._fee = ZeroFeeModel()
        self._seq = 0

    def run(self, strategy: Strategy, bars: Sequence[Bar]) -> SimulationResult:
        strategy.reset()
        tracker = PortfolioTracker(
            cash_asset=self._config.cash_asset,
            cash=self._config.initial_cash,
            fee_rate=self._config.fee_rate,
        )
        fills: list[Fill] = []
        orders: list[Order] = []
        equity_curve: list[EquityPoint] = []
        snapshots: list[PortfolioState] = []
        events_log: list[dict[str, object]] = []
        marks: dict[str, Decimal] = {}
        pending: list[_PendingIntent] = []
        bar_list = list(bars)
        n = len(bar_list)

        for idx, bar in enumerate(bar_list):
            marks[bar.instrument_id] = bar.close

            # Fills diferidos (latencia) ANTES del contexto de estrategia
            due = [p for p in pending if p.effective_index == idx]
            pending = [p for p in pending if p.effective_index != idx]
            for item in due:
                self._try_fill(
                    intent=item.intent,
                    bar=bar,
                    tracker=tracker,
                    fills=fills,
                    orders=orders,
                    events_log=events_log,
                )

            clock = SimulationClock(
                current_time=bar.timestamp_close,
                mode=ClockMode.EVENT_DRIVEN,
                speed=ClockSpeed.ACCELERATED,
            )
            portfolio = tracker.mark_equity(marks, bar.timestamp_close)
            ctx = StrategyContext(
                clock=clock,
                portfolio_state=portfolio,
                parameters=strategy.get_parameters(),
            )
            event = MarketEvent(
                event_id=self._next_id("evt"),
                event_type=EventType.BAR,
                timestamp=bar.timestamp_close,
                instrument_id=bar.instrument_id,
                payload={"timeframe": bar.timeframe, "close": str(bar.close)},
            )

            intents = strategy.on_event(event, ctx)
            if not intents:
                intents = strategy.on_bar(bar, ctx)

            for intent in intents:
                events_log.append(
                    {
                        "bar_ts": bar.timestamp_close.isoformat(),
                        "intent_id": intent.intent_id,
                        "intent_type": intent.intent_type.value,
                        "submit_index": idx,
                    }
                )
                if intent.intent_type is not IntentType.PLACE_ORDER:
                    continue
                latency = self._latency.resolve(
                    submit_index=idx,
                    submit_time=bar.timestamp_close,
                    series_length=n,
                )
                if not latency.executable or latency.effective_index is None:
                    events_log.append(
                        {
                            "skipped": intent.intent_id,
                            "reason": latency.reason,
                        }
                    )
                    continue
                if latency.effective_index == idx:
                    self._try_fill(
                        intent=intent,
                        bar=bar,
                        tracker=tracker,
                        fills=fills,
                        orders=orders,
                        events_log=events_log,
                    )
                else:
                    pending.append(
                        _PendingIntent(intent=intent, effective_index=latency.effective_index)
                    )
                    events_log.append(
                        {
                            "queued": intent.intent_id,
                            "effective_index": latency.effective_index,
                            "latency": self._latency.model_id,
                        }
                    )

            snap = tracker.mark_equity(marks, bar.timestamp_close)
            snapshots.append(snap)
            point = EquityPoint(timestamp=bar.timestamp_close, equity=snap.total_equity)
            if equity_curve and equity_curve[-1].timestamp == point.timestamp:
                equity_curve[-1] = point
            else:
                equity_curve.append(point)

        return SimulationResult(
            experiment_id=self._config.experiment_id,
            equity_curve=tuple(equity_curve),
            fills=tuple(fills),
            orders=tuple(orders),
            portfolio_snapshots=tuple(snapshots),
            events_log=tuple(events_log),
            metadata={
                "engine": "BarSimulationEngine",
                "schema_version": self._config.schema_version,
                "fill_model": getattr(
                    self._fill_model, "model_id", type(self._fill_model).__name__
                ),
                "slippage_model": self._slippage.model_id,
                "latency_model": self._latency.model_id,
                "fee_model": self._fee.model_id,
                "bars": len(bar_list),
                "initial_cash": str(self._config.initial_cash),
                "completed_at": datetime.now(tz=UTC).isoformat(),
            },
        )

    def _try_fill(
        self,
        *,
        intent: OrderIntent,
        bar: Bar,
        tracker: PortfolioTracker,
        fills: list[Fill],
        orders: list[Order],
        events_log: list[dict[str, object]],
    ) -> None:
        decision = self._fill_model.evaluate(intent, bar)
        if not decision.filled or decision.price is None or decision.quantity is None:
            events_log.append({"skipped": intent.intent_id, "reason": decision.reason})
            return
        assert intent.side is not None
        fill_price = self._slippage.apply(
            side=intent.side,
            price=decision.price,
            quantity=decision.quantity,
            bar=bar,
        )
        liquidity = LiquidityType.TAKER
        assessment = self._fee.assess(
            side=intent.side,
            price=fill_price,
            quantity=decision.quantity,
            liquidity=liquidity,
        )
        if not tracker.can_afford(
            intent.side,
            intent.instrument_id,
            decision.quantity,
            fill_price,
            fee=assessment.amount,
        ):
            events_log.append({"skipped": intent.intent_id, "reason": "insufficient"})
            return
        fee_amt = tracker.apply_fill(
            instrument_id=intent.instrument_id,
            side=intent.side,
            quantity=decision.quantity,
            price=fill_price,
            fee=assessment.amount,
        )
        order_id = self._next_id("ord")
        fill_id = self._next_id("fill")
        now = bar.timestamp_close
        order = Order(
            order_id=order_id,
            client_order_id=intent.intent_id,
            instrument_id=intent.instrument_id,
            side=intent.side,
            order_type=intent.order_type or OrderType.LIMIT,
            quantity=decision.quantity,
            filled_quantity=decision.quantity,
            price=(intent.price if intent.order_type is OrderType.LIMIT else None),
            status=OrderStatus.FILLED,
            created_at=now,
            updated_at=now,
            time_in_force=intent.time_in_force,
        )
        fee = Fee(
            fee_id=self._next_id("fee"),
            fill_id=fill_id,
            amount=fee_amt,
            currency=self._config.cash_asset,
            fee_type=assessment.fee_type,
        )
        fill = Fill(
            fill_id=fill_id,
            order_id=order_id,
            instrument_id=intent.instrument_id,
            price=fill_price,
            quantity=decision.quantity,
            fee=fee,
            timestamp=now,
            liquidity=liquidity,
        )
        orders.append(order)
        fills.append(fill)

    def _next_id(self, prefix: str) -> str:
        self._seq += 1
        return f"{prefix}-{self._seq:06d}-{uuid4().hex[:8]}"
