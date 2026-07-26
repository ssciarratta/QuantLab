"""Paper kill switch — bloquea submit + session step cuando engaged (F70).

Flag ``paper_kill_engaged`` en session ``meta.json``. Solo paper/research;
no flip LIVE / place_order venue.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.session import WorkbenchSession

PAPER_KILL_META_KEY = "paper_kill_engaged"
PAPER_KILL_UPDATED_AT_KEY = "paper_kill_updated_at"
PAPER_KILL_VERSION = 1

KILL_ENGAGED_MSG = "paper kill switch engaged — paper submit/step rechazado"


def is_paper_kill_engaged(meta: dict[str, Any] | None) -> bool:
    """True si meta marca kill switch engaged (truthy bool/str)."""
    if not isinstance(meta, dict):
        return False
    raw = meta.get(PAPER_KILL_META_KEY)
    if raw is True:
        return True
    if raw is False or raw is None:
        return False
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return raw != 0
    if not isinstance(raw, str):
        return False
    return raw.strip().lower() in {"1", "true", "yes", "on", "engaged"}


def paper_kill_status(session: WorkbenchSession, *, engaged: bool | None = None) -> dict[str, Any]:
    """Estado kill switch para GET /api/paper/kill."""
    meta = session.load_meta()
    flag = is_paper_kill_engaged(meta) if engaged is None else bool(engaged)
    updated_at = meta.get(PAPER_KILL_UPDATED_AT_KEY)
    return {
        "ok": True,
        "kind": "paper_kill",
        "version": PAPER_KILL_VERSION,
        "engaged": flag,
        "session_id": session.session_id,
        "updated_at": updated_at if isinstance(updated_at, str) else None,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "blocks": ["paper_submit", "paper_session_step"],
    }


def set_paper_kill_engaged(session: WorkbenchSession, engaged: bool) -> dict[str, Any]:
    """Persiste ``paper_kill_engaged`` en meta.json."""
    meta = dict(session.load_meta())
    now = datetime.now(tz=UTC).isoformat()
    meta[PAPER_KILL_META_KEY] = bool(engaged)
    meta[PAPER_KILL_UPDATED_AT_KEY] = now
    try:
        session.save_meta(meta)
    except ValidationError:
        raise
    except OSError as exc:
        raise ValidationError(f"no se pudo persistir paper kill en meta: {exc}") from exc
    return paper_kill_status(session, engaged=bool(engaged))


def raise_if_paper_kill_engaged(*, engaged: bool) -> None:
    """Fail-closed: ValidationError si kill switch engaged."""
    if engaged:
        raise ValidationError(KILL_ENGAGED_MSG)
