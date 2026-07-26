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
from quantlab.workbench.catalog_browser import list_catalog_datasets
from quantlab.workbench.commands import list_commands
from quantlab.workbench.docs_browser import list_docs, read_docs_content
from quantlab.workbench.feature_store_browser import list_feature_store
from quantlab.workbench.hb_exports import get_hb_export, list_hb_exports
from quantlab.workbench.layout import load_layout, save_layout
from quantlab.workbench.montecarlo_runs import (
    get_montecarlo_run,
    list_montecarlo_runs,
)
from quantlab.workbench.montecarlo_runs import (
    validate_run_id as validate_montecarlo_run_id,
)
from quantlab.workbench.onboarding import mark_onboarding_complete, onboarding_status
from quantlab.workbench.optimizer_runs import (
    get_optimizer_run,
    list_optimizer_runs,
)
from quantlab.workbench.optimizer_runs import (
    validate_run_id as validate_optimizer_run_id,
)
from quantlab.workbench.paper_session import PaperSessionConfig, PaperSessionRunner
from quantlab.workbench.reports import get_lab_report, list_lab_reports, validate_report_id
from quantlab.workbench.risk import PaperRiskLimits
from quantlab.workbench.session import WorkbenchSession
from quantlab.workbench.settings import load_settings, save_settings
from quantlab.workbench.validation_runs import (
    get_validation_run,
    list_validation_runs,
)
from quantlab.workbench.validation_runs import (
    validate_run_id as validate_validation_run_id,
)
from quantlab.workbench.watchlist import (
    add_symbols,
    load_watchlist,
    remove_symbols,
    save_watchlist,
)

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

    def ensure_lab_reports_dir(self) -> Path:
        session = self.ensure_session()
        session.reports_dir.mkdir(parents=True, exist_ok=True)
        return session.reports_dir

    def ensure_lab_features_dir(self) -> Path:
        session = self.ensure_session()
        session.features_dir.mkdir(parents=True, exist_ok=True)
        return session.features_dir

    def ensure_lab_validation_dir(self) -> Path:
        session = self.ensure_session()
        session.validation_dir.mkdir(parents=True, exist_ok=True)
        return session.validation_dir

    def ensure_lab_optimizer_dir(self) -> Path:
        session = self.ensure_session()
        session.optimizer_dir.mkdir(parents=True, exist_ok=True)
        return session.optimizer_dir

    def ensure_lab_montecarlo_dir(self) -> Path:
        session = self.ensure_session()
        session.montecarlo_dir.mkdir(parents=True, exist_ok=True)
        return session.montecarlo_dir

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


