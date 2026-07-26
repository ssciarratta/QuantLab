"""ThreadingHTTPServer del workbench (stdlib, loopback por defecto)."""

from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from quantlab.core.exceptions import ValidationError
from quantlab.workbench.api import (
    ApiError,
    WorkbenchState,
    handle_get_about,
    handle_get_account,
    handle_get_activity,
    handle_get_catalog,
    handle_get_chat_tools,
    handle_get_commands,
    handle_get_docs,
    handle_get_docs_content,
    handle_get_health,
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
    handle_get_mode,
    handle_get_onboarding,
    handle_get_ops_metrics,
    handle_get_ops_prometheus,
    handle_get_paper_book,
    handle_get_paper_fills,
    handle_get_paper_session_status,
    handle_get_positions,
    handle_get_presets,
    handle_get_risk,
    handle_get_session,
    handle_get_session_export,
    handle_get_settings,
    handle_get_snapshot,
    handle_get_universe,
    handle_get_venues,
    handle_get_watchlist,
    handle_post_broker_connect,
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
    handle_post_paper_session_start,
    handle_post_paper_session_step,
    handle_post_paper_session_stop,
    handle_post_paper_submit,
    handle_post_presets_apply,
    handle_post_session_import,
    handle_put_layout,
    handle_put_settings,
    handle_put_watchlist,
)

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

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _send_download(self, body: bytes, *, filename: str, content_type: str) -> None:
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
            st, body, ctype = _json_bytes(payload, status)
            self._send(st, body, ctype)

        def _send_error_json(self, status: int, message: str) -> None:
            self._send_json({"ok": False, "error": message}, status=status)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path

            try:
                if path == "/api/health":
                    self._send_json(handle_get_health(state))
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
                if path == "/api/paper/book":
                    self._send_json(handle_get_paper_book(state))
                    return
                if path == "/api/paper/fills":
                    self._send_json(handle_get_paper_fills(state))
                    return
                if path == "/api/paper/session/status":
                    self._send_json(handle_get_paper_session_status(state))
                    return
                if path == "/api/session":
                    self._send_json(handle_get_session(state))
                    return
                if path == "/api/activity":
                    self._send_json(handle_get_activity(state, parsed.query))
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
                if path == "/api/universe":
                    self._send_json(handle_get_universe(state))
                    return
                if path == "/api/catalog":
                    self._send_json(handle_get_catalog(state))
                    return
                if path == "/api/risk":
                    self._send_json(handle_get_risk(state))
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
                if path == "/api/paper/submit":
                    self._send_json(handle_post_paper_submit(state, body))
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
                if path == "/api/presets/apply":
                    self._send_json(handle_post_presets_apply(state, body))
                    return
                self._send_error_json(404, f"ruta no encontrada: {path}")
            except ApiError as exc:
                self._send_error_json(exc.status, exc.message)
            except Exception as exc:  # noqa: BLE001
                self._send_error_json(500, str(exc))

        def do_PUT(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path
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
    # Exponer estado para tests
    server.workbench_state = app_state  # type: ignore[attr-defined]
    return server
