"""Paper Session Runner — estrategia → intents → risk → PaperBroker (F26).

Nunca envía órdenes a venue LIVE. Solo ``PaperBroker.submit`` (fills locales).
Constructor fail-closed si el broker no es ``PaperBroker``.
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from quantlab.brokers.paper.book import PaperBook
from quantlab.brokers.paper.broker import PaperBroker
from quantlab.brokers.types import BrokerAck, BrokerSnapshot
from quantlab.core.contracts.strategy import StrategyContext
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import ClockMode, ClockSpeed, EventType, IntentType
from quantlab.core.types.market import Bar, MarketEvent
from quantlab.core.types.orders import OrderIntent
from quantlab.core.types.portfolio import Balance, PortfolioState, Position, SimulationClock
from quantlab.core.types.serialization import dataclass_to_dict, to_jsonable
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.research.strategies.buy_once import BuyOnceStrategy
from quantlab.research.strategies.dummy_strategy import DummyStrategy
from quantlab.research.strategies.simple_momentum import SimpleMomentumStrategy
from quantlab.workbench.risk import PaperRiskLimits

SESSION_STRATEGY_IDS: tuple[str, ...] = ("dummy", "buy_once", "momentum", "simple_momentum")


@dataclass(frozen=True, slots=True)
class PaperSessionConfig:
    """Configuración de una sesión paper operativa."""

    strategy_id: str
    symbol: str
    max_steps: int = 100
    interval_ms: int | None = None
    params: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.strategy_id.strip():
            raise ValidationError("strategy_id requerido")
        if not self.symbol.strip():
            raise ValidationError("symbol requerido")
        if self.max_steps < 1 or self.max_steps > 10_000:
            raise ValidationError("max_steps debe estar entre 1 y 10000")
        if self.interval_ms is not None and self.interval_ms < 1:
            raise ValidationError("interval_ms debe ser >= 1")
        object.__setattr__(self, "params", dict(self.params))


def build_session_strategy(strategy_id: str, params: Mapping[str, Any] | None = None) -> Any:
    """Factory de estrategias research para sesión paper."""
    sid = strategy_id.strip().lower()
    strategy_params = dict(params or {})
    if sid == "dummy":
        if "quantity" not in strategy_params:
            strategy_params["quantity"] = "0.01"
        if "price" not in strategy_params:
            strategy_params["price"] = "100.0"
        return DummyStrategy(strategy_params)
    if sid == "buy_once":
        if "quantity" not in strategy_params:
            strategy_params["quantity"] = "1"
        return BuyOnceStrategy(strategy_params)
    if sid in ("momentum", "simple_momentum"):
        if "quantity" not in strategy_params:
            strategy_params["quantity"] = "1"
        if "lookback" not in strategy_params:
            strategy_params["lookback"] = 3
        return SimpleMomentumStrategy(strategy_params)
    raise ValidationError(
        f"strategy_id desconocido: {strategy_id!r}; disponibles: dummy, buy_once, momentum"
    )


def _mark_from_snapshot(snapshot: BrokerSnapshot) -> Decimal:
    if snapshot.bid > 0 and snapshot.ask > 0:
        return (snapshot.bid + snapshot.ask) / Decimal("2")
    if snapshot.last > 0:
        return snapshot.last
    if snapshot.ask > 0:
        return snapshot.ask
    if snapshot.bid > 0:
        return snapshot.bid
    raise ValidationError(f"snapshot sin precio usable: {snapshot.symbol}")


def snapshot_to_bar(
    snapshot: BrokerSnapshot,
    *,
    timeframe: str = "1m",
    step_index: int = 0,
) -> Bar:
    """Barra OHLCV trivial desde last/mid del snapshot (buffer sintético)."""
    px = _mark_from_snapshot(snapshot)
    ts_close = snapshot.ts if snapshot.ts.tzinfo is not None else snapshot.ts.replace(tzinfo=UTC)
    # Desplazar levemente para series crecientes de timestamps por step.
    ts_close = ts_close + timedelta(minutes=step_index)
    ts_open = ts_close - timedelta(minutes=1)
    return Bar(
        instrument_id=snapshot.symbol,
        open=px,
        high=px,
        low=px,
        close=px,
        volume=Decimal("1"),
        timestamp_open=ts_open,
        timestamp_close=ts_close,
        timeframe=timeframe,
    )


class PaperSessionRunner:
    """Loop paper: MD snapshot → strategy → risk → broker.submit.

    Background opcional (``interval_ms``): thread daemon cancelable vía ``stop()``.
    En tests preferir ``step()`` manual.
    """

    def __init__(
        self,
        broker: PaperBroker,
        risk: PaperRiskLimits,
        book: PaperBook,
        *,
        on_book_persist: Callable[[], None] | None = None,
    ) -> None:
        if not LIVE_BLOCKED:
            raise ValidationError("LIVE_BLOCKED debe ser True; PaperSessionRunner aborta")
        # Fail-closed: solo PaperBroker (nunca BrokerPort venue / MD-only con submit).
        if not isinstance(broker, PaperBroker):
            raise ValidationError(
                "PaperSessionRunner requiere PaperBroker "
                "(nunca place_order / submit venue)"
            )
        self._broker = broker
        self._risk = risk
        self._book = book
        self._on_book_persist = on_book_persist
        self._lock = threading.RLock()
        self._running = False
        self._steps = 0
        self._last_error: str | None = None
        self._config: PaperSessionConfig | None = None
        self._strategy: Any | None = None
        self._bars: list[Bar] = []
        self._stop_event = threading.Event()
        self._bg_thread: threading.Thread | None = None

    def start(self, config: PaperSessionConfig) -> dict[str, Any]:
        """Inicia (o reinicia) la sesión; opcionalmente lanza background."""
        self.stop()
        with self._lock:
            sid = config.strategy_id.strip().lower()
            if sid not in ("dummy", "buy_once", "momentum", "simple_momentum"):
                raise ValidationError(
                    f"strategy_id desconocido: {config.strategy_id!r}; "
                    f"disponibles: dummy, buy_once, momentum"
                )
            normalized = PaperSessionConfig(
                strategy_id="momentum" if sid == "simple_momentum" else sid,
                symbol=config.symbol.strip(),
                max_steps=config.max_steps,
                interval_ms=config.interval_ms,
                params=dict(config.params),
            )
            self._strategy = build_session_strategy(normalized.strategy_id, normalized.params)
            self._strategy.reset()
            self._config = normalized
            self._bars.clear()
            self._steps = 0
            self._last_error = None
            self._running = True
            self._stop_event.clear()
            if normalized.interval_ms is not None:
                self._bg_thread = threading.Thread(
                    target=self._background_loop,
                    name="paper-session-bg",
                    daemon=True,
                )
                self._bg_thread.start()
            return self.status()

    def stop(self) -> dict[str, Any]:
        """Detiene background y marca sesión no running."""
        self._stop_event.set()
        thread: threading.Thread | None
        with self._lock:
            thread = self._bg_thread
            self._bg_thread = None
            self._running = False
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=2.0)
        return self.status()

    def step(self) -> dict[str, Any]:
        """Un paso: snapshot → bar → strategy → risk/submit → resumen."""
        with self._lock:
            return self._step_unlocked()

    def status(self) -> dict[str, Any]:
        with self._lock:
            cfg = self._config
            return {
                "running": self._running,
                "steps": self._steps,
                "last_error": self._last_error,
                "strategy_id": cfg.strategy_id if cfg is not None else None,
                "symbol": cfg.symbol if cfg is not None else None,
                "max_steps": cfg.max_steps if cfg is not None else None,
                "interval_ms": cfg.interval_ms if cfg is not None else None,
                "bars_buffered": len(self._bars),
                "live_blocked": LIVE_BLOCKED is True,
                "background_alive": bool(
                    self._bg_thread is not None and self._bg_thread.is_alive()
                ),
            }

    def _background_loop(self) -> None:
        while not self._stop_event.is_set():
            with self._lock:
                cfg = self._config
                if cfg is None or not self._running or self._steps >= cfg.max_steps:
                    self._running = False
                    break
                interval = cfg.interval_ms
            try:
                self.step()
            except Exception as exc:  # noqa: BLE001 — capturar para last_error
                with self._lock:
                    self._last_error = str(exc)
                    self._running = False
                break
            if interval is None:
                break
            if self._stop_event.wait(timeout=interval / 1000.0):
                break
            with self._lock:
                cfg2 = self._config
                if cfg2 is None or self._steps >= cfg2.max_steps:
                    self._running = False
                    break

    def _step_unlocked(self) -> dict[str, Any]:
        if not LIVE_BLOCKED:
            raise ValidationError("LIVE_BLOCKED debe ser True")
        if self._config is None or self._strategy is None:
            raise ValidationError("sesión paper no iniciada; llamar start() primero")
        cfg = self._config
        if self._steps >= cfg.max_steps:
            self._running = False
            raise ValidationError(f"max_steps alcanzado ({cfg.max_steps})")
        if not self._running:
            raise ValidationError("sesión paper detenida; llamar start() primero")

        snapshot = self._broker.get_snapshot(cfg.symbol)
        bar = snapshot_to_bar(snapshot, step_index=self._steps)
        self._bars.append(bar)

        now = bar.timestamp_close
        clock = SimulationClock(
            current_time=now,
            mode=ClockMode.STEP,
            speed=ClockSpeed.ACCELERATED,
        )
        portfolio = self._portfolio_from_book(now)
        ctx = StrategyContext(
            clock=clock,
            portfolio_state=portfolio,
            parameters=self._strategy.get_parameters(),
        )

        event = MarketEvent(
            event_id=f"ps-{self._steps}-{cfg.symbol}",
            event_type=EventType.BAR,
            timestamp=now,
            instrument_id=cfg.symbol,
            payload={
                "timeframe": bar.timeframe,
                "close": str(bar.close),
                "source": "paper_session",
            },
        )
        intents = self._strategy.on_event(event, ctx)
        if not intents:
            intents = self._strategy.on_bar(bar, ctx)

        actions: list[dict[str, Any]] = []
        for intent in intents:
            actions.append(self._process_intent(intent, snapshot))

        self._steps += 1
        if self._steps >= cfg.max_steps:
            self._running = False
            self._stop_event.set()

        book_snap = self._book.to_dict()
        return {
            "ok": True,
            "step": self._steps,
            "symbol": cfg.symbol,
            "strategy_id": cfg.strategy_id,
            "snapshot": dataclass_to_dict(snapshot),
            "bar": dataclass_to_dict(bar),
            "intents": [dataclass_to_dict(i) for i in intents],
            "actions": actions,
            "book": book_snap,
            "running": self._running,
            "last_error": self._last_error,
            "live_blocked": LIVE_BLOCKED is True,
            "live_routing": False,
        }

    def _process_intent(self, intent: OrderIntent, snapshot: BrokerSnapshot) -> dict[str, Any]:
        base: dict[str, Any] = {
            "intent_id": intent.intent_id,
            "intent_type": intent.intent_type.value,
            "instrument_id": intent.instrument_id,
        }
        if intent.intent_type is IntentType.NO_ACTION:
            base["status"] = "NO_ACTION"
            return base

        if intent.intent_type is IntentType.PLACE_ORDER:
            try:
                self._risk.check_intent(intent, snapshot)
            except ValidationError as exc:
                self._last_error = str(exc)
                base["status"] = "RISK_REJECTED"
                base["error"] = str(exc)
                return base

        if intent.intent_type not in (
            IntentType.PLACE_ORDER,
            IntentType.CANCEL_ORDER,
        ):
            base["status"] = "SKIPPED"
            base["error"] = f"intent_type no ejecutado en paper session: {intent.intent_type}"
            return base

        try:
            ack: BrokerAck = self._broker.submit(intent)
        except ValidationError as exc:
            self._last_error = str(exc)
            base["status"] = "BROKER_REJECTED"
            base["error"] = str(exc)
            return base

        if self._on_book_persist is not None:
            self._on_book_persist()

        base["status"] = ack.status
        base["ack"] = to_jsonable(dataclass_to_dict(ack))
        return base

    def _portfolio_from_book(self, now: datetime) -> PortfolioState:
        positions: list[Position] = []
        for bp in self._book.get_positions():
            avg = bp.avg_price if bp.avg_price is not None else Decimal("0")
            positions.append(
                Position(
                    instrument_id=bp.symbol,
                    quantity=bp.quantity,
                    avg_entry_price=avg,
                    unrealized_pnl=Decimal("0"),
                    realized_pnl=Decimal("0"),
                    updated_at=now,
                )
            )
        cash = self._book.cash
        balances = (
            Balance(
                asset=self._book.currency,
                available=cash if cash >= 0 else Decimal("0"),
                locked=Decimal("0"),
                total=cash if cash >= 0 else Decimal("0"),
                updated_at=now,
            ),
        )
        return PortfolioState(
            timestamp=now,
            positions=tuple(positions),
            balances=balances,
            total_equity=cash,
            total_realized_pnl=Decimal("0"),
            total_unrealized_pnl=Decimal("0"),
        )
