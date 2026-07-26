"""First-run onboarding wizard — flag ``onboarding_done`` en session ``meta.json`` (F37).

Sin LIVE / auth WAN. Persistencia vía meta de sesión (no archivo aparte).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.session import WorkbenchSession

ONBOARDING_META_KEY = "onboarding_done"
ONBOARDING_COMPLETED_AT_KEY = "onboarding_completed_at"
ONBOARDING_VERSION = 1

# Pasos canónicos del wizard (UI + API status).
ONBOARDING_STEPS: tuple[dict[str, str], ...] = (
    {
        "id": "modes",
        "title": "Modos TESTER / REAL / LIVE",
        "summary": (
            "TESTER = fake/offline; REAL (=PAPER) = MD real + fills simulados; "
            "LIVE = órdenes venue (bloqueado)."
        ),
    },
    {
        "id": "venue_tester",
        "title": "Conectar venue tester",
        "summary": "Conectá un venue en modo TESTER (paper/a3 fake) desde Market Data.",
    },
    {
        "id": "paper_or_backtest",
        "title": "Sesión Paper / Backtest",
        "summary": "Abrí Sesión Paper o Backtest para research-safe sin envío venue.",
    },
    {
        "id": "chat_safe",
        "title": "Chat IA safe",
        "summary": "El asistente es allowlist de lectura; no envía órdenes ni flip LIVE.",
    },
)


def is_onboarding_done(meta: dict[str, Any] | None) -> bool:
    """True si meta marca onboarding completado (truthy bool/str)."""
    if not isinstance(meta, dict):
        return False
    raw = meta.get(ONBOARDING_META_KEY)
    if raw is True:
        return True
    if not isinstance(raw, str):
        return False
    return raw.strip().lower() in {"1", "true", "yes"}


def onboarding_status(session: WorkbenchSession) -> dict[str, Any]:
    """Estado de onboarding para GET /api/onboarding."""
    meta = session.load_meta()
    done = is_onboarding_done(meta)
    completed_at = meta.get(ONBOARDING_COMPLETED_AT_KEY) if done else None
    return {
        "version": ONBOARDING_VERSION,
        "onboarding_done": done,
        "show_wizard": not done,
        "completed_at": completed_at if isinstance(completed_at, str) else None,
        "steps": [dict(step) for step in ONBOARDING_STEPS],
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
        "modes": {
            "tester": "Fake backends / datasets locales — sin órdenes venue",
            "real": "Alias de PAPER: MD/cuenta reales + fills simulados (≠ LIVE)",
            "paper": "Fills simulados vía PaperBroker — sin submit venue",
            "live": "Órdenes venue reales — BLOQUEADO (LIVE_BLOCKED=True)",
        },
    }


def mark_onboarding_complete(session: WorkbenchSession) -> dict[str, Any]:
    """Persiste ``onboarding_done=true`` en meta.json; idempotente."""
    meta = dict(session.load_meta())
    now = datetime.now(tz=UTC).isoformat()
    if is_onboarding_done(meta):
        # Idempotente: no reescribe completed_at si ya estaba.
        meta[ONBOARDING_META_KEY] = True
        if ONBOARDING_COMPLETED_AT_KEY not in meta:
            meta[ONBOARDING_COMPLETED_AT_KEY] = now
    else:
        meta[ONBOARDING_META_KEY] = True
        meta[ONBOARDING_COMPLETED_AT_KEY] = now
    try:
        session.save_meta(meta)
    except ValidationError:
        raise
    except OSError as exc:
        raise ValidationError(f"no se pudo persistir onboarding en meta: {exc}") from exc
    return onboarding_status(session)
