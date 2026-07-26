"""JSON API handlers del workbench (loopback, fail-closed ante LIVE)."""

from __future__ import annotations

import contextlib
import tempfile
import uuid
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs

from quantlab.brokers.mode import REAL_ALIAS, OperatingMode, default_mode, resolve_mode
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

if TYPE_CHECKING:
    from quantlab.workbench.chat.orchestrator import ChatOrchestrator


@dataclass
class WorkbenchState:
    """Estado de sesión del workbench (un proceso)."""

    mode: OperatingMode = field(default_factory=default_mode)
    registry: BrokerRegistry = field(default_factory=get_default_registry)
    broker: BrokerPort | None = None
    venue: str | None = None
    journal: PaperFillJournal | None = None
    last_lab_result: dict[str, Any] | None = None
    _journal_dir: Path | None = field(default=None, repr=False)
    _lab_registry_path: Path | None = field(default=None, repr=False)
    _lab_export_dir: Path | None = field(default=None, repr=False)
    _chat: ChatOrchestrator | None = field(default=None, repr=False)

    def ensure_journal(self) -> PaperFillJournal:
        if self.journal is None:
            if self._journal_dir is None:
                self._journal_dir = Path(tempfile.mkdtemp(prefix="ql_wb_journal_"))
            self.journal = PaperFillJournal(self._journal_dir / "paper_fills.jsonl")
        return self.journal

    def ensure_lab_registry_path(self) -> Path:
        if self._lab_registry_path is None:
            root = Path(tempfile.mkdtemp(prefix="ql_wb_experiments_"))
            self._lab_registry_path = root / "experiments.sqlite"
            lab_services.ensure_demo_experiment(self._lab_registry_path)
        return self._lab_registry_path

    def ensure_lab_export_dir(self) -> Path:
        if self._lab_export_dir is None:
            self._lab_export_dir = Path(tempfile.mkdtemp(prefix="ql_wb_hb_export_"))
        return self._lab_export_dir

    def store_lab_result(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.last_lab_result = payload
        return payload

    def ensure_chat(self) -> ChatOrchestrator:
        """Lazy ChatOrchestrator (FakeProvider por defecto)."""
        if self._chat is None:
            from quantlab.workbench.chat.orchestrator import build_orchestrator

            self._chat = build_orchestrator(self)
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


def handle_get_health(_state: WorkbenchState) -> dict[str, Any]:
    return run_health_checks().to_dict()


def handle_get_mode(state: WorkbenchState) -> dict[str, Any]:
    return {
        "mode": state.mode.value,
        "live_blocked": LIVE_BLOCKED is True,
        "real_alias": REAL_ALIAS.value,
    }


def handle_post_mode(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    raw = body.get("mode")
    if not isinstance(raw, str) or not raw.strip():
        raise ApiError(400, "campo 'mode' requerido (tester|paper|real)")
    mode = _parse_mode(raw)
    state.mode = mode
    # Cambiar modo invalida broker conectado (evita mismatch mode/venue).
    if state.broker is not None:
        with contextlib.suppress(Exception):
            state.broker.close()
        state.broker = None
        state.venue = None
    return handle_get_mode(state)


def handle_get_venues(state: WorkbenchState) -> dict[str, Any]:
    return {"venues": state.registry.list_venues()}


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

    try:
        created = state.registry.create(venue, mode)
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc

    # Cerrar anterior
    if state.broker is not None:
        with contextlib.suppress(Exception):
            state.broker.close()

    # Siempre PaperBroker + journal de sesión: el workbench nunca llama
    # place_order del venue (MD se unwrappea si el registry ya envolvió).
    journal = state.ensure_journal()
    md: BrokerPort = created._md if isinstance(created, PaperBroker) else created  # noqa: SLF001
    broker: BrokerPort = PaperBroker(md, journal=journal)

    connect_info = broker.connect()
    state.broker = broker
    state.venue = venue
    return {
        "ok": True,
        "venue": venue,
        "mode": mode.value,
        "broker_venue_id": broker.venue_id,
        "paper_broker": True,
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
    try:
        ack = broker.submit(intent)
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    return {"ack": dataclass_to_dict(ack)}


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
        result = lab_services.run_lab_backtest(
            strategy_id=strategy_id,
            params=params_dict,
            n_bars=n_bars,
            experiment_id=experiment_id.strip(),
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
        result = lab_services.run_lab_export_hb(
            state.ensure_lab_export_dir(),
            experiment_id=experiment_id.strip(),
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
