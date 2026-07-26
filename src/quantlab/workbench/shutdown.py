"""Graceful shutdown + paper session safety (F52).

Orden idempotente:
1. Marca ``shutdown_requested``
2. Detiene ``PaperSessionRunner`` si corre
3. Flush layout.json + settings.json (+ book)
4. Opcional: ``ThreadingHTTPServer.shutdown()`` (otro hilo)

``POST /api/shutdown`` es loopback-only (útil en tests/automatización);
SIGINT/SIGTERM en ``launch.py`` es el camino normal de usuario.
"""

from __future__ import annotations

import contextlib
import threading
from decimal import Decimal
from http.server import ThreadingHTTPServer
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.layout import load_layout, save_layout
from quantlab.workbench.settings import load_settings, save_settings

# Local (no importar server.py): evita ciclo api → shutdown → server → api.
_LOOPBACK_CLIENTS = frozenset({"127.0.0.1", "::1", "localhost"})


def is_loopback_client(client_ip: str) -> bool:
    """True si la IP del peer es loopback (127.0.0.1 / ::1 / localhost)."""
    h = (client_ip or "").strip().lower()
    if h.startswith("[") and h.endswith("]"):
        h = h[1:-1]
    if h.startswith("::ffff:"):
        h = h[7:]
    return h in _LOOPBACK_CLIENTS


def stop_paper_session_if_running(state: Any) -> dict[str, Any]:
    """Detiene el runner paper si existe; no falla si ya estaba parado."""
    runner = getattr(state, "paper_session", None)
    if runner is None:
        return {
            "stopped": False,
            "was_running": False,
            "status": {"running": False, "steps": 0},
        }
    was_running = False
    with contextlib.suppress(Exception):
        st = runner.status()
        was_running = bool(st.get("running")) or bool(st.get("background"))
    status = runner.stop()
    state.paper_session = None
    return {"stopped": True, "was_running": was_running, "status": status}


def flush_layout_settings(state: Any) -> dict[str, Any]:
    """Re-persiste layout.json y settings.json (flush atómico idempotente).

    Sincroniza ``slippage_bps`` del estado en settings antes de guardar.
    """
    session = state.ensure_session()
    layout_flushed = False
    settings_flushed = False
    book_flushed = False

    with contextlib.suppress(OSError, ValidationError):
        layout = load_layout(session.layout_path)
        save_layout(session.layout_path, layout)
        layout_flushed = True

    with contextlib.suppress(OSError, ValidationError, TypeError, ValueError):
        settings = load_settings(session.settings_path)
        merged = dict(settings)
        slip = getattr(state, "slippage_bps", None)
        if slip is not None:
            merged["slippage_bps"] = format(Decimal(str(slip)), "f")
        save_settings(session.settings_path, merged)
        settings_flushed = True

    with contextlib.suppress(OSError, ValidationError):
        if getattr(state, "book", None) is not None:
            state.persist_book()
            book_flushed = True

    return {
        "layout": layout_flushed,
        "settings": settings_flushed,
        "book": book_flushed,
        "session_id": session.session_id,
        "layout_path": str(session.layout_path),
        "settings_path": str(session.settings_path),
    }


def _schedule_server_shutdown(server: ThreadingHTTPServer) -> None:
    """``server.shutdown()`` debe llamarse desde otro hilo (stdlib)."""

    def _run() -> None:
        with contextlib.suppress(Exception):
            server.shutdown()

    threading.Thread(target=_run, name="quantlab-shutdown", daemon=True).start()


def perform_graceful_shutdown(
    state: Any,
    *,
    reason: str = "shutdown",
    stop_server: bool = True,
) -> dict[str, Any]:
    """Shutdown idempotente: paper stop → flush → flag → server.shutdown opcional."""
    lock = getattr(state, "_shutdown_lock", None)
    if lock is None:
        lock = threading.Lock()
        state._shutdown_lock = lock

    with lock:
        already = bool(getattr(state, "shutdown_done", False))
        state.shutdown_requested = True
        state.shutdown_reason = str(reason)

        paper = stop_paper_session_if_running(state)
        flushed = flush_layout_settings(state)

        from quantlab.workbench.auto_backup import stop_auto_backup_scheduler

        stop_auto_backup_scheduler(state)

        server_stopped = False
        if stop_server and not already:
            server = getattr(state, "_http_server", None)
            if isinstance(server, ThreadingHTTPServer):
                _schedule_server_shutdown(server)
                server_stopped = True

        state.shutdown_done = True

        return {
            "ok": True,
            "kind": "shutdown",
            "reason": str(reason),
            "already_done": already,
            "paper": paper,
            "flushed": flushed,
            "server_shutdown_scheduled": server_stopped,
            "live_blocked": LIVE_BLOCKED is True,
            "live_routing": False,
            "research_safe": True,
        }


def bind_http_server(state: Any, server: ThreadingHTTPServer) -> None:
    """Asocia el HTTPServer al state para que shutdown pueda detenerlo."""
    state._http_server = server
