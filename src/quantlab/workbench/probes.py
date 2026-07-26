"""Liveness / readiness probes (F54).

``/api/livez`` — proceso up (siempre 200 si el handler responde).
``/api/readyz`` — LIVE_BLOCKED True + session root writable → 200; else 503.

Sin flip LIVE / place_order. Pensado para Docker HEALTHCHECK / orchestrators.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED

PROBE_WRITE_NAME = ".readyz_write_probe"


def is_session_root_writable(root: Path) -> bool:
    """True si ``root`` existe, es dir y admite create+unlink de un probe file."""
    try:
        path = Path(root)
        if not path.is_dir():
            return False
        if not os.access(path, os.W_OK | os.X_OK):
            return False
        probe = path / PROBE_WRITE_NAME
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def livez_payload() -> dict[str, Any]:
    """Payload JSON de GET /api/livez (siempre alive si se alcanzó)."""
    return {
        "ok": True,
        "alive": True,
        "status": "alive",
        "kind": "livez",
        "version": __version__,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }


def readyz_payload(
    *,
    session_root: Path | None,
    live_blocked: bool | None = None,
) -> dict[str, Any]:
    """Evalúa readiness; caller mapea ``ready`` → HTTP 200/503."""
    gate_ok = LIVE_BLOCKED is True if live_blocked is None else bool(live_blocked)
    writable = False
    if session_root is not None:
        writable = is_session_root_writable(session_root)

    ready = gate_ok and writable
    reasons: list[str] = []
    if not gate_ok:
        reasons.append("LIVE_BLOCKED is not True")
    if not writable:
        reasons.append("session root not writable")

    out: dict[str, Any] = {
        "ok": ready,
        "ready": ready,
        "status": "ready" if ready else "not_ready",
        "kind": "readyz",
        "checks": {
            "live_blocked": gate_ok,
            "session_root_writable": writable,
        },
        "session_root": str(session_root) if session_root is not None else None,
        "version": __version__,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }
    if not ready:
        out["error"] = "; ".join(reasons) if reasons else "not ready"
    return out
