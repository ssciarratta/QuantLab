"""Motor de simulación microestructura 5B (trades + resting orders)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from quantlab.backtester.inventory import InventoryTracker
from quantlab.backtester.market_replay import MarketReplay, ReplayEvent
from quantlab.backtester.partial_fill import PartialFillModel, RestingOrder
from quantlab.core.contracts.strategy import Strategy, StrategyContext
from quantlab.core.types.enums import (
    ClockMode,
    ClockSpeed,
    IntentType,
    LiquidityType,
    OrderSide,
    OrderStatus,
    OrderType,
)
from quantlab.core.types.market import MarketEvent, OrderBookSnapshot
from quantlab.core.types.orders import Fee, Fill, Order, OrderIntent
from quantlab.core.types.portfolio import SimulationClock
from quantlab.core.types.results import EquityPoint, SimulationResult
from quantlab.execution.fees import MakerTakerFeeModel, ZeroFeeModel
from quantlab.execution.protocols import FeeModel
from quantlab.simulation.portfolio_tracker import PortfolioTracker


@dataclass(frozen=True, slots=True)
class OrderCancelledEvent:
    """Cancelación explícita (TTL / estrategia) para contabilidad de órdenes."""

    order_id: str
    reason: str
    timestamp: datetime
    client_order_id: str | None = None


@dataclass(frozen=True, slots=True)
class MicroSimulationConfig:
    experiment_id: str
    initial_cash: Decimal = Decimal("100000")
    cash_asset: str = "USDT"
    max_abs_inventory: Decimal = Decimal("100")
    schema_version: str = "1.0"
    # None = sin TTL; N = purgar resting con edad > N ticks de replay
    resting_max_age_ticks: int | None = None


@dataclass
class MicroSimulationEngine:
    """Ejecuta Strategy sobre MarketReplay (trades); soporta cancel/replace/partial."""

    config: MicroSimulationConfig
    fill_model: PartialFillModel = field(default_factory=PartialFillModel)
    fee_model: FeeModel | None = None

    def __post_init__(self) -> None:
        if self.fee_model is None:
            self.fee_model = MakerTakerFeeModel(maker_bps=Decimal("2"), taker_bps=Decimal("5"))
        self._seq = 0
        self._tick = 0
        self._resting: dict[str, RestingOrder] = {}
        self._client_to_order: dict[str, str] = {}

    def run(self, strategy: Strategy, replay: MarketReplay) -> SimulationResult:
        strategy.reset()
        self._seq = 0
        self._tick = 0
        self._resting.clear()
        self._client_to_order.clear()
        tracker = PortfolioTracker(cash_asset=self.config.cash_asset, cash=self.config.initial_cash)
        inventory = InventoryTracker(max_abs_position=self.config.max_abs_inventory)
        fills: list[Fill] = []
        orders: list[Order] = []
        equity_curve: list[EquityPoint] = []
        snapshots = []
        events_log: list[dict[str, object]] = []
        last_books: dict[str, OrderBookSnapshot] = {}
        last_px: dict[str, Decimal] = {}
        marks: dict[str, Decimal] = {}

        for ev in replay:
            self._tick += 1
            # Actualizar estado de mercado ANTES de match/estrategia (evita stale book).
            if ev.book is not None:
                last_books[ev.book.instrument_id] = ev.book
                mid = _book_mid(ev.book)
                if mid is not None:
                    marks[ev.book.instrument_id] = mid
            if ev.trade is not None:
                last_px[ev.trade.instrument_id] = ev.trade.price
                marks[ev.trade.instrument_id] = ev.trade.price

            self.purge_expired_resting_orders(
                max_age_ticks=self.config.resting_max_age_ticks,
                timestamp=ev.timestamp,
                orders=orders,
                events_log=events_log,
            )
            self._on_market(
                ev,
                strategy=strategy,
                tracker=tracker,
                inventory=inventory,
                fills=fills,
                orders=orders,
                events_log=events_log,
                last_books=last_books,
                last_px=last_px,
                marks=marks,
            )
            if marks:
                snap = tracker.mark_equity(marks, ev.timestamp)
                snapshots.append(snap)
                point = EquityPoint(timestamp=ev.timestamp, equity=snap.total_equity)
                if equity_curve and equity_curve[-1].timestamp == point.timestamp:
                    equity_curve[-1] = point
                else:
                    equity_curve.append(point)

        return SimulationResult(
            experiment_id=self.config.experiment_id,
            equity_curve=tuple(equity_curve),
            fills=tuple(fills),
            orders=tuple(orders),
            portfolio_snapshots=tuple(snapshots),
            events_log=tuple(events_log),
            metadata={
                "engine": "MicroSimulationEngine",
                "schema_version": self.config.schema_version,
                "fill_model": self.fill_model.model_id,
                "fee_model": getattr(self.fee_model, "model_id", "fee"),
                "inventory_final": str(inventory.position),
                "inventory_realized": str(inventory.realized_pnl),
                "initial_cash": str(self.config.initial_cash),
                "resting_max_age_ticks": self.config.resting_max_age_ticks,
                "completed_at": datetime.now(tz=UTC).isoformat(),
            },
        )

    def purge_expired_resting_orders(
        self,
        *,
        max_age_ticks: int | None,
        timestamp: datetime,
        orders: list[Order],
        events_log: list[dict[str, object]],
    ) -> list[OrderCancelledEvent]:
        """Elimina resting con edad > max_age_ticks; emite OrderCancelledEvent TTL_EXPIRED."""
        if max_age_ticks is None or max_age_ticks < 0:
            return []
        cancelled: list[OrderCancelledEvent] = []
        for oid in list(self._resting.keys()):
            resting = self._resting[oid]
            age = self._tick - resting.created_tick
            if age <= max_age_ticks:
                continue
            del self._resting[oid]
            client = resting.intent.intent_id
            evt = OrderCancelledEvent(
                order_id=oid,
                reason="TTL_EXPIRED",
                timestamp=timestamp,
                client_order_id=client,
            )
            cancelled.append(evt)
            events_log.append(
                {
                    "event": "OrderCancelledEvent",
                    "order_id": evt.order_id,
                    "reason": evt.reason,
                    "timestamp": evt.timestamp.isoformat(),
                    "client_order_id": evt.client_order_id,
                }
            )
            self._mark_order_canceled(orders, oid, timestamp)
        return cancelled

    def _on_market(
        self,
        ev: ReplayEvent,
        *,
        strategy: Strategy,
        tracker: PortfolioTracker,
        inventory: InventoryTracker,
        fills: list[Fill],
        orders: list[Order],
        events_log: list[dict[str, object]],
        last_books: dict[str, OrderBookSnapshot],
        last_px: dict[str, Decimal],
        marks: dict[str, Decimal],
    ) -> None:
        # 1) Match resting vs trade
        if ev.trade is not None:
            for oid in list(self._resting.keys()):
                resting = self._resting[oid]
                decision = self.fill_model.match_trade(resting, ev.trade)
                if not decision.filled or decision.fill_qty <= 0:
                    continue
                self._apply_partial(
                    resting=resting,
                    decision_qty=decision.fill_qty,
                    price=decision.fill_price or ev.trade.price,
                    maker=decision.liquidity_maker,
                    timestamp=ev.timestamp,
                    tracker=tracker,
                    inventory=inventory,
                    fills=fills,
                    orders=orders,
                    events_log=events_log,
                )

        # 2) Strategy
        instrument = (
            ev.trade.instrument_id
            if ev.trade
            else (ev.book.instrument_id if ev.book else "UNKNOWN")
        )
        book = last_books.get(instrument)
        clock = SimulationClock(
            current_time=ev.timestamp,
            mode=ClockMode.EVENT_DRIVEN,
            speed=ClockSpeed.ACCELERATED,
        )
        portfolio = tracker.mark_equity(marks, ev.timestamp) if marks else None
        ctx = StrategyContext(
            clock=clock,
            portfolio_state=portfolio,
            parameters={
                **strategy.get_parameters(),
                "inventory": str(inventory.position),
                "inventory_skew": str(inventory.skew_bias()),
                "best_bid": (str(book.bids[0].price) if book and book.bids else None),
                "best_ask": (str(book.asks[0].price) if book and book.asks else None),
            },
        )
        market_event = MarketEvent(
            event_id=self._next_id("evt"),
            event_type=ev.event_type,
            timestamp=ev.timestamp,
            instrument_id=instrument,
            payload={"inventory": str(inventory.position)},
        )
        intents = strategy.on_event(market_event, ctx)
        for intent in intents:
            self._handle_intent(
                intent,
                timestamp=ev.timestamp,
                tracker=tracker,
                inventory=inventory,
                fills=fills,
                orders=orders,
                events_log=events_log,
                last_books=last_books,
                last_px=last_px,
            )

    def _handle_intent(
        self,
        intent: OrderIntent,
        *,
        timestamp: datetime,
        tracker: PortfolioTracker,
        inventory: InventoryTracker,
        fills: list[Fill],
        orders: list[Order],
        events_log: list[dict[str, object]],
        last_books: dict[str, OrderBookSnapshot],
        last_px: dict[str, Decimal],
    ) -> None:
        if intent.intent_type is IntentType.NO_ACTION:
            return
        if intent.intent_type is IntentType.CANCEL_ORDER:
            target = intent.replace_target_id or ""
            oid = self._client_to_order.get(target)
            if oid and oid in self._resting:
                del self._resting[oid]
                events_log.append(
                    {
                        "event": "OrderCancelledEvent",
                        "order_id": oid,
                        "reason": "CLIENT_CANCEL",
                        "timestamp": timestamp.isoformat(),
                        "client_order_id": target,
                    }
                )
                self._mark_order_canceled(orders, oid, timestamp)
            else:
                events_log.append({"cancel_miss": target})
            return
        if intent.intent_type is IntentType.REPLACE_ORDER:
            target = intent.replace_target_id or ""
            oid = self._client_to_order.get(target)
            if oid and oid in self._resting:
                del self._resting[oid]
                events_log.append({"replaced": oid})
            # cae a place con nuevo intent
        if intent.intent_type in (IntentType.PLACE_ORDER, IntentType.REPLACE_ORDER):
            if intent.side is None or intent.quantity is None:
                return
            if not inventory.can_increase(intent.side, intent.quantity):
                events_log.append({"rejected": intent.intent_id, "reason": "inventory_limit"})
                return
            order_id = self._next_id("ord")
            self._resting[order_id] = RestingOrder(
                order_id=order_id,
                intent=intent,
                remaining=intent.quantity,
                created_tick=self._tick,
            )
            self._client_to_order[intent.intent_id] = order_id
            orders.append(
                Order(
                    order_id=order_id,
                    client_order_id=intent.intent_id,
                    instrument_id=intent.instrument_id,
                    side=intent.side,
                    order_type=intent.order_type or OrderType.LIMIT,
                    quantity=intent.quantity,
                    filled_quantity=Decimal("0"),
                    price=intent.price,
                    status=OrderStatus.OPEN,
                    created_at=timestamp,
                    updated_at=timestamp,
                    time_in_force=intent.time_in_force,
                )
            )
            events_log.append({"resting": order_id, "client": intent.intent_id})
            # MARKET: L2 Best Bid/Ask primero; last_px solo fallback
            if intent.order_type is OrderType.MARKET:
                ref = _market_ref_price(
                    instrument_id=intent.instrument_id,
                    side=intent.side,
                    last_books=last_books,
                    last_px=last_px,
                )
                if ref is None:
                    events_log.append(
                        {"skipped_market": order_id, "reason": "no_ref_price"}
                    )
                    return
                from quantlab.core.types.market import Trade

                synthetic = Trade(
                    instrument_id=intent.instrument_id,
                    price=ref,
                    quantity=intent.quantity,
                    side=intent.side,
                    timestamp=timestamp,
                    trade_id=self._next_id("syn"),
                )
                resting = self._resting[order_id]
                decision = self.fill_model.match_trade(resting, synthetic)
                if decision.filled and decision.fill_qty > 0:
                    self._apply_partial(
                        resting=resting,
                        decision_qty=decision.fill_qty,
                        price=decision.fill_price or synthetic.price,
                        maker=False,
                        timestamp=timestamp,
                        tracker=tracker,
                        inventory=inventory,
                        fills=fills,
                        orders=orders,
                        events_log=events_log,
                    )

    def _apply_partial(
        self,
        *,
        resting: RestingOrder,
        decision_qty: Decimal,
        price: Decimal,
        maker: bool,
        timestamp: datetime,
        tracker: PortfolioTracker,
        inventory: InventoryTracker,
        fills: list[Fill],
        orders: list[Order],
        events_log: list[dict[str, object]],
    ) -> None:
        intent = resting.intent
        assert intent.side is not None
        liquidity = LiquidityType.MAKER if maker else LiquidityType.TAKER
        fee_model = self.fee_model or ZeroFeeModel()
        assessment = fee_model.assess(
            side=intent.side,
            price=price,
            quantity=decision_qty,
            liquidity=liquidity,
        )
        if not tracker.can_afford(
            intent.side, intent.instrument_id, decision_qty, price, fee=assessment.amount
        ):
            events_log.append({"skipped_fill": resting.order_id, "reason": "insufficient"})
            return
        if not inventory.can_increase(intent.side, decision_qty):
            events_log.append({"skipped_fill": resting.order_id, "reason": "inventory_limit"})
            return
        fee_amt = tracker.apply_fill(
            instrument_id=intent.instrument_id,
            side=intent.side,
            quantity=decision_qty,
            price=price,
            fee=assessment.amount,
        )
        inventory.apply(intent.side, decision_qty, price)
        resting.remaining -= decision_qty
        fill_id = self._next_id("fill")
        fills.append(
            Fill(
                fill_id=fill_id,
                order_id=resting.order_id,
                instrument_id=intent.instrument_id,
                price=price,
                quantity=decision_qty,
                fee=Fee(
                    fee_id=self._next_id("fee"),
                    fill_id=fill_id,
                    amount=fee_amt,
                    currency=self.config.cash_asset,
                    fee_type=assessment.fee_type,
                ),
                timestamp=timestamp,
                liquidity=liquidity,
            )
        )
        for i, o in enumerate(orders):
            if o.order_id == resting.order_id:
                filled = o.filled_quantity + decision_qty
                status = OrderStatus.FILLED if resting.remaining <= 0 else OrderStatus.PARTIAL
                orders[i] = Order(
                    order_id=o.order_id,
                    client_order_id=o.client_order_id,
                    instrument_id=o.instrument_id,
                    side=o.side,
                    order_type=o.order_type,
                    quantity=o.quantity,
                    filled_quantity=filled,
                    price=o.price,
                    status=status,
                    created_at=o.created_at,
                    updated_at=timestamp,
                    time_in_force=o.time_in_force,
                )
                break
        if resting.remaining <= 0:
            self._resting.pop(resting.order_id, None)
        events_log.append(
            {
                "partial_fill": resting.order_id,
                "qty": str(decision_qty),
                "remaining": str(resting.remaining),
            }
        )

    def _mark_order_canceled(
        self, orders: list[Order], order_id: str, timestamp: datetime
    ) -> None:
        for i, o in enumerate(orders):
            if o.order_id == order_id and o.status not in (
                OrderStatus.FILLED,
                OrderStatus.CANCELED,
            ):
                orders[i] = Order(
                    order_id=o.order_id,
                    client_order_id=o.client_order_id,
                    instrument_id=o.instrument_id,
                    side=o.side,
                    order_type=o.order_type,
                    quantity=o.quantity,
                    filled_quantity=o.filled_quantity,
                    price=o.price,
                    status=OrderStatus.CANCELED,
                    created_at=o.created_at,
                    updated_at=timestamp,
                    time_in_force=o.time_in_force,
                )
                break

    def _next_id(self, prefix: str) -> str:
        self._seq += 1
        return f"{prefix}-{self._seq:06d}"


def _book_mid(book: OrderBookSnapshot) -> Decimal | None:
    if book.bids and book.asks:
        return (book.bids[0].price + book.asks[0].price) / Decimal("2")
    if book.bids:
        return book.bids[0].price
    if book.asks:
        return book.asks[0].price
    return None


def _market_ref_price(
    *,
    instrument_id: str,
    side: OrderSide,
    last_books: dict[str, OrderBookSnapshot],
    last_px: dict[str, Decimal],
) -> Decimal | None:
    """Best Ask (BUY) / Best Bid (SELL) del L2; fallback a last_px."""
    book = last_books.get(instrument_id)
    if book is not None:
        if side is OrderSide.BUY and book.asks:
            return book.asks[0].price
        if side is OrderSide.SELL and book.bids:
            return book.bids[0].price
    return last_px.get(instrument_id)
