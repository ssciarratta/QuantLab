"""About / version metadata for workbench (F45).

Read-only surface: version, LIVE gate, phases INTERNAL summary, Python,
and bind policy. No LIVE flip / place_order.
"""

from __future__ import annotations

import platform
import sys
from typing import Any

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED

# Arco workbench APROBADO_INTERNO tip (sin certificados externos F19+).
PHASES_SUMMARY = "F19–F50 INTERNAL"

DEFAULT_BIND_HOST = "127.0.0.1"
BIND_POLICY_LOOPBACK = "loopback-default"
BIND_POLICY_ALLOW_NON_LOOPBACK = "allow-non-loopback"

_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})


def _is_loopback_host(host: str) -> bool:
    """True si host es loopback (evita import circular con server)."""
    h = host.strip().lower()
    if h.startswith("[") and h.endswith("]"):
        h = h[1:-1]
    return h in _LOOPBACK_HOSTS


def bind_policy_dict(
    *,
    bind_host: str = DEFAULT_BIND_HOST,
    allow_non_loopback: bool = False,
) -> dict[str, Any]:
    """Describe política de bind HTTP del workbench."""
    host = (bind_host or DEFAULT_BIND_HOST).strip() or DEFAULT_BIND_HOST
    loopback = _is_loopback_host(host)
    if allow_non_loopback and not loopback:
        policy = BIND_POLICY_ALLOW_NON_LOOPBACK
        summary = (
            f"non-loopback host={host!r} permitido vía --allow-non-loopback "
            "(sin auth HTTP; no exponer a WAN)"
        )
    else:
        policy = BIND_POLICY_LOOPBACK
        summary = f"loopback-default (host={host!r}; non-loopback requiere --allow-non-loopback)"
    return {
        "policy": policy,
        "summary": summary,
        "default_host": DEFAULT_BIND_HOST,
        "bind_host": host,
        "loopback": loopback,
        "allow_non_loopback": bool(allow_non_loopback),
        "loopback_enforced": not bool(allow_non_loopback),
    }


def build_about_payload(
    *,
    bind_host: str = DEFAULT_BIND_HOST,
    allow_non_loopback: bool = False,
) -> dict[str, Any]:
    """Payload JSON de GET /api/about."""
    py_version = platform.python_version()
    return {
        "ok": True,
        "kind": "about",
        "name": "QuantLab Workbench",
        "version": __version__,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
        "phases_summary": PHASES_SUMMARY,
        "python_version": py_version,
        "python": {
            "version": py_version,
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
        },
        "bind_policy": bind_policy_dict(
            bind_host=bind_host,
            allow_non_loopback=allow_non_loopback,
        ),
    }
