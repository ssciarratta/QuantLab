"""Broker reconnect — re-run last connect params from session meta (F76).

Persiste ``last_broker_connect`` en ``meta.json`` al conectar.
``POST /api/broker/reconnect`` reutiliza esos params. Sin flip LIVE.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.session import WorkbenchSession

LAST_CONNECT_META_KEY = "last_broker_connect"
LAST_CONNECT_UPDATED_AT_KEY = "last_broker_connect_updated_at"
RECONNECT_VERSION = 1

NO_LAST_CONNECT_MSG = (
    "no hay config de connect previa; POST /api/broker/connect primero"
)


def _as_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text if text else None


def normalize_connect_config(body: dict[str, Any]) -> dict[str, Any]:
    """Extrae params reutilizables de un body de connect (fail-closed)."""
    venue_raw = body.get("venue")
    if not isinstance(venue_raw, str) or not venue_raw.strip():
        raise ValidationError("campo 'venue' requerido para last_broker_connect")
    venue = venue_raw.strip().lower()

    cfg: dict[str, Any] = {"venue": venue}

    mode_raw = body.get("mode")
    if mode_raw is not None:
        if not isinstance(mode_raw, str) or not mode_raw.strip():
            raise ValidationError("campo 'mode' inválido en last_broker_connect")
        cfg["mode"] = mode_raw.strip().lower()

    md_source = _as_optional_str(body.get("md_source"))
    if md_source is not None:
        cfg["md_source"] = md_source.lower()

    csv_path = body.get("csv_path")
    if csv_path is not None:
        if not isinstance(csv_path, str) or not csv_path.strip():
            raise ValidationError("campo 'csv_path' inválido en last_broker_connect")
        cfg["csv_path"] = csv_path.strip()

    slippage = body.get("slippage_bps")
    if slippage is not None:
        cfg["slippage_bps"] = str(slippage)

    return cfg


def load_last_connect(session: WorkbenchSession) -> dict[str, Any] | None:
    """Lee ``last_broker_connect`` desde meta; None si ausente/inválido."""
    meta = session.load_meta()
    raw = meta.get(LAST_CONNECT_META_KEY)
    if not isinstance(raw, dict):
        return None
    try:
        return normalize_connect_config(raw)
    except ValidationError:
        return None


def save_last_connect(session: WorkbenchSession, body: dict[str, Any]) -> dict[str, Any]:
    """Persiste last connect config en meta.json."""
    cfg = normalize_connect_config(body)
    meta = dict(session.load_meta())
    now = datetime.now(tz=UTC).isoformat()
    meta[LAST_CONNECT_META_KEY] = cfg
    meta[LAST_CONNECT_UPDATED_AT_KEY] = now
    try:
        session.save_meta(meta)
    except ValidationError:
        raise
    except OSError as exc:
        raise ValidationError(
            f"no se pudo persistir last_broker_connect en meta: {exc}"
        ) from exc
    return cfg


def last_connect_status(
    session: WorkbenchSession, *, config: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Estado de last connect para respuestas de reconnect / inspección."""
    meta = session.load_meta()
    cfg = config if config is not None else load_last_connect(session)
    updated_at = meta.get(LAST_CONNECT_UPDATED_AT_KEY)
    return {
        "kind": "broker_reconnect",
        "version": RECONNECT_VERSION,
        "session_id": session.session_id,
        "has_last_connect": cfg is not None,
        "last_connect": cfg,
        "updated_at": updated_at if isinstance(updated_at, str) else None,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }


def require_last_connect(session: WorkbenchSession) -> dict[str, Any]:
    """Fail-closed: ValidationError si no hay last connect."""
    cfg = load_last_connect(session)
    if cfg is None:
        raise ValidationError(NO_LAST_CONNECT_MSG)
    return cfg
