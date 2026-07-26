"""ThreadingHTTPServer del workbench (stdlib, loopback por defecto)."""

from __future__ import annotations

import json
import mimetypes
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from quantlab.core.exceptions import ValidationError
from quantlab.workbench.api import (
    ApiError,
    WorkbenchState,
    handle_delete_presets,
    handle_get_about,
    handle_get_access_log,
    handle_get_account,
    handle_get_activity,
    handle_get_backups,
    handle_get_broker_heartbeat,
    handle_get_catalog,
    handle_get_chat_tools,
    handle_get_commands,
    handle_get_diagnostics,
    handle_get_docs,
    handle_get_docs_content,
    handle_get_health,
    handle_get_i18n,
    handle_get_instruments,
    handle_get_lab_capabilities,
    handle_get_lab_experiments,
    handle_get_lab_export,
    handle_get_lab_exports,
    handle_get_lab_features_store,
    handle_get_lab_metrics,
    handle_get_lab_montecarlo_history,
    handle_get_lab_montecarlo_run,
    handle_get_lab_optimize_history,
    handle_get_lab_optimize_run,
    handle_get_lab_report,
    handle_get_lab_reports,
    handle_get_lab_strategies,
    handle_get_lab_validation,
    handle_get_lab_validation_run,
    handle_get_layout,
    handle_get_livez,
    handle_get_mode,
    handle_get_onboarding,
    handle_get_openapi,
    handle_get_ops_metrics,
    handle_get_ops_prometheus,
    handle_get_paper_book,
    handle_get_paper_equity,
    handle_get_paper_fills,
    handle_get_paper_fills_csv,
    handle_get_paper_kill,
    handle_get_paper_pnl,
    handle_get_paper_reconciliation,
    handle_get_paper_session_status,
    handle_get_positions,
    handle_get_presets,
    handle_get_readyz,
    handle_get_risk,
    handle_get_risk_utilization,
    handle_get_session,
    handle_get_session_export,
    handle_get_sessions,
    handle_get_settings,
    handle_get_snapshot,
    handle_get_universe,
    handle_get_venues,
    handle_get_watchlist,
    handle_get_watchlist_export,
    handle_post_backups_run,
    handle_post_broker_connect,
    handle_post_broker_disconnect,
    handle_post_broker_reconnect,
    handle_post_chat,
    handle_post_lab_backtest,
    handle_post_lab_export_hb,
    handle_post_lab_features,
    handle_post_lab_montecarlo,
    handle_post_lab_optimize,
    handle_post_lab_scanner,
    handle_post_lab_validation_run,
    handle_post_mode,
    handle_post_onboarding_complete,
    handle_post_paper_kill,
    handle_post_paper_rehydrate,
    handle_post_paper_session_start,
    handle_post_paper_session_step,
    handle_post_paper_session_stop,
    handle_post_paper_submit,
    handle_post_presets_apply,
    handle_post_presets_save,
    handle_post_session_import,
    handle_post_sessions_new,
    handle_post_sessions_switch,
    handle_post_shutdown,
    handle_post_watchlist_import,
    handle_put_layout,
    handle_put_settings,
    handle_put_watchlist,
    record_http_access,
)
from quantlab.workbench.auto_backup import ensure_auto_backup_scheduler
from quantlab.workbench.rate_limit import rate_limit_error_payload
from quantlab.workbench.security_headers import (
    ACCESS_CONTROL_ALLOW_ORIGIN,
    CACHE_CONTROL_NO_STORE,
    SECURITY_HEADERS,
    cors_allow_origin,
    wants_api_no_store,
)
from quantlab.workbench.shutdown import bind_http_server, is_loopback_client

STATIC_ROOT = Path(__file__).resolve().parent / "static"

# F43 red-team: body JSON acotado (import ZIP tiene techo propio).
DEFAULT_MAX_BODY_BYTES = 2_000_000
SESSION_IMPORT_MAX_BODY_BYTES = 55_000_000

LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})


def is_loopback_host(host: str) -> bool:
    """True si host es loopback (127.0.0.1 / ::1 / localhost)."""
    h = host.strip().lower()
    if h.startswith("[") and h.endswith("]"):
        h = h[1:-1]
    return h in LOOPBACK_HOSTS


