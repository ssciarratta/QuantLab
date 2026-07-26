"""Broker disconnect — close broker, clear connected state (F77).

Conserva ``last_broker_connect`` en meta para ``POST /api/broker/reconnect``.
Sin flip LIVE.
"""

from __future__ import annotations

import contextlib
from typing import Any

from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.broker_reconnect import last_connect_status, load_last_connect
from quantlab.workbench.session import WorkbenchSession

DISCONNECT_VERSION = 1


def clear_broker_connection(state: Any) -> dict[str, Any]:
    """Cierra broker y limpia campos de conexión en ``WorkbenchState``.

    No toca ``last_broker_connect`` / ``last_broker_connect_updated_at`` en meta.
    Detiene paper session runner si está activo (evita mismatch sin broker).
    """
    previous_venue = getattr(state, "venue", None)
    previous_md_provider = getattr(state, "md_provider", None)
    previous_md_source = getattr(state, "md_source", None)
    was_connected = getattr(state, "broker", None) is not None
    close_info: dict[str, Any] | None = None

    paper_session = getattr(state, "paper_session", None)
    if paper_session is not None:
        with contextlib.suppress(Exception):
            paper_session.stop()
        state.paper_session = None

    broker = getattr(state, "broker", None)
    if broker is not None:
        with contextlib.suppress(Exception):
            raw = broker.close()
            if isinstance(raw, dict):
                close_info = dict(raw)
        state.broker = None

    state.venue = None
    state.md_provider = None
    state.md_source = None

    return {
        "was_connected": was_connected,
        "previous_venue": previous_venue if isinstance(previous_venue, str) else None,
        "previous_md_provider": (
            previous_md_provider if isinstance(previous_md_provider, str) else None
        ),
        "previous_md_source": (
            previous_md_source if isinstance(previous_md_source, str) else None
        ),
        "close": close_info,
    }


def disconnect_status(
    session: WorkbenchSession, *, cleared: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Payload de estado post-disconnect / inspección."""
    cfg = load_last_connect(session)
    lc = last_connect_status(session, config=cfg)
    base: dict[str, Any] = {
        "kind": "broker_disconnect",
        "version": DISCONNECT_VERSION,
        "session_id": session.session_id,
        "connected": False,
        "has_last_connect": lc["has_last_connect"],
        "last_connect": lc["last_connect"],
        "updated_at": lc["updated_at"],
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }
    if cleared is not None:
        base["was_connected"] = cleared.get("was_connected") is True
        base["previous_venue"] = cleared.get("previous_venue")
        base["previous_md_provider"] = cleared.get("previous_md_provider")
        base["previous_md_source"] = cleared.get("previous_md_source")
        base["close"] = cleared.get("close")
    return base
