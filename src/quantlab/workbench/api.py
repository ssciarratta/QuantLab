"""JSON API handlers del workbench (loopback, fail-closed ante LIVE)."""

from __future__ import annotations

import contextlib
import uuid
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs

from quantlab.brokers.mode import REAL_ALIAS, OperatingMode, default_mode, resolve_mode
from quantlab.brokers.paper.book import DEFAULT_INITIAL_CASH, PaperBook
from quantlab.brokers.paper.broker import PaperBroker
from quantlab.brokers.paper.journal import PaperFillJournal
from quantlab.brokers.port import BrokerPort
from quantlab.brokers.registry import BrokerRegistry, get_default_registry
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import IntentType, OrderSide, OrderType, TimeInForce
from quantlab.core.types.orders import OrderIntent
from quantlab.core.types.serialization import dataclass_to_dict, to_jsonable
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.infra.health import run_health_checks
from quantlab.workbench import lab_services
from quantlab.workbench.paper_session import PaperSessionConfig, PaperSessionRunner
from quantlab.workbench.risk import PaperRiskLimits
from quantlab.workbench.session import WorkbenchSession

if TYPE_CHECKING:
    from quantlab.workbench.chat.orchestrator import ChatOrchestrator


@dataclass
class WorkbenchState:
    """Estado de sesión del workbench (un proceso) con raíz durable."""

    mode: OperatingMode = field(default_factory=default_mode)
    registry: BrokerRegistry = field(default_factory=get_default_registry)
    broker: BrokerPort | None = None
    venue: str | None = None
    md_provider: str | None = None
    md_source: str | None = None
    journal: PaperFillJournal | None = None
    book: PaperBook | None = None
    session: WorkbenchSession | None = None
    risk: PaperRiskLimits = field(default_factory=PaperRiskLimits)
    initial_cash: Decimal = field(default_factory=lambda: Decimal(DEFAULT_INITIAL_CASH))
    slippage_bps: Decimal = field(default_factory=lambda: Decimal("0"))
    last_lab_result: dict[str, Any] | None = None
    paper_session: PaperSessionRunner | None = None
    _lab_registry_path: Path | None = field(default=None, repr=False)
    _lab_export_dir: Path | None = field(default=None, repr=False)
    _chat: ChatOrchestrator | None = field(default=None, repr=False)

    def ensure_session(self) -> WorkbenchSession:
        if self.session is None:
            self.session = WorkbenchSession.create_or_load(
                None,
                None,
                initial_cash=self.initial_cash,
            )
            self._hydrate_from_session()
        elif self.journal is None or self.book is None:
            self._hydrate_from_session()
        return self.session

    def _hydrate_from_session(self) -> None:
        if self.session is None:
            raise ValidationError("sesión no inicializada")
        self.session.ensure_layout()
        self.journal = PaperFillJournal(self.session.journal_path)
        self.book = self.session.load_book(default_cash=self.initial_cash)
        self._lab_registry_path = self.session.experiments_dir / "experiments.sqlite"
        self._lab_export_dir = self.session.exports_dir
        lab_services.ensure_demo_experiment(self._lab_registry_path)

    def persist_book(self) -> None:
        session = self.ensure_session()
        if self.book is None:
            return
        session.save_book(self.book)

    def ensure_journal(self) -> PaperFillJournal:
        self.ensure_session()
        if self.journal is None:
            raise ValidationError("journal no hidratado")
        return self.journal

    def ensure_book(self) -> PaperBook:
        self.ensure_session()
        if self.book is None:
            raise ValidationError("book no hidratado")
        return self.book

    def ensure_lab_registry_path(self) -> Path:
        self.ensure_session()
        if self._lab_registry_path is None:
            raise ValidationError("lab registry path no hidratado")
        return self._lab_registry_path

    def ensure_lab_export_dir(self) -> Path:
        self.ensure_session()
        if self._lab_export_dir is None:
            raise ValidationError("lab export dir no hidratado")
        return self._lab_export_dir

    def store_lab_result(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.last_lab_result = payload
        return payload

    def ensure_chat(self) -> ChatOrchestrator:
        """Lazy ChatOrchestrator (FakeProvider por defecto; audit en sesión)."""
        if self._chat is None:
            from quantlab.workbench.chat.orchestrator import build_orchestrator

            session = self.ensure_session()
            self._chat = build_orchestrator(self, audit_path=session.chat_audit_path)
        return self._chat


class ApiError(Exception):
    """Error HTTP de la API con status code."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


def _require_broker(state: WorkbenchState) -> BrokerPort:
    if state.broker is None:
        raise ApiError(400, "broker no conectado; POST /api/broker/connect primero")
    return state.broker


def _reject_live_mode(mode: OperatingMode) -> None:
    if mode is OperatingMode.LIVE:
        raise ApiError(
            400,
            "OperatingMode.LIVE no permitido en workbench (LIVE_BLOCKED). Usar tester|paper|real.",
        )


def _parse_mode(raw: str) -> OperatingMode:
    try:
        mode = resolve_mode(raw)
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    _reject_live_mode(mode)
    return mode


def _md_info(state: WorkbenchState) -> dict[str, Any]:
    return {
        "md_provider": state.md_provider,
        "md_source": state.md_source,
        "venues": state.registry.list_venues(),
        "plugin_venues": state.registry.list_plugin_venues(),
        "connected_venue": state.venue,
    }


def handle_get_health(state: WorkbenchState) -> dict[str, Any]:
    report = run_health_checks().to_dict()
    report.update(_md_info(state))
    return report


def handle_get_mode(state: WorkbenchState) -> dict[str, Any]:
    return {
        "mode": state.mode.value,
        "live_blocked": LIVE_BLOCKED is True,
        "real_alias": REAL_ALIAS.value,
    }


def handle_get_session(state: WorkbenchState) -> dict[str, Any]:
    session = state.ensure_session()
    out: dict[str, Any] = {
        "ok": True,
        "session": session.to_dict(),
        "live_blocked": LIVE_BLOCKED is True,
        "mode": state.mode.value,
        "initial_cash": str(state.initial_cash),
        "slippage_bps": str(state.slippage_bps),
    }
    out.update(_md_info(state))
    return out


def handle_get_risk(state: WorkbenchState) -> dict[str, Any]:
    """Límites paper + path de sesión (panel Riesgo)."""
    session = state.ensure_session()
    allowed = sorted(state.risk.allowed_symbols) if state.risk.allowed_symbols is not None else None
    return {
        "ok": True,
        "limits": {
            "max_qty": str(state.risk.max_qty),
            "max_notional": str(state.risk.max_notional),
            "allowed_symbols": allowed,
        },
        "slippage_bps": str(state.slippage_bps),
        "session_id": session.session_id,
        "session_root": str(session.root),
        "live_blocked": LIVE_BLOCKED is True,
        "mode": state.mode.value,
    }


def handle_post_mode(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    raw = body.get("mode")
    if not isinstance(raw, str) or not raw.strip():
        raise ApiError(400, "campo 'mode' requerido (tester|paper|real)")
    mode = _parse_mode(raw)
    state.mode = mode
    # Cambiar modo invalida broker conectado (evita mismatch mode/venue).
    if state.paper_session is not None:
        state.paper_session.stop()
        state.paper_session = None
    if state.broker is not None:
        with contextlib.suppress(Exception):
            state.broker.close()
        state.broker = None
        state.venue = None
        state.md_provider = None
        state.md_source = None
    return handle_get_mode(state)


def handle_get_venues(state: WorkbenchState) -> dict[str, Any]:
    return {
        "venues": state.registry.list_venues(),
        "plugin_venues": state.registry.list_plugin_venues(),
    }


def _parse_md_source(body: dict[str, Any]) -> str | None:
    raw = body.get("md_source")
    if raw is None:
        return None
    if not isinstance(raw, str) or not raw.strip():
        raise ApiError(400, "campo 'md_source' inválido (fake|env)")
    key = raw.strip().lower()
    if key not in ("fake", "env"):
        raise ApiError(400, "campo 'md_source' inválido (fake|env)")
    return key


def _parse_slippage_bps(body: dict[str, Any], default: Decimal) -> Decimal:
    raw = body.get("slippage_bps")
    if raw is None:
        return default
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError) as exc:
        raise ApiError(400, f"slippage_bps inválido: {exc}") from exc
    if value < 0:
        raise ApiError(400, "slippage_bps no puede ser negativo")
    if value >= Decimal("10000"):
        raise ApiError(400, "slippage_bps debe ser < 10000")
    return value


def handle_post_broker_connect(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    venue_raw = body.get("venue")
    if not isinstance(venue_raw, str) or not venue_raw.strip():
        raise ApiError(400, "campo 'venue' requerido")
    venue = venue_raw.strip().lower()

    mode_raw = body.get("mode")
    if mode_raw is None:
        mode = state.mode
    elif isinstance(mode_raw, str):
        mode = _parse_mode(mode_raw)
        state.mode = mode
    else:
        raise ApiError(400, "campo 'mode' inválido")

    _reject_live_mode(mode)

    md_source = _parse_md_source(body)
    slippage_bps = _parse_slippage_bps(body, state.slippage_bps)
    state.slippage_bps = slippage_bps
    create_opts: dict[str, Any] = {}
    if md_source is not None:
        create_opts["md_source"] = md_source
    csv_path = body.get("csv_path")
    if csv_path is not None:
        if not isinstance(csv_path, str):
            raise ApiError(400, "campo 'csv_path' debe ser string")
        create_opts["csv_path"] = csv_path

    try:
        created = state.registry.create(venue, mode, **create_opts)
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc

    # Cerrar anterior
    if state.paper_session is not None:
        state.paper_session.stop()
        state.paper_session = None
    if state.broker is not None:
        with contextlib.suppress(Exception):
            state.broker.close()

    # Siempre PaperBroker + book/journal de sesión: nunca place_order venue.
    state.ensure_session()
    journal = state.ensure_journal()
    book = state.ensure_book()
    md: BrokerPort = created._md if isinstance(created, PaperBroker) else created  # noqa: SLF001

    def _on_book_change(updated: PaperBook) -> None:
        state.book = updated
        state.persist_book()

    broker: BrokerPort = PaperBroker(
        md,
        journal=journal,
        book=book,
        slippage_bps=slippage_bps,
        on_book_change=_on_book_change,
    )

    connect_info = broker.connect()
    state.broker = broker
    state.venue = venue
    health = broker.health()
    provider = health.get("md_provider") or health.get("provider") or venue
    state.md_provider = str(provider)
    state.md_source = str(
        health.get("md_source") or md_source or create_opts.get("md_source") or "fake"
    )
    return {
        "ok": True,
        "venue": venue,
        "mode": mode.value,
        "broker_venue_id": broker.venue_id,
        "paper_broker": True,
        "md_provider": state.md_provider,
        "md_source": state.md_source,
        "slippage_bps": str(slippage_bps),
        "session_id": state.ensure_session().session_id,
        "connect": to_jsonable(connect_info),
    }


def handle_get_instruments(state: WorkbenchState) -> dict[str, Any]:
    broker = _require_broker(state)
    items = [dataclass_to_dict(i) for i in broker.list_instruments()]
    return {"instruments": items}


def handle_get_snapshot(state: WorkbenchState, query: str) -> dict[str, Any]:
    broker = _require_broker(state)
    params = parse_qs(query, keep_blank_values=False)
    symbols = params.get("symbol") or params.get("symbols")
    if not symbols or not symbols[0].strip():
        raise ApiError(400, "query param 'symbol' requerido")
    symbol = symbols[0].strip()
    try:
        snap = broker.get_snapshot(symbol)
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise ApiError(400, str(exc)) from exc
    return {"snapshot": dataclass_to_dict(snap)}


def handle_get_account(state: WorkbenchState) -> dict[str, Any]:
    broker = _require_broker(state)
    return {"account": dataclass_to_dict(broker.get_account())}


def handle_get_positions(state: WorkbenchState) -> dict[str, Any]:
    broker = _require_broker(state)
    positions = [dataclass_to_dict(p) for p in broker.get_positions()]
    return {"positions": positions}


def handle_get_paper_book(state: WorkbenchState) -> dict[str, Any]:
    book = state.ensure_book()
    account: dict[str, Any] | None = None
    if state.broker is not None:
        account = dataclass_to_dict(state.broker.get_account())
    else:
        account = dataclass_to_dict(book.get_account())
    return {
        "book": book.to_dict(),
        "account": account,
        "session_id": state.ensure_session().session_id,
    }


def _parse_order_intent(body: dict[str, Any]) -> OrderIntent:
    intent_id = str(body.get("intent_id") or f"wb-{uuid.uuid4().hex[:12]}")
    intent_type_raw = body.get("intent_type", IntentType.PLACE_ORDER.value)
    try:
        intent_type = IntentType(str(intent_type_raw).strip().lower())
    except ValueError as exc:
        raise ApiError(400, f"intent_type inválido: {intent_type_raw!r}") from exc

    instrument_id = body.get("instrument_id") or body.get("symbol")
    if not isinstance(instrument_id, str) or not instrument_id.strip():
        raise ApiError(400, "instrument_id (o symbol) requerido")

    side: OrderSide | None = None
    if body.get("side") is not None:
        try:
            side = OrderSide(str(body["side"]).strip().lower())
        except ValueError as exc:
            raise ApiError(400, f"side inválido: {body['side']!r}") from exc

    order_type: OrderType | None = None
    if body.get("order_type") is not None:
        try:
            order_type = OrderType(str(body["order_type"]).strip().lower())
        except ValueError as exc:
            raise ApiError(400, f"order_type inválido: {body['order_type']!r}") from exc

    quantity: Decimal | None = None
    if body.get("quantity") is not None:
        try:
            quantity = Decimal(str(body["quantity"]))
        except (InvalidOperation, ValueError) as exc:
            raise ApiError(400, f"quantity inválida: {body['quantity']!r}") from exc

    price: Decimal | None = None
    if body.get("price") is not None:
        try:
            price = Decimal(str(body["price"]))
        except (InvalidOperation, ValueError) as exc:
            raise ApiError(400, f"price inválido: {body['price']!r}") from exc

    tif: TimeInForce | None = None
    if body.get("time_in_force") is not None:
        try:
            tif = TimeInForce(str(body["time_in_force"]).strip().lower())
        except ValueError as exc:
            raise ApiError(400, f"time_in_force inválido: {body['time_in_force']!r}") from exc

    replace_target_id = body.get("replace_target_id")
    if replace_target_id is not None:
        replace_target_id = str(replace_target_id)

    try:
        return OrderIntent(
            intent_id=intent_id,
            intent_type=intent_type,
            instrument_id=instrument_id.strip(),
            side=side,
            quantity=quantity,
            price=price,
            order_type=order_type,
            time_in_force=tif,
            replace_target_id=replace_target_id,
        )
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc


def handle_post_paper_submit(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    _reject_live_mode(state.mode)
    if state.mode not in (OperatingMode.TESTER, OperatingMode.PAPER):
        raise ApiError(400, "paper/submit solo en modos tester|paper")

    broker = _require_broker(state)
    if not isinstance(broker, PaperBroker):
        raise ApiError(
            400,
            "paper/submit requiere PaperBroker; reconectar en tester|paper "
            "(nunca llama place_order venue)",
        )

    intent = _parse_order_intent(body)
    if intent.intent_type is IntentType.PLACE_ORDER:
        try:
            snap = broker.get_snapshot(intent.instrument_id)
            state.risk.check_intent(intent, snap)
        except ValidationError as exc:
            raise ApiError(400, str(exc)) from exc
    try:
        ack = broker.submit(intent)
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    account = dataclass_to_dict(broker.get_account())
    return {
        "ack": dataclass_to_dict(ack),
        "account": account,
        "positions": [dataclass_to_dict(p) for p in broker.get_positions()],
    }


def _require_paper_broker(state: WorkbenchState) -> PaperBroker:
    broker = _require_broker(state)
    if not isinstance(broker, PaperBroker):
        raise ApiError(
            400,
            "paper/session requiere PaperBroker conectado (nunca place_order venue)",
        )
    return broker


def _ensure_paper_session_runner(state: WorkbenchState) -> PaperSessionRunner:
    broker = _require_paper_broker(state)
    book = state.ensure_book()
    if state.paper_session is not None:
        state.paper_session.stop()
    state.paper_session = PaperSessionRunner(
        broker,
        state.risk,
        book,
        on_book_persist=state.persist_book,
    )
    return state.paper_session


def handle_post_paper_session_start(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    """POST /api/paper/session/start — inicia sesión paper (estrategia + símbolo)."""
    if not LIVE_BLOCKED:
        raise ApiError(400, "LIVE_BLOCKED debe ser True")
    _reject_live_mode(state.mode)
    if state.mode not in (OperatingMode.TESTER, OperatingMode.PAPER):
        raise ApiError(400, "paper/session solo en modos tester|paper")

    strategy_id = body.get("strategy_id")
    if not isinstance(strategy_id, str) or not strategy_id.strip():
        raise ApiError(400, "campo 'strategy_id' requerido")
    symbol = body.get("symbol")
    if not isinstance(symbol, str) or not symbol.strip():
        raise ApiError(400, "campo 'symbol' requerido")

    max_steps = body.get("max_steps", 100)
    if not isinstance(max_steps, int):
        raise ApiError(400, "max_steps debe ser int")

    interval_ms = body.get("interval_ms")
    if interval_ms is not None and not isinstance(interval_ms, int):
        raise ApiError(400, "interval_ms debe ser int o null")

    params = body.get("params")
    if params is None:
        params_dict: dict[str, Any] = {}
    elif isinstance(params, dict):
        params_dict = params
    else:
        raise ApiError(400, "params debe ser objeto JSON")

    runner = _ensure_paper_session_runner(state)
    try:
        config = PaperSessionConfig(
            strategy_id=strategy_id.strip(),
            symbol=symbol.strip(),
            max_steps=max_steps,
            interval_ms=interval_ms,
            params=params_dict,
        )
        status = runner.start(config)
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    return {
        "ok": True,
        "status": status,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
    }


def handle_post_paper_session_stop(state: WorkbenchState) -> dict[str, Any]:
    """POST /api/paper/session/stop."""
    if state.paper_session is None:
        return {
            "ok": True,
            "status": {
                "running": False,
                "steps": 0,
                "last_error": None,
                "strategy_id": None,
                "live_blocked": LIVE_BLOCKED is True,
            },
            "live_blocked": LIVE_BLOCKED is True,
        }
    status = state.paper_session.stop()
    return {"ok": True, "status": status, "live_blocked": LIVE_BLOCKED is True}


def handle_post_paper_session_step(state: WorkbenchState) -> dict[str, Any]:
    """POST /api/paper/session/step — un tick manual."""
    if not LIVE_BLOCKED:
        raise ApiError(400, "LIVE_BLOCKED debe ser True")
    _require_paper_broker(state)
    if state.paper_session is None:
        raise ApiError(400, "sesión paper no iniciada; POST /api/paper/session/start")
    try:
        summary = state.paper_session.step()
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    state.persist_book()
    return summary


def handle_get_paper_session_status(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/paper/session/status."""
    if state.paper_session is None:
        return {
            "ok": True,
            "running": False,
            "steps": 0,
            "last_error": None,
            "strategy_id": None,
            "live_blocked": LIVE_BLOCKED is True,
            "broker_connected": state.broker is not None,
        }
    status = state.paper_session.status()
    status["ok"] = True
    status["broker_connected"] = state.broker is not None
    return status


def handle_get_paper_fills(state: WorkbenchState) -> dict[str, Any]:
    journal = state.ensure_journal()
    fills = [dataclass_to_dict(f) for f in journal.list_fills()]
    return {"fills": fills}


def _lab_validation_error(exc: ValidationError) -> ApiError:
    return ApiError(400, str(exc))


def handle_get_lab_capabilities(_state: WorkbenchState) -> dict[str, Any]:
    return lab_services.lab_capabilities()


def handle_get_lab_metrics(state: WorkbenchState) -> dict[str, Any]:
    if state.last_lab_result is None:
        return {
            "ok": True,
            "kind": "metrics",
            "has_result": False,
            "result": None,
            "message": "sin resultado aún; correr backtest/optimize/montecarlo/scanner",
            "live_routing": False,
        }
    return {
        "ok": True,
        "kind": "metrics",
        "has_result": True,
        "result": state.last_lab_result,
        "live_routing": False,
    }


def handle_get_lab_experiments(state: WorkbenchState) -> dict[str, Any]:
    path = state.ensure_lab_registry_path()
    return lab_services.list_lab_experiments(path)


def handle_get_lab_validation(_state: WorkbenchState) -> dict[str, Any]:
    try:
        return lab_services.run_lab_validation()
    except ValidationError as exc:
        raise _lab_validation_error(exc) from exc


def handle_post_lab_backtest(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    strategy_id = body.get("strategy_id", "momentum")
    if not isinstance(strategy_id, str) or not strategy_id.strip():
        raise ApiError(400, "strategy_id debe ser string no vacío")
    params = body.get("params")
    if params is None:
        params_dict: dict[str, Any] = {}
    elif isinstance(params, dict):
        params_dict = params
    else:
        raise ApiError(400, "params debe ser objeto JSON")
    n_bars = body.get("n_bars", 24)
    if not isinstance(n_bars, int):
        raise ApiError(400, "n_bars debe ser int")
    experiment_id = body.get("experiment_id", "wb-lab-backtest")
    if not isinstance(experiment_id, str) or not experiment_id.strip():
        raise ApiError(400, "experiment_id inválido")
    try:
        experiment_id = lab_services.validate_experiment_id(experiment_id)
        result = lab_services.run_lab_backtest(
            strategy_id=strategy_id,
            params=params_dict,
            n_bars=n_bars,
            experiment_id=experiment_id,
        )
    except ValidationError as exc:
        raise _lab_validation_error(exc) from exc
    return state.store_lab_result(result)


def handle_post_lab_scanner(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    top_n = body.get("top_n", 3)
    if not isinstance(top_n, int):
        raise ApiError(400, "top_n debe ser int")
    try:
        result = lab_services.run_lab_scanner(top_n=top_n)
    except ValidationError as exc:
        raise _lab_validation_error(exc) from exc
    return state.store_lab_result(result)


def handle_post_lab_optimize(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    lookbacks_raw = body.get("lookbacks", [2, 3])
    quantities_raw = body.get("quantities", ["1"])
    n_bars = body.get("n_bars", 20)
    if not isinstance(lookbacks_raw, list) or not lookbacks_raw:
        raise ApiError(400, "lookbacks debe ser lista no vacía")
    if not isinstance(quantities_raw, list) or not quantities_raw:
        raise ApiError(400, "quantities debe ser lista no vacía")
    if not isinstance(n_bars, int):
        raise ApiError(400, "n_bars debe ser int")
    try:
        lookbacks = tuple(int(x) for x in lookbacks_raw)
        quantities = tuple(str(x) for x in quantities_raw)
        result = lab_services.run_lab_optimize(
            lookbacks=lookbacks, quantities=quantities, n_bars=n_bars
        )
    except (ValidationError, TypeError, ValueError) as exc:
        raise ApiError(400, str(exc)) from exc
    return state.store_lab_result(result)


def handle_post_lab_montecarlo(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    n_scenarios = body.get("n_scenarios", 5)
    n_bars = body.get("n_bars", 16)
    noise_bps = body.get("noise_bps", 10.0)
    if not isinstance(n_scenarios, int):
        raise ApiError(400, "n_scenarios debe ser int")
    if not isinstance(n_bars, int):
        raise ApiError(400, "n_bars debe ser int")
    if not isinstance(noise_bps, (int, float)):
        raise ApiError(400, "noise_bps debe ser número")
    try:
        result = lab_services.run_lab_montecarlo(
            n_scenarios=n_scenarios,
            n_bars=n_bars,
            noise_bps=float(noise_bps),
        )
    except ValidationError as exc:
        raise _lab_validation_error(exc) from exc
    return state.store_lab_result(result)


def handle_post_lab_features(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    n_bars = body.get("n_bars", 20)
    if not isinstance(n_bars, int):
        raise ApiError(400, "n_bars debe ser int")
    try:
        result = lab_services.run_lab_features(n_bars=n_bars)
    except ValidationError as exc:
        raise _lab_validation_error(exc) from exc
    return state.store_lab_result(result)


def handle_post_lab_export_hb(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    experiment_id = body.get("experiment_id", "wb-hb-export")
    strategy_version = body.get("strategy_version", "demo-1")
    if not isinstance(experiment_id, str) or not experiment_id.strip():
        raise ApiError(400, "experiment_id inválido")
    if not isinstance(strategy_version, str) or not strategy_version.strip():
        raise ApiError(400, "strategy_version inválido")
    # Path-safe: solo sandbox de sesión; rechazar override externo.
    if "path" in body or "target_path" in body:
        raise ApiError(400, "path externo no permitido; export solo a sandbox de sesión")
    try:
        experiment_id = lab_services.validate_experiment_id(experiment_id)
        result = lab_services.run_lab_export_hb(
            state.ensure_lab_export_dir(),
            experiment_id=experiment_id,
            strategy_version=strategy_version.strip(),
        )
    except ValidationError as exc:
        raise _lab_validation_error(exc) from exc
    return state.store_lab_result(result)


def handle_get_chat_tools(state: WorkbenchState) -> dict[str, Any]:
    return state.ensure_chat().list_tools()


def handle_post_chat(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    message = body.get("message")
    if not isinstance(message, str) or not message.strip():
        raise ApiError(400, "campo 'message' requerido (string no vacío)")
    try:
        return state.ensure_chat().handle_message(message)
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