def _json_bytes(payload: dict[str, Any], status: int = 200) -> tuple[int, bytes, str]:
    body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return status, body, "application/json; charset=utf-8"


def _client_ip(handler: BaseHTTPRequestHandler) -> str:
    """IP del peer (ThreadingHTTPServer client_address)."""
    try:
        return str(handler.client_address[0])
    except (AttributeError, IndexError, TypeError):
        return "unknown"


def _read_json(
    handler: BaseHTTPRequestHandler, *, max_bytes: int = DEFAULT_MAX_BODY_BYTES
) -> dict[str, Any]:
    length_raw = handler.headers.get("Content-Length", "0")
    try:
        length = int(length_raw)
    except ValueError as exc:
        raise ApiError(400, "Content-Length inválido") from exc
    if length < 0 or length > max_bytes:
        raise ApiError(400, "body demasiado grande")
    raw = handler.rfile.read(length) if length else b"{}"
    if not raw:
        return {}
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ApiError(400, f"JSON inválido: {exc}") from exc
    if not isinstance(data, dict):
        raise ApiError(400, "body JSON debe ser un objeto")
    return data


def _wants_download(query: str) -> bool:
    from urllib.parse import parse_qs

    qs = parse_qs(query)
    raw = (qs.get("download") or qs.get("format") or ["0"])[0].strip().lower()
    return raw in {"1", "true", "yes", "zip"}


def _path_segment_ok(segment: str) -> bool:
    """Fail-closed: un segmento de URL sin separators ni traversal."""
    if not segment or segment in {".", ".."}:
        return False
    return "/" not in segment and "\\" not in segment and ".." not in segment


def _safe_static_path(url_path: str) -> Path | None:
    """Resuelve path bajo STATIC_ROOT; None si traversal o inexistente."""
    rel = unquote(url_path).lstrip("/")
    # Acepta /static/... y /api/static/...
    for prefix in ("api/static/", "static/"):
        if rel.startswith(prefix):
            rel = rel[len(prefix) :]
            break
    else:
        return None
    if not rel or ".." in Path(rel).parts:
        return None
    candidate = (STATIC_ROOT / rel).resolve()
    try:
        candidate.relative_to(STATIC_ROOT.resolve())
    except ValueError:
        return None
    if candidate.is_file():
        return candidate
    return None


