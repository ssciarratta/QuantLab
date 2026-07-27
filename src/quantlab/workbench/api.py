"""JSON API handlers del workbench (loopback, fail-closed ante LIVE)."""

from __future__ import annotations

import contextlib
import io
import json
import threading
import uuid
import zipfile
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs

from quantlab import __version__
from quantlab.brokers.mode import REAL_ALIAS, OperatingMode, default_mode, resolve_mode
from quantlab.brokers.paper.book import DEFAULT_INITIAL_CASH, PaperBook
from quantlab.brokers.paper.broker import PaperBroker
from quantlab.brokers.paper.journal import PaperFillJournal
from quantlab.brokers.paper.reconciliation import (
    ReconciliationReport,
    reconcile_book,
)
from quantlab.brokers.port import BrokerPort
from quantlab.brokers.registry import BrokerRegistry, get_default_registry
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import IntentType, OrderSide, OrderType, TimeInForce
from quantlab.core.types.orders import OrderIntent
from quantlab.core.types.serialization import dataclass_to_dict, to_jsonable
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.infra.health import run_health_checks
from quantlab.infra.ops_metrics import get_ops_metrics, render_prometheus_text
from quantlab.workbench import lab_services
from quantlab.workbench.about import build_about_payload
from quantlab.workbench.access_log import AccessLog, list_access_log
from quantlab.workbench.access_log import clamp_limit as clamp_access_limit
from quantlab.workbench.activity import ActivityLog, clamp_limit, list_activity
from quantlab.workbench.api_catalog import openapi_payload
from quantlab.workbench.auto_backup import (
    list_backups,
    run_auto_backup,
)
from quantlab.workbench.broker_disconnect import (
    clear_broker_connection,
    disconnect_status,
)
from quantlab.workbench.broker_reconnect import (
    last_connect_status,
    require_last_connect,
    save_last_connect,
)
from quantlab.workbench.catalog_browser import list_catalog_datasets
from quantlab.workbench.commands import list_commands
from quantlab.workbench.docs_browser import list_docs, read_docs_content
from quantlab.workbench.equity_curve import (
    EquityCurveLog,
    clamp_equity_limit,
    list_equity,
)
from quantlab.workbench.feature_store_browser import list_feature_store
from quantlab.workbench.hb_exports import get_hb_export, list_hb_exports
from quantlab.workbench.i18n import build_i18n_payload
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
from quantlab.workbench.paper_kill import (
    is_paper_kill_engaged,
    paper_kill_status,
    raise_if_paper_kill_engaged,
    set_paper_kill_engaged,
)
from quantlab.workbench.paper_pnl import pnl_from_book, pnl_from_broker
from quantlab.workbench.paper_session import PaperSessionConfig, PaperSessionRunner
from quantlab.workbench.presets import (
    apply_preset,
    delete_custom_preset,
    list_presets,
    save_custom_preset,
)
from quantlab.workbench.probes import livez_payload, readyz_payload
from quantlab.workbench.rate_limit import RateLimitConfig, RateLimiter
from quantlab.workbench.reports import get_lab_report, list_lab_reports, validate_report_id
from quantlab.workbench.risk import PaperRiskLimits
from quantlab.workbench.risk_utilization import (
    utilization_from_book,
    utilization_from_broker,
)
from quantlab.workbench.session import (
    DEFAULT_SESSION_PARENT,
    WorkbenchSession,
    list_sessions,
    resolve_session_parent,
    validate_session_id,
)
from quantlab.workbench.session_zip import (
    export_result_to_dict,
    export_session,
    import_result_to_dict,
    import_session_zip,
    make_temp_work_dir,
    resolve_upload_archive,
    rmtree_quiet,
    write_export_sidecar_sha,
)
from quantlab.workbench.settings import load_settings, save_settings
from quantlab.workbench.shutdown import is_loopback_client, perform_graceful_shutdown
from quantlab.workbench.validation_runs import (
    get_validation_run,
    list_validation_runs,
)
from quantlab.workbench.validation_runs import (
    validate_run_id as validate_validation_run_id,
)
from quantlab.workbench.watchlist import (
    add_symbols,
    export_watchlist_json,
    import_symbols,
    load_watchlist,
    parse_import_mode,
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
    chat_instructor_ctx: dict[str, Any] = field(default_factory=dict)
    chat_memory: Any = field(default=None, repr=False)  # ChatMemory lazy
    paper_session: PaperSessionRunner | None = None
    paper_kill_engaged: bool = False
    paper_reconciliation: ReconciliationReport | None = None
    bind_host: str = "127.0.0.1"
    allow_non_loopback: bool = False
    session_parent: Path | None = None
    rate_limiter: RateLimiter = field(default_factory=RateLimiter)
    shutdown_requested: bool = False
    shutdown_reason: str | None = None
    shutdown_done: bool = False
    auto_backup_scheduler: Any = field(default=None, repr=False)
    _http_server: Any = field(default=None, repr=False)
    _shutdown_lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _lab_registry_path: Path | None = field(default=None, repr=False)
    _lab_export_dir: Path | None = field(default=None, repr=False)
    _chat: ChatOrchestrator | None = field(default=None, repr=False)

    def configure_rate_limit(self, config: RateLimitConfig) -> RateLimiter:
        """Reemplaza el limiter (tests / inyección de límite bajo)."""
        self.rate_limiter = RateLimiter(config)
        return self.rate_limiter

    def resolve_session_parent(self) -> Path:
        """Parent durable de sesiones (switcher / list)."""
        if self.session is not None:
            parent = self.session.root.parent.resolve()
            self.session_parent = parent
            return parent
        if self.session_parent is not None:
            return resolve_session_parent(self.session_parent)
        return resolve_session_parent(DEFAULT_SESSION_PARENT)

    def ensure_session(self) -> WorkbenchSession:
        if self.session is None:
            self.session = WorkbenchSession.create_or_load(
                self.session_parent,
                None,
                initial_cash=self.initial_cash,
            )
            self.session_parent = self.session.root.parent.resolve()
            self._hydrate_from_session()
        elif self.journal is None or self.book is None:
            self._hydrate_from_session()
        return self.session

    def _hydrate_from_session(self) -> None:
        if self.session is None:
            raise ValidationError("sesión no inicializada")
        self.session.ensure_layout()
        self.session_parent = self.session.root.parent.resolve()
        self.journal = PaperFillJournal(self.session.journal_path)
        try:
            loaded = self.session.load_book_state(default_cash=self.initial_cash)
        except ValidationError as exc:
            self.book = PaperBook(initial_cash=self.initial_cash)
            try:
                checkpoint = self.journal.checkpoint()
                record_count = checkpoint.record_count
            except ValidationError:
                checkpoint = None
                record_count = 0
            self.paper_reconciliation = ReconciliationReport(
                ok=False,
                status="book_corrupt",
                record_count=record_count,
                issues=(str(exc),),
                expected_book=None,
                persisted_book={},
                checkpoint=checkpoint,
            )
        else:
            self.book = loaded.book
            self.paper_reconciliation = self._reconcile_loaded_book(
                stored_checkpoint=loaded.checkpoint,
                schema_version=loaded.schema_version,
            )
        self._lab_registry_path = self.session.experiments_dir / "experiments.sqlite"
        self._lab_export_dir = self.session.exports_dir
        lab_services.ensure_demo_experiment(self._lab_registry_path)
        self.paper_kill_engaged = is_paper_kill_engaged(self.session.load_meta())

    def _reconcile_loaded_book(
        self,
        *,
        stored_checkpoint: Any,
        schema_version: int,
        migrate_legacy: bool = True,
    ) -> ReconciliationReport:
        if self.book is None or self.journal is None:
            raise ValidationError("book/journal no hidratados")
        report = reconcile_book(self.book, self.journal)
        if not report.ok:
            issues = list(report.issues)
            if stored_checkpoint is not None and report.checkpoint is not None:
                if (
                    stored_checkpoint.record_count < report.checkpoint.record_count
                    and self.journal.contains_checkpoint(stored_checkpoint)
                ):
                    issues.insert(0, "journal_ahead")
                elif stored_checkpoint.record_count > report.checkpoint.record_count:
                    issues.insert(0, "book_ahead")
                elif stored_checkpoint != report.checkpoint:
                    issues.insert(0, "checkpoint_mismatch")
            elif schema_version == 1:
                issues.insert(0, "legacy_book_mismatch")
            elif schema_version == 0:
                issues.insert(0, "book_missing")
            return ReconciliationReport(
                ok=False,
                status=report.status,
                record_count=report.record_count,
                issues=tuple(dict.fromkeys(issues)),
                expected_book=report.expected_book,
                persisted_book=report.persisted_book,
                checkpoint=report.checkpoint,
            )

        if schema_version == 2 and stored_checkpoint != report.checkpoint:
            issue = "checkpoint_mismatch"
            if report.checkpoint is not None and stored_checkpoint is not None:
                if (
                    stored_checkpoint.record_count < report.checkpoint.record_count
                    and self.journal.contains_checkpoint(stored_checkpoint)
                ):
                    issue = "journal_ahead"
                elif stored_checkpoint.record_count > report.checkpoint.record_count:
                    issue = "book_ahead"
            return ReconciliationReport(
                ok=False,
                status="rebuild_required",
                record_count=report.record_count,
                issues=(issue,),
                expected_book=report.expected_book,
                persisted_book=report.persisted_book,
                checkpoint=report.checkpoint,
            )

        # Migración flat -> v2 sólo si replay y book coinciden exactamente.
        if schema_version in {0, 1} and report.checkpoint is not None and self.session is not None:
            if not migrate_legacy:
                return ReconciliationReport(
                    ok=False,
                    status="rebuild_required",
                    record_count=report.record_count,
                    issues=("book_missing" if schema_version == 0 else "legacy_format",),
                    expected_book=report.expected_book,
                    persisted_book=report.persisted_book,
                    checkpoint=report.checkpoint,
                )
            try:
                self.session.save_book(self.book, report.checkpoint)
            except (OSError, ValidationError) as exc:
                return ReconciliationReport(
                    ok=False,
                    status="rebuild_required",
                    record_count=report.record_count,
                    issues=(f"legacy_migration_failed: {exc}",),
                    expected_book=report.expected_book,
                    persisted_book=report.persisted_book,
                    checkpoint=report.checkpoint,
                )
            return ReconciliationReport(
                ok=True,
                status="ok",
                record_count=report.record_count,
                issues=("legacy_book_migrated",) if schema_version == 1 else (),
                expected_book=report.expected_book,
                persisted_book=report.persisted_book,
                checkpoint=report.checkpoint,
            )
        return report

    def check_paper_reconciliation(self) -> ReconciliationReport:
        """Check read-only del estado durable actual; nunca reconstruye."""
        session = self.ensure_session()
        if self.book is None or self.journal is None:
            raise ValidationError("book/journal no hidratados")
        # Un book corrupto detectado al boot no debe reemplazarse por el fallback.
        if (
            self.paper_reconciliation is not None
            and self.paper_reconciliation.status == "book_corrupt"
        ):
            return self.paper_reconciliation

        def _check_durable() -> ReconciliationReport:
            try:
                loaded = session.load_book_state(default_cash=self.initial_cash)
            except ValidationError as exc:
                return ReconciliationReport(
                    ok=False,
                    status="book_corrupt",
                    record_count=0,
                    issues=(str(exc),),
                    expected_book=None,
                    persisted_book={},
                    checkpoint=None,
                )
            live_book = self.book
            try:
                self.book = loaded.book
                return self._reconcile_loaded_book(
                    stored_checkpoint=loaded.checkpoint,
                    schema_version=loaded.schema_version,
                    migrate_legacy=False,
                )
            finally:
                self.book = live_book

        if isinstance(self.broker, PaperBroker):
            report = self.broker.inspect_reconciliation(_check_durable)
        else:
            report = _check_durable()
        self.paper_reconciliation = report
        return report

    def rehydrate_session(self) -> ReconciliationReport:
        """Relee journal/book desde disco tras un rebuild CLI (F91).

        Nunca reconstruye archivos ni muta el journal: hace teardown del
        runtime (runner/broker) y re-hidrata desde el estado durable, igual
        que un reinicio de proceso. Si el estado durable sigue inválido, el
        resultado queda igual de bloqueado que al boot.
        """
        session = self.ensure_session()
        self.switch_session(session.session_id)
        if self.paper_reconciliation is None:
            raise ValidationError("reconciliación no disponible tras rehydrate")
        return self.paper_reconciliation

    def _teardown_session_runtime(self) -> None:
        """Detiene runner paper, persiste book y limpia estado atado a sesión."""
        if self.paper_session is not None:
            self.paper_session.stop()
            self.paper_session = None
        if self.session is not None and self.book is not None:
            with contextlib.suppress(OSError, ValidationError):
                self.persist_book()
        self.broker = None
        self.venue = None
        self.md_provider = None
        self.md_source = None
        self.journal = None
        self.book = None
        self.paper_reconciliation = None
        self.last_lab_result = None
        self._chat = None
        self._lab_registry_path = None
        self._lab_export_dir = None

    def switch_session(self, session_id: str, *, create: bool = False) -> WorkbenchSession:
        """Cambia a otra sesión (fail-closed ``validate_session_id``) y recrea paths."""
        sid = validate_session_id(session_id)
        parent = self.resolve_session_parent()
        parent.mkdir(parents=True, exist_ok=True)
        target = (parent / sid).resolve()
        if not target.is_relative_to(parent):
            raise ValidationError(
                f"session root fuera de parent (path traversal): {target} vs {parent}"
            )
        if not create and not target.is_dir():
            raise ValidationError(f"sesión no encontrada: {sid}")
        self._teardown_session_runtime()
        self.session = WorkbenchSession.create_or_load(
            parent,
            sid,
            initial_cash=self.initial_cash,
        )
        self.session_parent = parent
        self._hydrate_from_session()
        return self.session

    def new_session(self, session_id: str | None = None) -> WorkbenchSession:
        """Crea sesión nueva bajo el parent y hace switch."""
        parent = self.resolve_session_parent()
        raw = (session_id or "").strip() or uuid.uuid4().hex[:12]
        sid = validate_session_id(raw)
        target = (parent / sid).resolve()
        if not target.is_relative_to(parent):
            raise ValidationError(
                f"session root fuera de parent (path traversal): {target} vs {parent}"
            )
        if target.is_dir() and (target / "meta.json").is_file():
            raise ValidationError(f"sesión ya existe: {sid}")
        return self.switch_session(sid, create=True)

    def persist_book(self) -> None:
        session = self.ensure_session()
        if self.book is None or self.journal is None:
            return
        report = reconcile_book(self.book, self.journal)
        if not report.ok or report.checkpoint is None:
            self.paper_reconciliation = report
            raise ValidationError(
                "book no se persiste: journal/book requieren reconciliación "
                f"({'; '.join(report.issues)})"
            )
        session.save_book(self.book, report.checkpoint)
        self.paper_reconciliation = report

    def assert_paper_kill_clear(self) -> None:
        """Fail-closed: ValidationError si paper kill switch engaged."""
        raise_if_paper_kill_engaged(engaged=self.paper_kill_engaged)

    def set_paper_kill(self, engaged: bool) -> dict[str, Any]:
        """Engage/disengage kill switch y persiste en session meta."""
        session = self.ensure_session()
        status = set_paper_kill_engaged(session, bool(engaged))
        self.paper_kill_engaged = bool(engaged)
        return status

    def paper_kill_status(self) -> dict[str, Any]:
        """Estado kill switch (GET /api/paper/kill)."""
        session = self.ensure_session()
        status = paper_kill_status(session, engaged=self.paper_kill_engaged)
        # Prefer in-memory flag (already hydrated / set).
        status["engaged"] = self.paper_kill_engaged is True
        return status

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


def _record_activity(
    state: WorkbenchState,
    event: str,
    *,
    ok: bool = True,
    message: str = "",
    detail: dict[str, Any] | None = None,
    op: str | None = None,
) -> None:
    """Append-only a ``activity.jsonl`` (best-effort; no rompe el handler)."""
    try:
        session = state.ensure_session()
        session.ensure_layout()
        ActivityLog(session.activity_path).append(
            event,
            ok=ok,
            message=message,
            detail=detail,
            op=op,
        )
    except Exception:  # noqa: BLE001 — activity nunca debe tumbar la API
        return


def _record_equity_point(state: WorkbenchState) -> dict[str, Any] | None:
    """Append equity/cash a ``equity.jsonl`` (best-effort; F66)."""
    try:
        session = state.ensure_session()
        session.ensure_layout()
        book = state.ensure_book()
        if state.broker is not None and isinstance(state.broker, PaperBroker):
            account = state.broker.get_account()
        else:
            account = book.get_account()
        equity = account.equity if account.equity is not None else account.cash
        return EquityCurveLog(session.equity_path).append(
            equity=equity,
            cash=account.cash,
        )
    except Exception:  # noqa: BLE001 — equity curve nunca debe tumbar la API
        return None


def _activity_error(state: WorkbenchState, op: str, message: str) -> None:
    _record_activity(
        state,
        "error",
        ok=False,
        message=message,
        op=op,
        detail={"op": op},
    )


def handle_get_activity(state: WorkbenchState, query: str = "") -> dict[str, Any]:
    """GET /api/activity?limit=100 — últimos eventos de sesión."""
    session = state.ensure_session()
    session.ensure_layout()
    params = parse_qs(query, keep_blank_values=False)
    limit: int | None = None
    raw_limit = params.get("limit")
    if raw_limit and raw_limit[0].strip():
        try:
            limit = int(raw_limit[0].strip())
        except ValueError as exc:
            raise ApiError(400, "limit debe ser int") from exc
    try:
        payload = list_activity(session.activity_path, limit=limit)
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    payload["session_id"] = session.session_id
    payload["limit"] = clamp_limit(limit)
    return payload


def handle_get_access_log(state: WorkbenchState, query: str = "") -> dict[str, Any]:
    """GET /api/access-log?limit=100 — últimos requests HTTP de sesión (F61)."""
    session = state.ensure_session()
    session.ensure_layout()
    params = parse_qs(query, keep_blank_values=False)
    limit: int | None = None
    raw_limit = params.get("limit")
    if raw_limit and raw_limit[0].strip():
        try:
            limit = int(raw_limit[0].strip())
        except ValueError as exc:
            raise ApiError(400, "limit debe ser int") from exc
    try:
        payload = list_access_log(session.access_path, limit=limit)
        settings = load_settings(session.settings_path)
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    payload["session_id"] = session.session_id
    payload["limit"] = clamp_access_limit(limit)
    payload["access_log_enabled"] = bool(settings.get("access_log", True))
    return payload


def record_http_access(
    state: WorkbenchState,
    *,
    method: str,
    path: str,
    status: int,
    ms: float,
) -> None:
    """Append-only a ``access.jsonl`` si settings.access_log (best-effort)."""
    try:
        session = state.ensure_session()
        session.ensure_layout()
        settings = load_settings(session.settings_path)
        if settings.get("access_log", True) is not True:
            return
        AccessLog(session.access_path).append(
            method=method,
            path=path,
            status=status,
            ms=ms,
        )
    except Exception:  # noqa: BLE001 — access log nunca debe tumbar la API
        return


def handle_get_ops_metrics(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/ops/metrics — snapshot JSON de contadores in-process (F42)."""
    session = state.ensure_session()
    counters = dict(get_ops_metrics().snapshot().counters)
    blocked = int(counters.get("live_gate.blocked", 0))
    rows = [{"name": name, "value": int(value)} for name, value in counters.items()]
    return {
        "ok": True,
        "kind": "ops_metrics",
        "counters": counters,
        "rows": rows,
        "count": len(rows),
        "live_gate_blocked": blocked,
        "highlight_live_gate_blocked": blocked > 0,
        "session_id": session.session_id,
        "version": __version__,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }


def handle_get_ops_prometheus(state: WorkbenchState) -> str:
    """GET /api/ops/prometheus — text/plain Prometheus counters (F42)."""
    state.ensure_session()
    return render_prometheus_text()


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


def _workbench_ops_flags(state: WorkbenchState) -> dict[str, Any]:
    """Flags operativos de sesión para health/about (F71).

    ``paper_kill_engaged`` · ``auto_backup_minutes`` · ``access_log``.
    Fail-closed a defaults canónicos si settings ilegibles.
    """
    session = state.ensure_session()
    try:
        settings = load_settings(session.settings_path)
    except ValidationError:
        settings = {
            "access_log": True,
            "auto_backup_minutes": 0,
        }
    minutes_raw = settings.get("auto_backup_minutes", 0)
    minutes = int(minutes_raw) if isinstance(minutes_raw, int) else 0
    access_raw = settings.get("access_log", True)
    return {
        "paper_kill_engaged": state.paper_kill_engaged is True,
        "auto_backup_minutes": minutes,
        "access_log": access_raw is True,
    }


def handle_get_health(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/health — checks + md + flags ops sesión (F71)."""
    report = run_health_checks().to_dict()
    report.update(_md_info(state))
    report.update(_workbench_ops_flags(state))
    return report


def handle_get_livez(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/livez — liveness: 200 si el proceso responde (F54)."""
    _ = state  # process up = handler reachable; no I/O dependency
    return livez_payload()


def handle_get_readyz(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/readyz — readiness: LIVE_BLOCKED + session root writable (F54).

    Caller HTTP debe mapear ``ready`` → status 200 / 503.
    """
    session_root: Path | None = None
    try:
        session = state.ensure_session()
        session_root = session.root
    except Exception:  # noqa: BLE001 — not ready if session unavailable
        session_root = None
    return readyz_payload(session_root=session_root)


def handle_get_openapi(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/openapi.json — OpenAPI 3 mínimo desde catálogo (F55)."""
    _ = state
    return openapi_payload()


def handle_get_about(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/about — version, phases INTERNAL, Python, bind + flags (F45/F71)."""
    state.ensure_session()
    payload = build_about_payload(
        bind_host=state.bind_host,
        allow_non_loopback=state.allow_non_loopback,
    )
    payload.update(_workbench_ops_flags(state))
    return payload


def handle_get_mode(state: WorkbenchState) -> dict[str, Any]:
    from quantlab.execution.live_unlock import live_unlock_status

    return {
        "mode": state.mode.value,
        "live_blocked": LIVE_BLOCKED is True,
        "live_unlocked": live_unlock_status()["unlocked"],
        "real_alias": REAL_ALIAS.value,
    }


def handle_get_live_status(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/live/status — estado del gate LIVE + unlock (F100/F101)."""
    from quantlab.brokers.binance.demo_router import get_shared_demo_router
    from quantlab.execution.live_unlock import is_live_session_unlocked, live_unlock_status

    _ = state
    status = live_unlock_status()
    demo: dict[str, Any] | None = None
    if is_live_session_unlocked():
        try:
            demo = get_shared_demo_router().status()
        except ValidationError:
            demo = None
    return {
        "ok": True,
        "kind": "live_status",
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "demo_routing": demo is not None,
        "demo": demo,
        **status,
    }


def handle_post_live_unlock(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    """POST /api/live/unlock — pide usuario/contraseña; no persiste el password."""
    from quantlab.execution.live_unlock import live_unlock_status, unlock_live_session

    username = body.get("username")
    password = body.get("password")
    venue_scope = body.get("venue_scope", "binance_demo")
    if not isinstance(username, str) or not isinstance(password, str):
        raise ApiError(400, "username y password deben ser strings")
    if not isinstance(venue_scope, str):
        raise ApiError(400, "venue_scope debe ser string")
    try:
        session = unlock_live_session(
            username=username,
            password=password,
            venue_scope=venue_scope,
        )
    except ValidationError as exc:
        raise ApiError(401, str(exc)) from exc
    _record_activity(
        state,
        "live_unlock",
        ok=True,
        message=f"LIVE unlock ok scope={session.venue_scope}",
        detail={"username": session.username, "venue_scope": session.venue_scope},
    )
    status = live_unlock_status()
    return {
        "ok": True,
        "kind": "live_unlock",
        "live_blocked": LIVE_BLOCKED is True,
        "token": session.token,
        **status,
    }


def handle_post_live_lock(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    """POST /api/live/lock — cierra sesión LIVE desbloqueada."""
    from quantlab.execution.live_unlock import live_unlock_status, lock_live_session

    _ = body
    lock_live_session()
    _record_activity(state, "live_lock", ok=True, message="LIVE lock", detail={})
    return {
        "ok": True,
        "kind": "live_lock",
        "live_blocked": LIVE_BLOCKED is True,
        **live_unlock_status(),
    }


def _mirror_demo_fill_to_paper(
    state: WorkbenchState, fill: dict[str, Any]
) -> dict[str, Any] | None:
    """Opt-in: refleja fill demo FILLED en journal/book de sesión (F109)."""
    from datetime import datetime

    from quantlab.brokers.types import PaperFill

    price_raw = fill.get("price")
    if price_raw is None:
        return None
    try:
        price = Decimal(str(price_raw))
        quantity = Decimal(str(fill["quantity"]))
        ts = datetime.fromisoformat(str(fill["ts"]))
    except (InvalidOperation, ValueError, KeyError, TypeError):
        return None
    if not price.is_finite() or price <= 0:
        return None
    paper_fill = PaperFill(
        fill_id=f"demo-mirror-{uuid.uuid4().hex[:12]}",
        order_id=str(fill["order_id"]),
        symbol=str(fill["symbol"]),
        side=str(fill["side"]),
        quantity=quantity,
        price=price,
        ts=ts,
        source="binance_demo",
    )
    journal = state.ensure_journal()
    book = state.ensure_book()
    journal.append(paper_fill)
    book.apply_fill(paper_fill)
    state.persist_book()
    _record_equity_point(state)
    return dataclass_to_dict(paper_fill)


def handle_post_live_demo_submit(
    state: WorkbenchState, body: dict[str, Any]
) -> dict[str, Any]:
    """POST /api/live/demo/submit — orden demo Binance simulada (F101, unlock)."""
    from quantlab.brokers.binance.demo_router import (
        get_shared_demo_router,
        intent_from_demo_body,
    )
    from quantlab.execution.live_gate import LiveOrderRouter

    try:
        # Fail-closed: unlock primero (antes de validar body) para 401 sin unlock.
        from quantlab.execution.live_gate import LiveOrderRouter, require_live_unlock

        require_live_unlock(venue_scope="binance_demo")
        intent = intent_from_demo_body(body)
        router = LiveOrderRouter()
        ack = router.submit(intent)
        demo_status = get_shared_demo_router().status()
    except ValidationError as exc:
        msg = str(exc)
        status = 401 if "BLOQUEADO" in msg or "unlock" in msg.lower() else 400
        raise ApiError(status, msg) from exc

    _record_activity(
        state,
        "demo_submit",
        ok=True,
        message=f"demo fill {ack.order_id}",
        detail={
            "order_id": ack.order_id,
            "symbol": intent.instrument_id,
            "side": None if intent.side is None else intent.side.value,
            "quantity": None if intent.quantity is None else str(intent.quantity),
            "status": ack.status,
            "venue": ack.venue,
            "transport": demo_status.get("transport"),
        },
    )
    mirrored: dict[str, Any] | None = None
    mirror_flag = body.get("mirror_to_paper") in {True, "true", "1", 1}
    if mirror_flag and ack.status == "FILLED":
        fills = get_shared_demo_router().recent_fills(limit=1)
        if fills:
            try:
                mirrored = _mirror_demo_fill_to_paper(state, fills[-1])
            except ValidationError:
                mirrored = None
    return {
        "ok": True,
        "kind": "demo_submit",
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "transport": demo_status.get("transport"),
        "order_id": ack.order_id,
        "client_order_id": ack.client_order_id,
        "status": ack.status,
        "message": ack.message,
        "venue": ack.venue,
        "demo": demo_status,
        "mirrored_to_paper": mirrored is not None,
        "paper_fill": mirrored,
    }


def handle_post_live_demo_cancel(
    state: WorkbenchState, body: dict[str, Any]
) -> dict[str, Any]:
    """POST /api/live/demo/cancel — cancela orden demo resting (F109)."""
    from quantlab.brokers.binance.demo_router import (
        get_shared_demo_router,
        intent_from_demo_body,
    )
    from quantlab.execution.live_gate import LiveOrderRouter, require_live_unlock

    try:
        require_live_unlock(venue_scope="binance_demo")
        cancel_body = {"intent_type": "cancel_order", "order_id": body.get("order_id")}
        intent = intent_from_demo_body(cancel_body)
        router = LiveOrderRouter()
        ack = router.submit(intent)
        demo_status = get_shared_demo_router().status()
    except ValidationError as exc:
        msg = str(exc)
        status = 401 if "BLOQUEADO" in msg or "unlock" in msg.lower() else 400
        raise ApiError(status, msg) from exc

    _record_activity(
        state,
        "demo_cancel",
        ok=ack.status == "CANCELED",
        message=f"demo cancel {ack.order_id} -> {ack.status}",
        detail={"order_id": ack.order_id, "status": ack.status},
    )
    return {
        "ok": ack.status == "CANCELED",
        "kind": "demo_cancel",
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "order_id": ack.order_id,
        "status": ack.status,
        "message": ack.message,
        "demo": demo_status,
    }


def handle_get_live_demo_open_orders(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/live/demo/open-orders — órdenes demo resting (F109)."""
    from quantlab.brokers.binance.demo_router import get_shared_demo_router

    _ = state
    try:
        router = get_shared_demo_router()
    except ValidationError as exc:
        raise ApiError(401, str(exc)) from exc
    orders = router.open_orders()
    return {
        "ok": True,
        "kind": "demo_open_orders",
        "count": len(orders),
        "orders": orders,
        "demo": router.status(),
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
    }


def handle_get_live_demo_fills(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/live/demo/fills — fills demo de la sesión unlock (F101)."""
    from quantlab.brokers.binance.demo_router import get_shared_demo_router

    _ = state
    try:
        router = get_shared_demo_router()
    except ValidationError as exc:
        raise ApiError(401, str(exc)) from exc
    fills = router.recent_fills(limit=50)
    return {
        "ok": True,
        "kind": "demo_fills",
        "count": len(fills),
        "fills": fills,
        "demo": router.status(),
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
    }


def handle_post_binance_scan(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    """POST /api/lab/binance/scan — MD público Binance read-only (F100)."""
    from quantlab.brokers.binance.public_md import scan_binance_usdt

    _ = state
    limit = body.get("limit", 20)
    if not isinstance(limit, int):
        raise ApiError(400, "limit debe ser int")
    try:
        return scan_binance_usdt(limit=limit)
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc


def handle_post_binance_scanner(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    """POST /api/lab/binance/scanner — Alpha ranking sobre klines Binance (F111)."""
    top_n = body.get("top_n", 5)
    symbol_limit = body.get("symbol_limit", 15)
    interval = body.get("interval", "1h")
    kline_limit = body.get("kline_limit", 24)
    if not isinstance(top_n, int):
        raise ApiError(400, "top_n debe ser int")
    if not isinstance(symbol_limit, int):
        raise ApiError(400, "symbol_limit debe ser int")
    if not isinstance(interval, str):
        raise ApiError(400, "interval debe ser string")
    if not isinstance(kline_limit, int):
        raise ApiError(400, "kline_limit debe ser int")
    try:
        result = lab_services.run_binance_lab_scanner(
            top_n=top_n,
            symbol_limit=symbol_limit,
            interval=interval.strip(),
            kline_limit=kline_limit,
        )
        out = state.store_lab_result(result)
        _record_activity(
            state,
            "scanner",
            ok=True,
            message="binance alpha scanner",
            detail={"top_n": top_n, "kind": result.get("kind")},
        )
        return out
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc


def handle_post_binance_pipeline(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    """POST /api/lab/binance/pipeline — scan alpha + backtest top-N (F111)."""
    strategy_id = body.get("strategy_id", "momentum")
    if not isinstance(strategy_id, str) or not strategy_id.strip():
        raise ApiError(400, "strategy_id inválido")
    params = body.get("params")
    if params is None:
        params_dict: dict[str, Any] = {}
    elif isinstance(params, dict):
        params_dict = params
    else:
        raise ApiError(400, "params debe ser objeto JSON")
    top_n = body.get("top_n", 5)
    symbol_limit = body.get("symbol_limit", 15)
    interval = body.get("interval", "1h")
    kline_limit = body.get("kline_limit", 24)
    experiment_id = body.get("experiment_id", "wb-bn-pipe")
    if not isinstance(top_n, int):
        raise ApiError(400, "top_n debe ser int")
    if not isinstance(symbol_limit, int):
        raise ApiError(400, "symbol_limit debe ser int")
    if not isinstance(interval, str):
        raise ApiError(400, "interval debe ser string")
    if not isinstance(kline_limit, int):
        raise ApiError(400, "kline_limit debe ser int")
    if not isinstance(experiment_id, str) or not experiment_id.strip():
        raise ApiError(400, "experiment_id inválido")
    try:
        experiment_id = lab_services.validate_experiment_id(experiment_id)
        result = lab_services.run_binance_lab_pipeline(
            strategy_id=strategy_id,
            params=params_dict,
            top_n=top_n,
            symbol_limit=symbol_limit,
            interval=interval.strip(),
            kline_limit=kline_limit,
            experiment_id_prefix=experiment_id,
            reports_dir=state.ensure_lab_reports_dir(),
        )
        out = state.store_lab_result(result)
        _record_activity(
            state,
            "backtest",
            ok=result.get("ok") is True,
            message=f"binance pipeline {strategy_id}",
            detail={"top_n": top_n, "kind": result.get("kind")},
        )
        return out
    except ValidationError as exc:
        raise _lab_validation_error(exc) from exc


def handle_get_a3_md_status(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/lab/a3/md-status — capacidad MD A3 env (sin secrets) F105."""
    from quantlab.brokers.a3.md_backend import a3_md_capability_status

    _ = state
    return a3_md_capability_status()


def handle_get_diagnostics(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/diagnostics — snapshot read-only agregado para soporte (F95).

    Compone versión, modo, salud, conexión y estado de reconciliación en un
    único payload. No muta estado ni reconstruye archivos.
    """
    from quantlab.workbench.about import PHASES_SUMMARY

    session = state.ensure_session()

    health = run_health_checks().to_dict()
    checks = health.get("checks", [])
    checks_total = len(checks) if isinstance(checks, list) else 0
    checks_ok = (
        sum(1 for c in checks if isinstance(c, dict) and c.get("ok") is True)
        if isinstance(checks, list)
        else 0
    )

    recon: dict[str, Any]
    try:
        report = state.check_paper_reconciliation()
        recon = {"ok": report.ok, "status": report.status}
    except ValidationError as exc:
        recon = {"ok": False, "status": "error", "detail": str(exc)}

    return {
        "ok": True,
        "kind": "diagnostics",
        "version": __version__,
        "phases_summary": PHASES_SUMMARY,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "mode": state.mode.value,
        "real_alias": REAL_ALIAS.value,
        "session_id": session.session_id,
        "connected_venue": state.venue,
        "md_provider": state.md_provider,
        "md_source": state.md_source,
        "broker_connected": state.broker is not None,
        "paper_kill_engaged": state.paper_kill_engaged is True,
        "health": {
            "status": health.get("status"),
            "checks_ok": checks_ok,
            "checks_total": checks_total,
        },
        "reconciliation": recon,
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
        "session_id": session.session_id,
        "session_parent": str(state.resolve_session_parent()),
    }
    out.update(_md_info(state))
    return out


def handle_get_sessions(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/sessions — lista dirs de sesión bajo session root (F46)."""
    current = state.ensure_session()
    parent = state.resolve_session_parent()
    sessions = list_sessions(parent)
    for item in sessions:
        item["current"] = item["session_id"] == current.session_id
    return {
        "ok": True,
        "kind": "sessions",
        "session_id": current.session_id,
        "session_parent": str(parent),
        "count": len(sessions),
        "sessions": sessions,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }


def handle_post_sessions_switch(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    """POST /api/sessions/switch — cambia a otra sesión (fail-closed)."""
    raw = body.get("session_id")
    if not isinstance(raw, str) or not raw.strip():
        raise ApiError(400, "session_id requerido")
    try:
        session = state.switch_session(raw.strip(), create=False)
    except ValidationError as exc:
        msg = str(exc)
        status = 404 if "no encontrada" in msg else 400
        _activity_error(state, "session_switch", msg)
        raise ApiError(status, msg) from exc
    _record_activity(
        state,
        "session_switch",
        ok=True,
        message=f"switched to {session.session_id}",
        detail={"session_id": session.session_id},
        op="switch",
    )
    return {
        "ok": True,
        "kind": "session_switch",
        "session_id": session.session_id,
        "session": session.to_dict(),
        "session_parent": str(state.resolve_session_parent()),
        "mode": state.mode.value,
        "live_blocked": LIVE_BLOCKED is True,
        "connected_venue": state.venue,
        "md_provider": state.md_provider,
    }


def handle_post_sessions_new(
    state: WorkbenchState, body: dict[str, Any] | None = None
) -> dict[str, Any]:
    """POST /api/sessions/new — crea sesión nueva y switch (F46)."""
    payload = body if isinstance(body, dict) else {}
    raw = payload.get("session_id")
    sid: str | None = None
    if raw is not None:
        if not isinstance(raw, str):
            raise ApiError(400, "session_id debe ser string")
        sid = raw.strip() or None
    try:
        session = state.new_session(sid)
    except ValidationError as exc:
        msg = str(exc)
        _activity_error(state, "session_new", msg)
        raise ApiError(400, msg) from exc
    _record_activity(
        state,
        "session_new",
        ok=True,
        message=f"created session {session.session_id}",
        detail={"session_id": session.session_id},
        op="new",
    )
    return {
        "ok": True,
        "kind": "session_new",
        "session_id": session.session_id,
        "session": session.to_dict(),
        "session_parent": str(state.resolve_session_parent()),
        "mode": state.mode.value,
        "live_blocked": LIVE_BLOCKED is True,
        "created": True,
    }


def handle_get_session_export(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/session/export — ZIP research-safe de la sesión (path + meta)."""
    session = state.ensure_session()
    try:
        result = export_session(session)
        write_export_sidecar_sha(result)
    except ValidationError as exc:
        _activity_error(state, "export", str(exc))
        raise ApiError(400, str(exc)) from exc
    out = export_result_to_dict(result)
    _record_activity(
        state,
        "export",
        ok=True,
        message="session zip export",
        detail={
            "filename": out.get("filename"),
            "files_count": out.get("files_count"),
        },
    )
    return out


def handle_get_backups(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/backups — lista ZIPs en session/backups/ (F63)."""
    session = state.ensure_session()
    try:
        return list_backups(session)
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc


def handle_post_backups_run(state: WorkbenchState) -> dict[str, Any]:
    """POST /api/backups/run — trigger manual run_auto_backup (F64)."""
    session = state.ensure_session()
    try:
        result = run_auto_backup(session)
        write_export_sidecar_sha(result)
    except ValidationError as exc:
        _activity_error(state, "backup", str(exc))
        raise ApiError(400, str(exc)) from exc
    export_meta = export_result_to_dict(result)
    listed = list_backups(session)
    _record_activity(
        state,
        "backup",
        ok=True,
        message="manual session backup",
        detail={
            "filename": export_meta.get("filename"),
            "bytes": export_meta.get("bytes"),
            "count": listed.get("count"),
        },
    )
    return {
        "ok": True,
        "kind": "backup_run",
        "session_id": session.session_id,
        "filename": export_meta.get("filename"),
        "path": export_meta.get("path"),
        "bytes": export_meta.get("bytes"),
        "sha256": export_meta.get("sha256"),
        "files_count": export_meta.get("files_count"),
        "backups": listed.get("backups", []),
        "count": listed.get("count", 0),
        "max_keep": listed.get("max_keep"),
        "auto_backup_minutes": listed.get("auto_backup_minutes"),
        "auto_backup_enabled": listed.get("auto_backup_enabled"),
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
        "banner": "manual backup research-safe — ZIP allowlist · rotación max 5 · sin LIVE",
    }


def handle_post_session_import(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    """POST /api/session/import — ZIP → sesión nueva o merge fail-closed."""
    session = state.ensure_session()
    mode_raw = body.get("mode", "new")
    if not isinstance(mode_raw, str) or mode_raw not in ("new", "merge"):
        _activity_error(state, "export", "mode debe ser 'new' o 'merge'")
        raise ApiError(400, "mode debe ser 'new' o 'merge'")
    mode: str = mode_raw
    sid_raw = body.get("session_id")
    session_id: str | None = None
    if sid_raw is not None:
        if not isinstance(sid_raw, str):
            _activity_error(state, "export", "session_id debe ser string")
            raise ApiError(400, "session_id debe ser string")
        session_id = sid_raw.strip() or None

    zip_path_raw = body.get("zip_path")
    zip_b64_raw = body.get("zip_base64")
    zip_path = zip_path_raw if isinstance(zip_path_raw, str) else None
    zip_b64 = zip_b64_raw if isinstance(zip_b64_raw, str) else None

    work = make_temp_work_dir()
    owned_upload = False
    try:
        try:
            parent = session.root.parent.resolve()
            archive = resolve_upload_archive(
                zip_path=zip_path,
                zip_base64=zip_b64,
                work_dir=work,
                allowed_roots=(parent,),
            )
            owned_upload = zip_b64 is not None and bool(zip_b64.strip())
        except ValidationError as exc:
            _activity_error(state, "export", str(exc))
            raise ApiError(400, str(exc)) from exc

        parent = session.root.parent
        try:
            if mode == "new":
                result = import_session_zip(
                    archive,
                    session_parent=parent,
                    mode="new",
                    session_id=session_id,
                )
            else:
                result = import_session_zip(
                    archive,
                    session_parent=parent,
                    mode="merge",
                    merge_into=session,
                )
                # Rehidrata book/journal tras merge.
                state._hydrate_from_session()
        except ValidationError as exc:
            _activity_error(state, "export", str(exc))
            raise ApiError(400, str(exc)) from exc
        out = import_result_to_dict(result)
        _record_activity(
            state,
            "export",
            ok=True,
            message=f"session zip import ({mode})",
            detail={
                "mode": mode,
                "session_id": out.get("session_id"),
                "files_written": out.get("files_written"),
            },
        )
        return out
    finally:
        if owned_upload:
            rmtree_quiet(work)
        else:
            rmtree_quiet(work)


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


def handle_get_presets(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/presets — catálogo built-in + custom de sesión (F40/F80)."""
    session = state.ensure_session()
    payload = list_presets(session.presets_dir)
    payload["session_id"] = session.session_id
    return payload


def handle_post_presets_apply(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    """POST /api/presets/apply — aplica preset (built-in o custom) a layout.json."""
    session = state.ensure_session()
    name = body.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ApiError(400, "body.name requerido (research|trading_paper|ops|custom)")
    try:
        result = apply_preset(
            session.layout_path, name.strip(), session.presets_dir
        )
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    result["session_id"] = session.session_id
    return result


def handle_post_presets_save(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    """POST /api/presets/save — guarda layout.json actual como preset custom (F80)."""
    session = state.ensure_session()
    name = body.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ApiError(400, "body.name requerido (preset custom)")
    label = body.get("label")
    description = body.get("description")
    try:
        result = save_custom_preset(
            session.layout_path,
            session.presets_dir,
            name.strip(),
            label=label if isinstance(label, str) else None,
            description=description if isinstance(description, str) else None,
        )
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    result["session_id"] = session.session_id
    return result


def handle_delete_presets(state: WorkbenchState, name: str) -> dict[str, Any]:
    """DELETE /api/presets/{name} — borra preset custom (F81); built-ins inmutables."""
    session = state.ensure_session()
    if not isinstance(name, str) or not name.strip():
        raise ApiError(400, "preset name requerido en /api/presets/{name}")
    try:
        result = delete_custom_preset(session.presets_dir, name.strip())
    except ValidationError as exc:
        msg = str(exc)
        status = 404 if "no encontrado" in msg.lower() else 400
        raise ApiError(status, msg) from exc
    result["session_id"] = session.session_id
    return result


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
    """GET /api/settings — preferencias (access_log / backup / notif / sound / timezone)."""
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
        "allowed_locales": ["en", "es"],
        "allowed_timezones": ["UTC", "local"],
    }


def handle_get_i18n(state: WorkbenchState, locale: str) -> dict[str, Any]:
    """GET /api/i18n/{locale} — diccionario UI (F60 scaffold; default es)."""
    _ = state  # sesión no requerida; surface read-only research-safe
    try:
        payload = build_i18n_payload(locale)
    except ValidationError as exc:
        msg = str(exc)
        status = 404 if "no encontrado" in msg.lower() else 400
        raise ApiError(status, msg) from exc
    return payload


def handle_put_settings(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    """PUT /api/settings — guarda settings en ``settings.json`` (fail-closed)."""
    session = state.ensure_session()
    if "settings" in body and isinstance(body["settings"], dict):
        payload = body["settings"]
    elif any(
        k in body
        for k in (
            "theme",
            "default_venue",
            "default_strategy",
            "slippage_bps",
            "locale",
            "access_log",
            "auto_backup_minutes",
            "desktop_notifications",
            "sound_alerts",
            "timezone",
            "version",
        )
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
            "access_log",
            "auto_backup_minutes",
            "desktop_notifications",
            "sound_alerts",
            "timezone",
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
    # Re-sincroniza scheduler F63 si ya está adjunto (create_server / launch).
    sched = getattr(state, "auto_backup_scheduler", None)
    if sched is not None and hasattr(sched, "notify_settings_changed"):
        sched.notify_settings_changed()
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


def handle_get_watchlist_export(state: WorkbenchState) -> tuple[bytes, str]:
    """GET /api/watchlist/export — JSON download de la watchlist (F79)."""
    session = state.ensure_session()
    try:
        watchlist = load_watchlist(session.watchlist_path)
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    text = export_watchlist_json(watchlist)
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in session.session_id)[
        :64
    ]
    filename = f"quantlab-watchlist-{safe or 'session'}.json"
    return text.encode("utf-8"), filename


def handle_post_watchlist_import(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    """POST /api/watchlist/import — merge/replace símbolos desde JSON (F79).

    Body:
    - ``{"symbols": [...], "mode": "merge"|"replace"}``
    - ``{"watchlist": {"symbols": [...]}, "mode": ...}``
    """
    session = state.ensure_session()
    try:
        mode = parse_import_mode(body.get("mode", "merge"))
        if "symbols" in body:
            raw_symbols = body["symbols"]
            if not isinstance(raw_symbols, list):
                raise ValidationError("watchlist.import symbols debe ser lista")
            symbols = [str(x) for x in raw_symbols]
        elif "watchlist" in body and isinstance(body["watchlist"], dict):
            wl_raw = body["watchlist"].get("symbols", [])
            if not isinstance(wl_raw, list):
                raise ValidationError("watchlist.import watchlist.symbols debe ser lista")
            symbols = [str(x) for x in wl_raw]
        else:
            raise ValidationError("body debe incluir symbols o watchlist")
        current = load_watchlist(session.watchlist_path)
        before = list(current["symbols"])
        next_wl = import_symbols(current, symbols, mode=mode)
        saved = save_watchlist(session.watchlist_path, next_wl)
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    return {
        "ok": True,
        "import": True,
        "mode": mode,
        "watchlist": saved,
        "symbols": list(saved["symbols"]),
        "before_count": len(before),
        "after_count": len(saved["symbols"]),
        "imported_count": len(symbols),
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
        "paper_kill_engaged": state.paper_kill_engaged is True,
    }


def handle_get_risk_utilization(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/risk/utilization — % used max_qty/notional vs book (F69)."""
    session = state.ensure_session()
    session.ensure_layout()
    book = state.ensure_book()
    if state.broker is not None and isinstance(state.broker, PaperBroker):
        payload = utilization_from_broker(state.broker, state.risk)
    else:
        payload = utilization_from_book(book, state.risk)
    payload["session_id"] = session.session_id
    return payload


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
    """GET /api/venues — registro de brokers (F93: enriquecido, read-only)."""
    from quantlab.brokers.contracts.v1 import (
        BROKER_PLUGIN_API_VERSION,
        BROKER_PLUGIN_CAPABILITIES,
    )

    plugin_venues = state.registry.list_plugin_venues()
    return {
        "venues": state.registry.list_venues(),
        "plugin_venues": plugin_venues,
        "connected_venue": state.venue,
        "md_provider": state.md_provider,
        "mode": state.mode.value,
        "live_blocked": LIVE_BLOCKED is True,
        "plugin_contract": {
            "api_version": BROKER_PLUGIN_API_VERSION,
            "allowed_capabilities": sorted(BROKER_PLUGIN_CAPABILITIES),
            "read_only_wrapper": "ReadOnlyBrokerPort",
            "execution": "blocked",
        },
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


def _validate_csv_path(raw: str) -> str:
    """Fail-closed F43: rechaza traversal / null byte en csv_path del workbench."""
    if not isinstance(raw, str) or not raw.strip():
        raise ApiError(400, "campo 'csv_path' inválido")
    if "\x00" in raw:
        raise ApiError(400, "csv_path inválido (null byte)")
    text = raw.strip().replace("\\", "/")
    parts = Path(text).parts
    if any(p == ".." for p in parts) or ".." in text:
        raise ApiError(400, "csv_path path traversal rechazado")
    return raw.strip()


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
    try:
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
            create_opts["csv_path"] = _validate_csv_path(csv_path)

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
            _record_equity_point(state)

        broker: BrokerPort = PaperBroker(
            md,
            journal=journal,
            book=book,
            slippage_bps=slippage_bps,
            on_book_change=_on_book_change,
            reconciliation_required=not bool(
                state.paper_reconciliation is not None
                and state.paper_reconciliation.ok
            ),
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
        # F76: persist last connect params in session meta for reconnect.
        persist_body: dict[str, Any] = {
            "venue": venue,
            "mode": mode.value,
            "slippage_bps": str(slippage_bps),
        }
        if md_source is not None:
            persist_body["md_source"] = md_source
        elif state.md_source:
            persist_body["md_source"] = state.md_source
        if "csv_path" in create_opts:
            persist_body["csv_path"] = create_opts["csv_path"]
        try:
            saved = save_last_connect(state.ensure_session(), persist_body)
        except ValidationError as exc:
            raise ApiError(400, str(exc)) from exc
        out = {
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
            "last_connect": saved,
        }
        _record_activity(
            state,
            "connect",
            ok=True,
            message=f"connected {venue}",
            detail={"venue": venue, "mode": mode.value},
        )
        return out
    except ApiError as exc:
        _activity_error(state, "connect", exc.message)
        raise


def handle_post_broker_reconnect(
    state: WorkbenchState, body: dict[str, Any] | None = None
) -> dict[str, Any]:
    """POST /api/broker/reconnect — re-run last connect params from session meta (F76).

    Body opcional (ignorado; reconnect usa solo session meta). Sin last connect → 400.
    """
    del body  # reserved; reconnect uses session meta only
    session = state.ensure_session()
    try:
        cfg = require_last_connect(session)
    except ValidationError as exc:
        _activity_error(state, "reconnect", str(exc))
        raise ApiError(400, str(exc)) from exc
    # Reutiliza connect (LIVE reject, PaperBroker wrap, persist last_connect).
    out = handle_post_broker_connect(state, dict(cfg))
    status = last_connect_status(session, config=cfg)
    out["reconnect"] = True
    out["kind"] = "broker_reconnect"
    out["has_last_connect"] = status["has_last_connect"]
    out["updated_at"] = status["updated_at"]
    _record_activity(
        state,
        "reconnect",
        ok=True,
        message=f"reconnected {cfg.get('venue')}",
        detail={"venue": cfg.get("venue"), "mode": cfg.get("mode")},
    )
    return out


def handle_post_broker_disconnect(
    state: WorkbenchState, body: dict[str, Any] | None = None
) -> dict[str, Any]:
    """POST /api/broker/disconnect — close broker, clear connected state (F77).

    Conserva ``last_broker_connect`` en meta para reconnect. Idempotente si ya
    estaba desconectado. Body opcional (ignorado).
    """
    del body  # reserved
    session = state.ensure_session()
    cleared = clear_broker_connection(state)
    status = disconnect_status(session, cleared=cleared)
    out: dict[str, Any] = {
        "ok": True,
        "disconnect": True,
        **status,
    }
    venue_label = cleared.get("previous_venue") or "none"
    _record_activity(
        state,
        "disconnect",
        ok=True,
        message=f"disconnected {venue_label}",
        detail={
            "was_connected": cleared.get("was_connected"),
            "previous_venue": cleared.get("previous_venue"),
            "has_last_connect": status["has_last_connect"],
        },
    )
    return out


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


# F75: shell poll interval (seconds) for GET /api/broker/heartbeat
HEARTBEAT_POLL_SECONDS = 5


def handle_get_broker_heartbeat(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/broker/heartbeat — ``broker.health()`` si hay broker; else disconnected.

    No exige connect (HTTP 200 siempre): status ``ok`` | ``fail`` | ``disconnected``.
    Fail-closed sin flip LIVE.
    """
    session = state.ensure_session()
    base: dict[str, Any] = {
        "kind": "broker_heartbeat",
        "session_id": session.session_id,
        "venue": state.venue,
        "md_provider": state.md_provider,
        "poll_seconds": HEARTBEAT_POLL_SECONDS,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }
    if state.broker is None:
        return {
            **base,
            "ok": False,
            "status": "disconnected",
            "heartbeat": "fail",
            "connected": False,
            "health": None,
        }
    try:
        health_raw = state.broker.health()
        health = to_jsonable(health_raw) if health_raw is not None else None
        health_ok = True
        if isinstance(health_raw, dict) and "ok" in health_raw:
            health_ok = bool(health_raw["ok"])
        return {
            **base,
            "ok": health_ok,
            "status": "ok" if health_ok else "fail",
            "heartbeat": "ok" if health_ok else "fail",
            "connected": True,
            "health": health,
        }
    except Exception as exc:  # noqa: BLE001 — heartbeat never raises to client
        return {
            **base,
            "ok": False,
            "status": "fail",
            "heartbeat": "fail",
            "connected": True,
            "health": None,
            "error": str(exc),
        }


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


def handle_get_paper_reconciliation(state: WorkbenchState) -> dict[str, Any]:
    """GET read-only: reporta drift/corrupción; nunca reconstruye archivos."""
    try:
        report = state.check_paper_reconciliation()
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    payload = report.to_dict()
    payload["session_id"] = state.ensure_session().session_id
    payload["rebuild_via"] = "scripts/reconcile_paper_session.py --session PATH --rebuild"
    return payload


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


def handle_post_paper_rehydrate(state: WorkbenchState) -> dict[str, Any]:
    """POST /api/paper/reconciliation/rehydrate — relee sesión desde disco (F91).

    Pensado para después de ``reconcile_paper_session.py --rebuild``: evita
    reiniciar el proceso. No reconstruye archivos; el único rebuild sigue
    siendo el CLI offline. Requiere reconectar broker tras el rehydrate.
    """
    if not LIVE_BLOCKED:
        raise ApiError(400, "LIVE_BLOCKED debe ser True")
    try:
        report = state.rehydrate_session()
    except ValidationError as exc:
        _activity_error(state, "paper.rehydrate", str(exc))
        raise ApiError(400, str(exc)) from exc
    payload = report.to_dict()
    payload["session_id"] = state.ensure_session().session_id
    payload["rehydrated"] = True
    payload["broker_connected"] = state.broker is not None
    payload["rebuild_via"] = "scripts/reconcile_paper_session.py --session PATH --rebuild"
    _record_activity(
        state,
        "rehydrate",
        ok=report.ok,
        message=f"status={report.status}",
        detail={"status": report.status, "issues": list(report.issues)},
        op="paper.rehydrate",
    )
    return payload


def handle_get_paper_kill(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/paper/kill — estado del paper kill switch (F70)."""
    return state.paper_kill_status()


def handle_post_paper_kill(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    """POST /api/paper/kill — {engaged: bool}; persiste en session meta."""
    if not LIVE_BLOCKED:
        raise ApiError(400, "LIVE_BLOCKED debe ser True")
    raw = body.get("engaged")
    if not isinstance(raw, bool):
        raise ApiError(400, "campo 'engaged' requerido (bool)")
    try:
        status = state.set_paper_kill(raw)
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    status["ok"] = True
    return status


def handle_post_paper_submit(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    try:
        _reject_live_mode(state.mode)
        if state.mode not in (OperatingMode.TESTER, OperatingMode.PAPER):
            raise ApiError(400, "paper/submit solo en modos tester|paper")
        try:
            state.assert_paper_kill_clear()
        except ValidationError as exc:
            raise ApiError(400, str(exc)) from exc

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
        out = {
            "ack": dataclass_to_dict(ack),
            "account": account,
            "positions": [dataclass_to_dict(p) for p in broker.get_positions()],
        }
        _record_activity(
            state,
            "submit",
            ok=True,
            message=f"submit {intent.intent_type.value}",
            detail={
                "intent_type": intent.intent_type.value,
                "instrument_id": intent.instrument_id,
                "side": getattr(intent.side, "value", str(intent.side)),
            },
        )
        return out
    except ApiError as exc:
        _activity_error(state, "submit", exc.message)
        raise


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

    def _on_step(_summary: dict[str, Any]) -> None:
        state.persist_book()
        _record_equity_point(state)

    state.paper_session = PaperSessionRunner(
        broker,
        state.risk,
        book,
        on_book_persist=state.persist_book,
        on_step=_on_step,
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


def handle_post_shutdown(
    state: WorkbenchState,
    *,
    client_ip: str = "127.0.0.1",
    stop_server: bool = True,
) -> dict[str, Any]:
    """POST /api/shutdown — solo loopback; marca flag y dispara graceful shutdown.

    Pensado para tests/automatización. El camino normal de usuario es
    SIGINT/SIGTERM en ``quantlab-workbench`` (``launch.py``).
    """
    if not is_loopback_client(client_ip):
        raise ApiError(403, "POST /api/shutdown solo permitido desde loopback")
    if not LIVE_BLOCKED:
        raise ApiError(400, "LIVE_BLOCKED debe ser True")
    result = perform_graceful_shutdown(
        state,
        reason="api:/api/shutdown",
        stop_server=stop_server,
    )
    result["client_ip"] = client_ip
    result["shutdown_requested"] = state.shutdown_requested is True
    return result


def handle_post_paper_session_step(state: WorkbenchState) -> dict[str, Any]:
    """POST /api/paper/session/step — un tick manual."""
    if not LIVE_BLOCKED:
        raise ApiError(400, "LIVE_BLOCKED debe ser True")
    try:
        state.assert_paper_kill_clear()
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
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


def handle_get_paper_equity(state: WorkbenchState, query: str = "") -> dict[str, Any]:
    """GET /api/paper/equity?limit=200 — últimos puntos equity.jsonl (F66)."""
    session = state.ensure_session()
    session.ensure_layout()
    params = parse_qs(query, keep_blank_values=False)
    limit: int | None = None
    raw_limit = params.get("limit")
    if raw_limit and raw_limit[0].strip():
        try:
            limit = int(raw_limit[0].strip())
        except ValueError as exc:
            raise ApiError(400, "limit debe ser int") from exc
    try:
        payload = list_equity(session.equity_path, limit=limit)
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    payload["session_id"] = session.session_id
    payload["limit"] = clamp_equity_limit(limit)
    return payload


def handle_get_paper_pnl(state: WorkbenchState) -> dict[str, Any]:
    """GET /api/paper/pnl — realized/unrealized/equity/cash desde book + marks (F67)."""
    session = state.ensure_session()
    session.ensure_layout()
    book = state.ensure_book()
    if state.broker is not None and isinstance(state.broker, PaperBroker):
        payload = pnl_from_broker(state.broker)
    else:
        payload = pnl_from_book(book)
    payload["session_id"] = session.session_id
    return payload


def handle_get_paper_fills_csv(state: WorkbenchState) -> tuple[bytes, str]:
    """GET /api/paper/fills.csv — body UTF-8 + filename attachment (F65)."""
    journal = state.ensure_journal()
    body = journal.export_csv().encode("utf-8")
    session = state.ensure_session()
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in session.session_id)[
        :64
    ]
    filename = f"quantlab-fills-{safe or 'session'}.csv"
    return body, filename


def handle_get_diagnostics_download(state: WorkbenchState) -> tuple[bytes, str]:
    """GET /api/diagnostics.json — snapshot como descarga adjunta (F96).

    Reutiliza ``handle_get_diagnostics`` (read-only) y lo serializa a un archivo
    para adjuntar a reportes de incidente. No muta estado.
    """
    payload = handle_get_diagnostics(state)
    body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
    session = state.ensure_session()
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in session.session_id)[
        :64
    ]
    filename = f"quantlab-diagnostics-{safe or 'session'}.json"
    return body, filename


def handle_get_support_bundle(state: WorkbenchState) -> tuple[bytes, str]:
    """GET /api/support-bundle.zip — ZIP read-only para soporte (F97).

    Empaqueta diagnostics + about + openapi + venues + reconciliation en un ZIP
    en memoria. No muta estado ni toca journal/book.
    """
    session = state.ensure_session()
    diagnostics = handle_get_diagnostics(state)
    about = handle_get_about(state)
    openapi = handle_get_openapi(state)
    venues = handle_get_venues(state)
    try:
        recon = handle_get_paper_reconciliation(state)
    except ApiError as exc:
        recon = {"ok": False, "error": str(exc), "status": "unavailable"}

    members: dict[str, bytes] = {
        "README.txt": (
            "QuantLab support bundle (read-only)\n"
            f"version={__version__}\n"
            f"session_id={session.session_id}\n"
            "live_blocked=True\n"
            "Contiene: diagnostics.json, about.json, openapi.json,\n"
            "venues.json, reconciliation.json.\n"
            "No incluye journal/book ni credenciales.\n"
        ).encode(),
        "diagnostics.json": json.dumps(diagnostics, indent=2, ensure_ascii=False).encode(
            "utf-8"
        ),
        "about.json": json.dumps(about, indent=2, ensure_ascii=False).encode("utf-8"),
        "openapi.json": json.dumps(openapi, indent=2, ensure_ascii=False).encode("utf-8"),
        "venues.json": json.dumps(venues, indent=2, ensure_ascii=False).encode("utf-8"),
        "reconciliation.json": json.dumps(recon, indent=2, ensure_ascii=False).encode(
            "utf-8"
        ),
    }

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, content in members.items():
            zf.writestr(name, content)
    body = buf.getvalue()
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in session.session_id)[
        :64
    ]
    filename = f"quantlab-support-{safe or 'session'}.zip"
    return body, filename


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
    try:
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
        out = state.store_lab_result(result)
        _record_activity(
            state,
            "backtest",
            ok=True,
            message=f"backtest {strategy_id}",
            detail={
                "strategy_id": strategy_id,
                "n_bars": n_bars,
                "experiment_id": experiment_id,
            },
        )
        return out
    except ApiError as exc:
        _activity_error(state, "backtest", exc.message)
        raise


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
    try:
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
        out = state.store_lab_result(result)
        _record_activity(
            state,
            "optimize",
            ok=True,
            message="optimize grid",
            detail={
                "n_bars": n_bars,
                "n_lookbacks": len(lookbacks),
                "persist": persist,
            },
        )
        return out
    except ApiError as exc:
        _activity_error(state, "optimize", exc.message)
        raise


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


def handle_get_chat_history(state: WorkbenchState) -> dict[str, Any]:
    return state.ensure_chat().history_payload()


def handle_post_chat_clear(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    _ = body
    return state.ensure_chat().clear_history()


def handle_post_chat(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    message = body.get("message")
    if not isinstance(message, str) or not message.strip():
        raise ApiError(400, "campo 'message' requerido (string no vacío)")
    ui_context = body.get("context")
    ui_ctx = ui_context if isinstance(ui_context, dict) else None
    try:
        return state.ensure_chat().handle_message(message, ui_context=ui_ctx)
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