def handle_get_layout(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/layout — geometría MDI persistida en sesión."""
    session = state.ensure_session()
    try:
        layout = load_layout(session.layout_path)
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    return {
        "ok": True,
        "layout": layout,
        "session_id": session.session_id,
        "live_blocked": LIVE_BLOCKED is True,
    }


def handle_put_layout(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    """PUT /api/layout — guarda geometría de ventanas en ``layout.json``."""
    session = state.ensure_session()
    # Acepta body completo o { "layout": {...} }.
    if "windows" in body or "version" in body:
        payload = body
    elif "layout" in body and isinstance(body["layout"], dict):
        payload = body["layout"]
    else:
        raise ApiError(400, "body debe incluir layout (version/windows) o ser el layout")
    try:
        saved = save_layout(session.layout_path, payload)
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    return {
        "ok": True,
        "layout": saved,
        "session_id": session.session_id,
        "live_blocked": LIVE_BLOCKED is True,
    }


def handle_get_onboarding(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/onboarding — estado first-run wizard (meta.onboarding_done)."""
    session = state.ensure_session()
    status = onboarding_status(session)
    return {
        "ok": True,
        "kind": "onboarding",
        "session_id": session.session_id,
        "mode": state.mode.value,
        **status,
    }


def handle_post_onboarding_complete(
    state: WorkbenchState, body: dict[str, Any] | None = None
) -> dict[str, Any]:
    """POST /api/onboarding/complete — marca onboarding_done en meta.json."""
    _ = body  # body opcional / ignorado (fail-closed: sin campos LIVE)
    session = state.ensure_session()
    try:
        status = mark_onboarding_complete(session)
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    return {
        "ok": True,
        "kind": "onboarding",
        "session_id": session.session_id,
        "mode": state.mode.value,
        **status,
    }


def handle_get_docs(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/docs — lista docs/*.md y docs/ops/*.md (paths relativos safe)."""
    _ = state.ensure_session()
    try:
        payload = list_docs()
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    return {
        **payload,
        "session_id": state.ensure_session().session_id,
        "mode": state.mode.value,
    }


def handle_get_docs_content(state: WorkbenchState, query: str) -> dict[str, Any]:
    """GET /api/docs/content?path= — lee markdown solo bajo docs/ (fail-closed)."""
    _ = state.ensure_session()
    params = parse_qs(query, keep_blank_values=False)
    paths = params.get("path") or params.get("file") or []
    if not paths or not str(paths[0]).strip():
        raise ApiError(400, "query param 'path' requerido")
    try:
        payload = read_docs_content(str(paths[0]))
    except ValidationError as exc:
        msg = str(exc)
        status = 404 if "no encontrado" in msg.lower() else 400
        raise ApiError(status, msg) from exc
    return {
        **payload,
        "session_id": state.ensure_session().session_id,
        "mode": state.mode.value,
    }


def handle_get_settings(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/settings — preferencias de sesión (theme/venue/strategy/slip/locale)."""
    session = state.ensure_session()
    try:
        settings = load_settings(session.settings_path)
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    # Hidrata slippage de estado desde settings si el archivo existe.
    with contextlib.suppress(InvalidOperation, KeyError, TypeError):
        state.slippage_bps = Decimal(str(settings["slippage_bps"]))
    return {
        "ok": True,
        "kind": "settings",
        "settings": settings,
        "session_id": session.session_id,
        "mode": state.mode.value,
        "venue": state.venue,
        "md_provider": state.md_provider,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
        "allowed_themes": ["slate", "high-contrast"],
        "allowed_locales": ["es"],
    }


def handle_put_settings(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    """PUT /api/settings — guarda settings en ``settings.json`` (fail-closed)."""
    session = state.ensure_session()
    if "settings" in body and isinstance(body["settings"], dict):
        payload = body["settings"]
    elif any(
        k in body
        for k in ("theme", "default_venue", "default_strategy", "slippage_bps", "locale", "version")
    ):
        payload = body
    else:
        raise ApiError(400, "body debe incluir settings o campos de settings")
    try:
        # Merge parcial sobre defaults/actuales.
        current = load_settings(session.settings_path)
        merged = dict(current)
        for key in (
            "version",
            "theme",
            "default_venue",
            "default_strategy",
            "slippage_bps",
            "locale",
        ):
            if key in payload:
                merged[key] = payload[key]
        saved = save_settings(session.settings_path, merged)
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    try:
        state.slippage_bps = Decimal(str(saved["slippage_bps"]))
    except (InvalidOperation, KeyError, TypeError) as exc:
        raise ApiError(400, f"slippage_bps inválido tras save: {exc}") from exc
    return {
        "ok": True,
        "kind": "settings",
        "settings": saved,
        "session_id": session.session_id,
        "mode": state.mode.value,
        "venue": state.venue,
        "md_provider": state.md_provider,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }


def handle_get_watchlist(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/watchlist — símbolos persistidos en sesión."""
    session = state.ensure_session()
    try:
        watchlist = load_watchlist(session.watchlist_path)
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    return {
        "ok": True,
        "watchlist": watchlist,
        "symbols": list(watchlist["symbols"]),
        "session_id": session.session_id,
        "live_blocked": LIVE_BLOCKED is True,
    }


def handle_put_watchlist(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    """PUT /api/watchlist — replace / add / remove símbolos en ``watchlist.json``.

    Body aceptado:
    - ``{"symbols": [...]}`` o ``{"watchlist": {"symbols": [...]}}`` → replace
    - ``{"add": [...]}`` → add
    - ``{"remove": [...]}`` → remove
    """
    session = state.ensure_session()
    try:
        current = load_watchlist(session.watchlist_path)
        if "add" in body or "remove" in body:
            next_wl = current
            if "add" in body:
                add_raw = body["add"]
                if not isinstance(add_raw, list):
                    raise ValidationError("watchlist.add debe ser lista")
                next_wl = add_symbols(next_wl, [str(x) for x in add_raw])
            if "remove" in body:
                rem_raw = body["remove"]
                if not isinstance(rem_raw, list):
                    raise ValidationError("watchlist.remove debe ser lista")
                next_wl = remove_symbols(next_wl, [str(x) for x in rem_raw])
            saved = save_watchlist(session.watchlist_path, next_wl)
        elif "symbols" in body:
            saved = save_watchlist(
                session.watchlist_path,
                {"version": 1, "symbols": body["symbols"]},
            )
        elif "watchlist" in body and isinstance(body["watchlist"], dict):
            saved = save_watchlist(session.watchlist_path, body["watchlist"])
        else:
            raise ApiError(
                400,
                "body debe incluir symbols, watchlist, add y/o remove",
            )
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    return {
        "ok": True,
        "watchlist": saved,
        "symbols": list(saved["symbols"]),
        "session_id": session.session_id,
        "live_blocked": LIVE_BLOCKED is True,
    }


def handle_get_universe(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/universe — broker instruments + watchlist (F30)."""
    session = state.ensure_session()
    try:
        watchlist = load_watchlist(session.watchlist_path)
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc

    broker_connected = state.broker is not None
    broker_symbols: list[dict[str, Any]] = []
    broker_message: str | None = None
    if broker_connected:
        assert state.broker is not None
        try:
            broker_symbols = [dataclass_to_dict(i) for i in state.broker.list_instruments()]
        except Exception as exc:  # noqa: BLE001
            broker_message = f"broker.list_instruments falló: {exc}"
            broker_symbols = []
    else:
        broker_message = "broker no conectado; POST /api/broker/connect primero"

    wl_set = set(watchlist["symbols"])
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in broker_symbols:
        sym = str(item.get("symbol") or "").strip().upper()
        if not sym or sym in seen:
            continue
        seen.add(sym)
        merged.append(
            {
                "symbol": sym,
                "source": "broker",
                "in_watchlist": sym in wl_set,
                "description": item.get("description"),
                "currency": item.get("currency"),
            }
        )
    for sym in watchlist["symbols"]:
        if sym in seen:
            continue
        seen.add(sym)
        merged.append(
            {
                "symbol": sym,
                "source": "watchlist",
                "in_watchlist": True,
                "description": None,
                "currency": None,
            }
        )

    return {
        "ok": True,
        "session_id": session.session_id,
        "live_blocked": LIVE_BLOCKED is True,
        "broker_connected": broker_connected,
        "broker_message": broker_message,
        "watchlist": list(watchlist["symbols"]),
        "broker_symbols": broker_symbols,
        "symbols": merged,
        "count": len(merged),
    }


def handle_get_catalog(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/catalog — datasets del Data Catalog local (read-only, F30)."""
    session = state.ensure_session()
    payload = list_catalog_datasets()
    payload["session_id"] = session.session_id
    return payload


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


def handle_get_commands(_state: WorkbenchState) -> dict[str, Any]:
    """GET /api/commands — command palette: paneles + acciones seguras (F35)."""
    return list_commands()


def handle_get_lab_capabilities(_state: WorkbenchState) -> dict[str, Any]:
    return lab_services.lab_capabilities()


def handle_get_lab_strategies(_state: WorkbenchState) -> dict[str, Any]:
    """GET /api/lab/strategies — catálogo F27."""
    return lab_services.lab_strategies()


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


def handle_get_lab_validation(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/lab/validation — lista corridas + latest; si vacío, preview efímero (F32)."""
    try:
        listed = list_validation_runs(state.ensure_lab_validation_dir())
        listed["session_id"] = state.ensure_session().session_id
        latest = listed.get("latest")
        if isinstance(latest, dict):
            listed["kind"] = "validation"
            listed["ok"] = bool(latest.get("ok", True))
            listed["n_bars"] = latest.get("n_bars")
            listed["train_val_oos"] = latest.get("train_val_oos")
            listed["walk_forward"] = latest.get("walk_forward")
            listed["anti_leakage"] = latest.get("anti_leakage")
            listed["multiple_testing"] = latest.get("multiple_testing")
            listed["persisted"] = True
            listed["run_id"] = latest.get("run_id")
            return listed
        # Empty-ok: preview sintético sin persistir (compat F21 + UI).
        preview = lab_services.run_lab_validation(persist=False)
        listed["preview"] = preview
        listed["kind"] = "validation"
        listed["ok"] = bool(preview.get("ok", True))
        listed["n_bars"] = preview["n_bars"]
        listed["train_val_oos"] = preview["train_val_oos"]
        listed["walk_forward"] = preview["walk_forward"]
        listed["anti_leakage"] = preview["anti_leakage"]
        listed["multiple_testing"] = preview["multiple_testing"]
        listed["persisted"] = False
        return listed
    except ValidationError as exc:
        raise _lab_validation_error(exc) from exc


def handle_get_lab_validation_run(state: WorkbenchState, run_id: str) -> dict[str, Any]:
    """GET /api/lab/validation/{run_id} — summary persistido."""
    try:
        rid = validate_validation_run_id(run_id)
        payload = get_validation_run(state.ensure_lab_validation_dir(), rid)
        payload["session_id"] = state.ensure_session().session_id
        return payload
    except ValidationError as exc:
        msg = str(exc)
        if "no encontrado" in msg:
            raise ApiError(404, msg) from exc
        raise _lab_validation_error(exc) from exc


def handle_post_lab_validation_run(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    """POST /api/lab/validation/run — splits + leakage + persist session/validation (F32)."""
    n_bars = body.get("n_bars", 40)
    if not isinstance(n_bars, int):
        raise ApiError(400, "n_bars debe ser int")
    train_frac = body.get("train_frac", 0.6)
    val_frac = body.get("val_frac", 0.2)
    train_size = body.get("train_size", 10)
    test_size = body.get("test_size", 5)
    step = body.get("step", test_size)
    persist = body.get("persist", True)
    for name, val, typ in (
        ("train_frac", train_frac, (int, float)),
        ("val_frac", val_frac, (int, float)),
        ("train_size", train_size, int),
        ("test_size", test_size, int),
        ("step", step, int),
    ):
        if not isinstance(val, typ):
            raise ApiError(400, f"{name} tipo inválido")
    if not isinstance(persist, bool):
        raise ApiError(400, "persist debe ser bool")
    # Path-safe: solo sandbox de sesión.
    if "path" in body or "validation_root" in body or "target_path" in body:
        raise ApiError(400, "path externo no permitido; validation solo a sandbox de sesión")
    try:
        result = lab_services.run_lab_validation(
            n_bars=n_bars,
            train_frac=float(train_frac),
            val_frac=float(val_frac),
            train_size=int(train_size),
            test_size=int(test_size),
            step=int(step),
            persist=persist,
            validation_root=state.ensure_lab_validation_dir() if persist else None,
        )
    except ValidationError as exc:
        raise _lab_validation_error(exc) from exc
    result["session_id"] = state.ensure_session().session_id
    return state.store_lab_result(result)


def handle_get_lab_reports(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/lab/reports — historial de reports persistidos (F29)."""
    try:
        return list_lab_reports(state.ensure_lab_reports_dir())
    except ValidationError as exc:
        raise _lab_validation_error(exc) from exc


def handle_get_lab_report(state: WorkbenchState, report_id: str) -> dict[str, Any]:
    """GET /api/lab/reports/{id} — summary + HTML preview payload."""
    try:
        rid = validate_report_id(report_id)
        return get_lab_report(state.ensure_lab_reports_dir(), rid, include_html=True)
    except ValidationError as exc:
        # 404 si no existe; 400 si id inválido.
        msg = str(exc)
        if "no encontrado" in msg:
            raise ApiError(404, msg) from exc
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
            reports_dir=state.ensure_lab_reports_dir(),
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
    """POST /api/lab/optimize — grid + Pareto + persist session/optimizer (F33)."""
    lookbacks_raw = body.get("lookbacks", [2, 3])
    quantities_raw = body.get("quantities", ["1"])
    n_bars = body.get("n_bars", 20)
    persist = body.get("persist", True)
    if not isinstance(lookbacks_raw, list) or not lookbacks_raw:
        raise ApiError(400, "lookbacks debe ser lista no vacía")
    if not isinstance(quantities_raw, list) or not quantities_raw:
        raise ApiError(400, "quantities debe ser lista no vacía")
    if not isinstance(n_bars, int):
        raise ApiError(400, "n_bars debe ser int")
    if not isinstance(persist, bool):
        raise ApiError(400, "persist debe ser bool")
    # Path-safe: solo sandbox de sesión.
    if "path" in body or "optimizer_root" in body or "target_path" in body:
        raise ApiError(400, "path externo no permitido; optimizer solo a sandbox de sesión")
    try:
        lookbacks = tuple(int(x) for x in lookbacks_raw)
        quantities = tuple(str(x) for x in quantities_raw)
        result = lab_services.run_lab_optimize(
            lookbacks=lookbacks,
            quantities=quantities,
            n_bars=n_bars,
            persist=persist,
            optimizer_root=state.ensure_lab_optimizer_dir() if persist else None,
        )
    except (ValidationError, TypeError, ValueError) as exc:
        raise ApiError(400, str(exc)) from exc
    result["session_id"] = state.ensure_session().session_id
    return state.store_lab_result(result)


def handle_get_lab_optimize_history(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/lab/optimize/history — lista corridas + latest (F33)."""
    try:
        listed = list_optimizer_runs(state.ensure_lab_optimizer_dir())
        listed["session_id"] = state.ensure_session().session_id
        latest = listed.get("latest")
        if isinstance(latest, dict):
            listed["kind"] = "optimize_history"
            listed["ok"] = True
            listed["method"] = latest.get("method")
            listed["n_trials"] = latest.get("n_trials")
            listed["n_bars"] = latest.get("n_bars")
            listed["best"] = latest.get("best")
            listed["history"] = latest.get("history")
            listed["pareto"] = latest.get("pareto")
            listed["persisted"] = True
            listed["run_id"] = latest.get("run_id")
            return listed
        listed["kind"] = "optimize_history"
        listed["ok"] = True
        listed["persisted"] = False
        listed["best"] = None
        listed["history"] = []
        listed["pareto"] = None
        return listed
    except ValidationError as exc:
        raise _lab_validation_error(exc) from exc


def handle_get_lab_optimize_run(state: WorkbenchState, run_id: str) -> dict[str, Any]:
    """GET /api/lab/optimize/history/{run_id} — summary persistido."""
    try:
        rid = validate_optimizer_run_id(run_id)
        payload = get_optimizer_run(state.ensure_lab_optimizer_dir(), rid)
        payload["session_id"] = state.ensure_session().session_id
        return payload
    except ValidationError as exc:
        msg = str(exc)
        if "no encontrado" in msg:
            raise ApiError(404, msg) from exc
        raise _lab_validation_error(exc) from exc


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
    persist = body.get("persist", True)
    if not isinstance(persist, bool):
        raise ApiError(400, "persist debe ser bool")
    if "path" in body or "montecarlo_root" in body or "target_path" in body:
        raise ApiError(400, "path externo no permitido; montecarlo solo a sandbox de sesión")
    try:
        result = lab_services.run_lab_montecarlo(
            n_scenarios=n_scenarios,
            n_bars=n_bars,
            noise_bps=float(noise_bps),
            persist=persist,
            montecarlo_root=state.ensure_lab_montecarlo_dir() if persist else None,
        )
    except ValidationError as exc:
        raise _lab_validation_error(exc) from exc
    result["session_id"] = state.ensure_session().session_id
    return state.store_lab_result(result)


def handle_get_lab_montecarlo_history(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/lab/montecarlo/history — lista corridas + latest (F34)."""
    try:
        listed = list_montecarlo_runs(state.ensure_lab_montecarlo_dir())
        listed["session_id"] = state.ensure_session().session_id
        latest = listed.get("latest")
        if isinstance(latest, dict):
            listed["kind"] = "montecarlo_history"
            listed["ok"] = True
            listed["n_scenarios"] = latest.get("n_scenarios")
            listed["n_bars"] = latest.get("n_bars")
            listed["seed"] = latest.get("seed")
            listed["mean_equity"] = latest.get("mean_equity")
            listed["std_equity"] = latest.get("std_equity")
            listed["ci_low"] = latest.get("ci_low")
            listed["ci_high"] = latest.get("ci_high")
            listed["ci_level"] = latest.get("ci_level", 0.95)
            listed["final_equities"] = latest.get("final_equities")
            listed["persisted"] = True
            listed["run_id"] = latest.get("run_id")
            return listed
        listed["kind"] = "montecarlo_history"
        listed["ok"] = True
        listed["persisted"] = False
        listed["mean_equity"] = None
        listed["ci_low"] = None
        listed["ci_high"] = None
        return listed
    except ValidationError as exc:
        raise _lab_validation_error(exc) from exc


def handle_get_lab_montecarlo_run(state: WorkbenchState, run_id: str) -> dict[str, Any]:
    """GET /api/lab/montecarlo/history/{run_id} — summary persistido."""
    try:
        rid = validate_montecarlo_run_id(run_id)
        payload = get_montecarlo_run(state.ensure_lab_montecarlo_dir(), rid)
        payload["session_id"] = state.ensure_session().session_id
        return payload
    except ValidationError as exc:
        msg = str(exc)
        if "no encontrado" in msg:
            raise ApiError(404, msg) from exc
        raise _lab_validation_error(exc) from exc


def handle_post_lab_features(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    """POST /api/lab/features[/run] — pipeline demo + persist FeatureStore sesión (F31)."""
    n_bars = body.get("n_bars", 20)
    if not isinstance(n_bars, int):
        raise ApiError(400, "n_bars debe ser int")
    version = body.get("version")
    if version is not None and not isinstance(version, str):
        raise ApiError(400, "version debe ser string")
    persist = body.get("persist", True)
    if not isinstance(persist, bool):
        raise ApiError(400, "persist debe ser bool")
    # Path-safe: solo sandbox de sesión; rechazar override externo.
    if "path" in body or "store_root" in body or "target_path" in body:
        raise ApiError(400, "path externo no permitido; features solo a sandbox de sesión")
    try:
        store_root = state.ensure_lab_features_dir() if persist else None
        result = lab_services.run_lab_features(
            n_bars=n_bars,
            store_root=store_root,
            version=version.strip() if isinstance(version, str) else None,
            persist=persist,
        )
    except ValidationError as exc:
        raise _lab_validation_error(exc) from exc
    result["session_id"] = state.ensure_session().session_id
    return state.store_lab_result(result)


def handle_get_lab_features_store(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/lab/features/store — lista artifacts session/features o default (F31)."""
    session = state.ensure_session()
    payload = list_feature_store(session_root=session.root)
    payload["session_id"] = session.session_id
    return payload


def handle_post_lab_export_hb(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    experiment_id = body.get("experiment_id", "wb-hb-export")
    strategy_version = body.get("strategy_version", "demo-1")
    if not isinstance(experiment_id, str) or not experiment_id.strip():
        raise ApiError(400, "experiment_id inválido")
    if not isinstance(strategy_version, str) or not strategy_version.strip():
        raise ApiError(400, "strategy_version inválido")
    # Path-safe: solo sandbox de sesión; rechazar override externo.
    if "path" in body or "target_path" in body or "export_root" in body:
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
    result["session_id"] = state.ensure_session().session_id
    return state.store_lab_result(result)


def handle_get_lab_exports(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/lab/exports — lista exports HB previos en session/exports (F34)."""
    listed = list_hb_exports(state.ensure_lab_export_dir())
    listed["session_id"] = state.ensure_session().session_id
    return listed


def handle_get_lab_export(state: WorkbenchState, export_id: str) -> dict[str, Any]:
    """GET /api/lab/exports/{export_id} — payload de un export."""
    try:
        payload = get_hb_export(state.ensure_lab_export_dir(), export_id)
        payload["session_id"] = state.ensure_session().session_id
        return payload
    except ValidationError as exc:
        msg = str(exc)
        if "no encontrado" in msg:
            raise ApiError(404, msg) from exc
        raise _lab_validation_error(exc) from exc


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