def make_handler(state: WorkbenchState) -> type[BaseHTTPRequestHandler]:
    """Factory de handler con estado de sesión compartido."""

    class WorkbenchHandler(BaseHTTPRequestHandler):
        server_version = "QuantLabWorkbench/0.15"

        def log_message(self, fmt: str, *args: object) -> None:
            # Silencioso en tests; útil en CLI vía print override opcional.
            pass

        def _begin_access(self, method: str, path: str) -> None:
            """F61: marca inicio de request para access.jsonl."""
            self._ql_access_t0 = time.perf_counter()
            self._ql_access_method = method
            self._ql_access_path = path
            self._ql_access_logged = False

        def _finish_access(self, status: int) -> None:
            """F61: append method/path/status/ms (sin bodies/secrets)."""
            if getattr(self, "_ql_access_logged", False):
                return
            self._ql_access_logged = True
            t0 = getattr(self, "_ql_access_t0", None)
            ms = round((time.perf_counter() - t0) * 1000.0, 3) if t0 is not None else 0.0
            record_http_access(
                state,
                method=str(getattr(self, "_ql_access_method", self.command or "GET")),
                path=str(getattr(self, "_ql_access_path", getattr(self, "_ql_path", "/"))),
                status=int(status),
                ms=ms,
            )

        def _apply_security_headers(self, path: str) -> None:
            """F56/F57: nosniff / DENY / no-referrer / CSP; no-store en /api/*; CORS fail-closed."""
            for name, value in SECURITY_HEADERS.items():
                self.send_header(name, value)
            if wants_api_no_store(path):
                self.send_header("Cache-Control", CACHE_CONTROL_NO_STORE)
            origin = self.headers.get("Origin")
            allow = cors_allow_origin(origin)
            # Nunca Access-Control-Allow-Origin: * ; no reflejar Origin non-loopback.
            if allow is not None:
                self.send_header(ACCESS_CONTROL_ALLOW_ORIGIN, allow)

        def _send(
            self, status: int, body: bytes, content_type: str, *, path: str | None = None
        ) -> None:
            route = path if path is not None else getattr(self, "_ql_path", "/api/")
            # Log antes de enviar bytes: evita race keep-alive / 2ª conexión
            # (cliente lee access-log antes de que termine append del request previo).
            self._finish_access(status)
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self._apply_security_headers(route)
            self.end_headers()
            self.wfile.write(body)

        def _send_download(
            self, body: bytes, *, filename: str, content_type: str, path: str | None = None
        ) -> None:
            route = path if path is not None else getattr(self, "_ql_path", "/api/")
            self._finish_access(200)
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self._apply_security_headers(route)
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
            st, body, ctype = _json_bytes(payload, status)
            self._send(st, body, ctype)

        def _send_error_json(self, status: int, message: str) -> None:
            self._send_json({"ok": False, "error": message}, status=status)

        def _check_rate_limit(self, path: str) -> bool:
            """Soft rate limit F51. Returns False si ya respondió 429."""
            decision = state.rate_limiter.allow(_client_ip(self), path)
            if decision.allowed:
                return True
            payload = rate_limit_error_payload(decision)
            status, body, ctype = _json_bytes(payload, 429)
            self._finish_access(429)
            self.send_response(429)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self._apply_security_headers(path)
            retry = max(1, int(decision.retry_after_s + 0.999))
            self.send_header("Retry-After", str(retry))
            self.end_headers()
            self.wfile.write(body)
            return False

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path
            self._ql_path = path
            self._begin_access("GET", path)
            if not self._check_rate_limit(path):
                return

            try:
                if path == "/api/livez":
                    self._send_json(handle_get_livez(state))
                    return
                if path == "/api/readyz":
                    payload = handle_get_readyz(state)
                    status = 200 if payload.get("ready") else 503
                    self._send_json(payload, status=status)
                    return
                if path == "/api/health":
                    self._send_json(handle_get_health(state))
                    return
                if path == "/api/openapi.json":
                    self._send_json(handle_get_openapi(state))
                    return
                if path == "/api/about":
                    self._send_json(handle_get_about(state))
                    return
                if path == "/api/commands":
                    self._send_json(handle_get_commands(state))
                    return
                if path == "/api/mode":
                    self._send_json(handle_get_mode(state))
                    return
                if path == "/api/diagnostics":
                    self._send_json(handle_get_diagnostics(state))
                    return
                if path == "/api/venues":
                    self._send_json(handle_get_venues(state))
                    return
                if path == "/api/broker/instruments":
                    self._send_json(handle_get_instruments(state))
                    return
                if path == "/api/broker/snapshot":
                    self._send_json(handle_get_snapshot(state, parsed.query))
                    return
                if path == "/api/broker/account":
                    self._send_json(handle_get_account(state))
                    return
                if path == "/api/broker/positions":
                    self._send_json(handle_get_positions(state))
                    return
                if path == "/api/broker/heartbeat":
                    self._send_json(handle_get_broker_heartbeat(state))
                    return
                if path == "/api/paper/book":
                    self._send_json(handle_get_paper_book(state))
                    return
                if path == "/api/paper/fills":
                    self._send_json(handle_get_paper_fills(state))
                    return
                if path == "/api/paper/equity":
                    self._send_json(handle_get_paper_equity(state, parsed.query))
                    return
                if path == "/api/paper/pnl":
                    self._send_json(handle_get_paper_pnl(state))
                    return
                if path == "/api/paper/reconciliation":
                    self._send_json(handle_get_paper_reconciliation(state))
                    return
                if path == "/api/paper/fills.csv":
                    body, filename = handle_get_paper_fills_csv(state)
                    self._send_download(
                        body,
                        filename=filename,
                        content_type="text/csv; charset=utf-8",
                    )
                    return
                if path == "/api/paper/session/status":
                    self._send_json(handle_get_paper_session_status(state))
                    return
                if path == "/api/paper/kill":
                    self._send_json(handle_get_paper_kill(state))
                    return
                if path == "/api/session":
                    self._send_json(handle_get_session(state))
                    return
                if path == "/api/sessions":
                    self._send_json(handle_get_sessions(state))
                    return
                if path == "/api/activity":
                    self._send_json(handle_get_activity(state, parsed.query))
                    return
                if path == "/api/access-log":
                    self._send_json(handle_get_access_log(state, parsed.query))
                    return
                if path == "/api/backups":
                    self._send_json(handle_get_backups(state))
                    return
                if path == "/api/ops/metrics":
                    self._send_json(handle_get_ops_metrics(state))
                    return
                if path == "/api/ops/prometheus":
                    text = handle_get_ops_prometheus(state)
                    self._send(
                        200,
                        text.encode("utf-8"),
                        "text/plain; version=0.0.4; charset=utf-8",
                    )
                    return
                if path == "/api/session/export":
                    payload = handle_get_session_export(state)
                    if _wants_download(parsed.query):
                        zip_path = Path(str(payload["path"]))
                        if not zip_path.is_file():
                            self._send_error_json(404, "ZIP de export no encontrado")
                            return
                        self._send_download(
                            zip_path.read_bytes(),
                            filename=str(payload.get("filename") or zip_path.name),
                            content_type="application/zip",
                        )
                        return
                    self._send_json(payload)
                    return
                if path == "/api/layout":
                    self._send_json(handle_get_layout(state))
                    return
                if path == "/api/presets":
                    self._send_json(handle_get_presets(state))
                    return
                if path == "/api/settings":
                    self._send_json(handle_get_settings(state))
                    return
                if path.startswith("/api/i18n/"):
                    locale = unquote(path[len("/api/i18n/") :]).strip("/")
                    if not locale or "/" in locale:
                        self._send_error_json(400, "locale requerido en /api/i18n/{locale}")
                        return
                    self._send_json(handle_get_i18n(state, locale))
                    return
                if path == "/api/onboarding":
                    self._send_json(handle_get_onboarding(state))
                    return
                if path == "/api/docs":
                    self._send_json(handle_get_docs(state))
                    return
                if path == "/api/docs/content":
                    self._send_json(handle_get_docs_content(state, parsed.query))
                    return
                if path == "/api/watchlist":
                    self._send_json(handle_get_watchlist(state))
                    return
                if path == "/api/watchlist/export":
                    body, filename = handle_get_watchlist_export(state)
                    self._send_download(
                        body,
                        filename=filename,
                        content_type="application/json; charset=utf-8",
                    )
                    return
                if path == "/api/universe":
                    self._send_json(handle_get_universe(state))
                    return
                if path == "/api/catalog":
                    self._send_json(handle_get_catalog(state))
                    return
                if path == "/api/risk":
                    self._send_json(handle_get_risk(state))
                    return
                if path == "/api/risk/utilization":
                    self._send_json(handle_get_risk_utilization(state))
                    return
                if path == "/api/lab/capabilities":
                    self._send_json(handle_get_lab_capabilities(state))
                    return
                if path == "/api/lab/strategies":
                    self._send_json(handle_get_lab_strategies(state))
                    return
                if path == "/api/lab/metrics":
                    self._send_json(handle_get_lab_metrics(state))
                    return
                if path == "/api/lab/experiments":
                    self._send_json(handle_get_lab_experiments(state))
                    return
                if path == "/api/lab/validation":
                    self._send_json(handle_get_lab_validation(state))
                    return
                if path.startswith("/api/lab/validation/"):
                    run_id = unquote(path[len("/api/lab/validation/") :]).strip("/")
                    if not _path_segment_ok(run_id) or run_id == "run":
                        self._send_error_json(400, "run_id inválido")
                        return
                    self._send_json(handle_get_lab_validation_run(state, run_id))
                    return
                if path == "/api/lab/optimize/history":
                    self._send_json(handle_get_lab_optimize_history(state))
                    return
                if path.startswith("/api/lab/optimize/history/"):
                    run_id = unquote(path[len("/api/lab/optimize/history/") :]).strip("/")
                    if not _path_segment_ok(run_id):
                        self._send_error_json(400, "run_id inválido")
                        return
                    self._send_json(handle_get_lab_optimize_run(state, run_id))
                    return
                if path == "/api/lab/montecarlo/history":
                    self._send_json(handle_get_lab_montecarlo_history(state))
                    return
                if path.startswith("/api/lab/montecarlo/history/"):
                    run_id = unquote(path[len("/api/lab/montecarlo/history/") :]).strip("/")
                    if not _path_segment_ok(run_id):
                        self._send_error_json(400, "run_id inválido")
                        return
                    self._send_json(handle_get_lab_montecarlo_run(state, run_id))
                    return
                if path == "/api/lab/exports":
                    self._send_json(handle_get_lab_exports(state))
                    return
                if path.startswith("/api/lab/exports/"):
                    export_id = unquote(path[len("/api/lab/exports/") :]).strip("/")
                    if not _path_segment_ok(export_id):
                        self._send_error_json(400, "export_id inválido")
                        return
                    self._send_json(handle_get_lab_export(state, export_id))
                    return
                if path == "/api/lab/reports":
                    self._send_json(handle_get_lab_reports(state))
                    return
                if path.startswith("/api/lab/reports/"):
                    report_id = unquote(path[len("/api/lab/reports/") :]).strip("/")
                    if not _path_segment_ok(report_id):
                        self._send_error_json(400, "report_id inválido")
                        return
                    self._send_json(handle_get_lab_report(state, report_id))
                    return
                if path == "/api/lab/features/store":
                    self._send_json(handle_get_lab_features_store(state))
                    return
                if path == "/api/chat/tools":
                    self._send_json(handle_get_chat_tools(state))
                    return
                if path in ("/", "/index.html"):
                    index = STATIC_ROOT / "index.html"
                    data = index.read_bytes()
                    self._send(200, data, "text/html; charset=utf-8")
                    return
                static_file = _safe_static_path(path)
                if static_file is not None:
                    data = static_file.read_bytes()
                    ctype, _ = mimetypes.guess_type(str(static_file))
                    self._send(200, data, ctype or "application/octet-stream")
                    return
                self._send_error_json(404, f"ruta no encontrada: {path}")
            except ApiError as exc:
                self._send_error_json(exc.status, exc.message)
            except Exception as exc:  # noqa: BLE001
                self._send_error_json(500, str(exc))

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path
            self._ql_path = path
            self._begin_access("POST", path)
            if not self._check_rate_limit(path):
                return
            try:
                # Import ZIP puede traer base64 grande (hasta ~50 MiB + overhead JSON).
                max_body = (
                    SESSION_IMPORT_MAX_BODY_BYTES
                    if path == "/api/session/import"
                    else DEFAULT_MAX_BODY_BYTES
                )
                body = _read_json(self, max_bytes=max_body)
                if path == "/api/mode":
                    self._send_json(handle_post_mode(state, body))
                    return
                if path == "/api/broker/connect":
                    self._send_json(handle_post_broker_connect(state, body))
                    return
                if path == "/api/broker/reconnect":
                    self._send_json(handle_post_broker_reconnect(state, body))
                    return
                if path == "/api/broker/disconnect":
                    self._send_json(handle_post_broker_disconnect(state, body))
                    return
                if path == "/api/paper/submit":
                    self._send_json(handle_post_paper_submit(state, body))
                    return
                if path == "/api/paper/kill":
                    self._send_json(handle_post_paper_kill(state, body))
                    return
                if path == "/api/paper/reconciliation/rehydrate":
                    self._send_json(handle_post_paper_rehydrate(state))
                    return
                if path == "/api/paper/session/start":
                    self._send_json(handle_post_paper_session_start(state, body))
                    return
                if path == "/api/paper/session/stop":
                    self._send_json(handle_post_paper_session_stop(state))
                    return
                if path == "/api/paper/session/step":
                    self._send_json(handle_post_paper_session_step(state))
                    return
                if path == "/api/lab/backtest":
                    self._send_json(handle_post_lab_backtest(state, body))
                    return
                if path == "/api/lab/scanner":
                    self._send_json(handle_post_lab_scanner(state, body))
                    return
                if path == "/api/lab/optimize":
                    self._send_json(handle_post_lab_optimize(state, body))
                    return
                if path == "/api/lab/montecarlo":
                    self._send_json(handle_post_lab_montecarlo(state, body))
                    return
                if path in ("/api/lab/features", "/api/lab/features/run"):
                    self._send_json(handle_post_lab_features(state, body))
                    return
                if path == "/api/lab/validation/run":
                    self._send_json(handle_post_lab_validation_run(state, body))
                    return
                if path == "/api/lab/export-hb":
                    self._send_json(handle_post_lab_export_hb(state, body))
                    return
                if path == "/api/chat":
                    self._send_json(handle_post_chat(state, body))
                    return
                if path == "/api/onboarding/complete":
                    self._send_json(handle_post_onboarding_complete(state, body))
                    return
                if path == "/api/session/import":
                    self._send_json(handle_post_session_import(state, body))
                    return
                if path == "/api/watchlist/import":
                    self._send_json(handle_post_watchlist_import(state, body))
                    return
                if path == "/api/sessions/switch":
                    self._send_json(handle_post_sessions_switch(state, body))
                    return
                if path == "/api/sessions/new":
                    self._send_json(handle_post_sessions_new(state, body))
                    return
                if path == "/api/backups/run":
                    self._send_json(handle_post_backups_run(state))
                    return
                if path == "/api/presets/apply":
                    self._send_json(handle_post_presets_apply(state, body))
                    return
                if path == "/api/presets/save":
                    self._send_json(handle_post_presets_save(state, body))
                    return
                if path == "/api/shutdown":
                    client_ip = _client_ip(self)
                    if not is_loopback_client(client_ip):
                        self._send_error_json(
                            403, "POST /api/shutdown solo permitido desde loopback"
                        )
                        return
                    self._send_json(
                        handle_post_shutdown(state, client_ip=client_ip, stop_server=True)
                    )
                    return
                self._send_error_json(404, f"ruta no encontrada: {path}")
            except ApiError as exc:
                self._send_error_json(exc.status, exc.message)
            except Exception as exc:  # noqa: BLE001
                self._send_error_json(500, str(exc))

        def do_PUT(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path
            self._ql_path = path
            self._begin_access("PUT", path)
            if not self._check_rate_limit(path):
                return
            try:
                body = _read_json(self)
                if path == "/api/layout":
                    self._send_json(handle_put_layout(state, body))
                    return
                if path == "/api/settings":
                    self._send_json(handle_put_settings(state, body))
                    return
                if path == "/api/watchlist":
                    self._send_json(handle_put_watchlist(state, body))
                    return
                self._send_error_json(404, f"ruta no encontrada: {path}")
            except ApiError as exc:
                self._send_error_json(exc.status, exc.message)
            except Exception as exc:  # noqa: BLE001
                self._send_error_json(500, str(exc))

        def do_DELETE(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path
            self._ql_path = path
            self._begin_access("DELETE", path)
            if not self._check_rate_limit(path):
                return
            try:
                if path.startswith("/api/presets/"):
                    name = unquote(path[len("/api/presets/") :]).strip("/")
                    if not _path_segment_ok(name):
                        self._send_error_json(400, "preset name inválido en DELETE")
                        return
                    self._send_json(handle_delete_presets(state, name))
                    return
                self._send_error_json(404, f"ruta no encontrada: {path}")
            except ApiError as exc:
                self._send_error_json(exc.status, exc.message)
            except Exception as exc:  # noqa: BLE001
                self._send_error_json(500, str(exc))

    return WorkbenchHandler


def create_server(
    host: str = "127.0.0.1",
    port: int = 8765,
    state: WorkbenchState | None = None,
    *,
    allow_non_loopback: bool = False,
) -> ThreadingHTTPServer:
    """Crea ThreadingHTTPServer bound a host:port.

    Fail-closed F43: host non-loopback requiere ``allow_non_loopback=True``.
    """
    if not is_loopback_host(host) and not allow_non_loopback:
        raise ValidationError(
            f"host={host!r} no es loopback; pasar allow_non_loopback=True (riesgo: sin auth HTTP)"
        )
    app_state = state if state is not None else WorkbenchState()
    app_state.bind_host = host
    app_state.allow_non_loopback = bool(allow_non_loopback)
    handler = make_handler(app_state)
    server = ThreadingHTTPServer((host, port), handler)
    # Exponer estado para tests + graceful shutdown (F52)
    server.workbench_state = app_state  # type: ignore[attr-defined]
    bind_http_server(app_state, server)
    # F63: auto-backup scheduler (idle si auto_backup_minutes=0)
    ensure_auto_backup_scheduler(app_state)
    return server
