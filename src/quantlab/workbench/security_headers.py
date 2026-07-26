"""Security headers + CORS + CSP hardening for workbench HTTP (F56/F57).

Fail-closed:
- Never emit ``Access-Control-Allow-Origin: *``.
- Reflect ``Origin`` only when its host is loopback; non-loopback Origins
  are not echoed.
- CSP restrictiva SPA local: sin ``unsafe-eval``; scripts solo ``'self'``.
"""

from __future__ import annotations

from collections.abc import Mapping
from urllib.parse import urlparse

# F57 — Content-Security-Policy (SPA local loopback).
# style-src incluye 'unsafe-inline' por atributos style= generados en panes JS.
# Sin unsafe-eval. Scripts solo archivos bajo /static/js (sin inline en HTML).
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "connect-src 'self'; "
    "frame-ancestors 'none'"
)

# Canonical response headers applied to every workbench response.
SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
}

CACHE_CONTROL_NO_STORE = "no-store"
ACCESS_CONTROL_ALLOW_ORIGIN = "Access-Control-Allow-Origin"

_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})


def is_loopback_host(host: str) -> bool:
    """True si host es loopback (127.0.0.1 / ::1 / localhost)."""
    h = host.strip().lower()
    if h.startswith("[") and h.endswith("]"):
        h = h[1:-1]
    # Strip zone id for IPv6 (e.g. fe80::1%lo0) — still not loopback unless ::1.
    if "%" in h:
        h = h.split("%", 1)[0]
    return h in _LOOPBACK_HOSTS


def origin_host(origin: str) -> str | None:
    """Extrae hostname de un Origin HTTP; None si inválido / vacío / '*'."""
    raw = (origin or "").strip()
    if not raw or raw == "*":
        return None
    # Origin may be "null" (opaque) — never reflect.
    if raw.lower() == "null":
        return None
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"}:
        return None
    host = parsed.hostname
    if not host:
        return None
    return host


def is_loopback_origin(origin: str) -> bool:
    """True si Origin apunta a un host loopback."""
    host = origin_host(origin)
    if host is None:
        return False
    return is_loopback_host(host)


def cors_allow_origin(origin: str | None) -> str | None:
    """Valor de ACAO a emitir, o None (no header).

    - Nunca ``*``.
    - Si Origin ausente / inválido → None.
    - Si Origin no-loopback → None (no reflejar).
    - Si Origin loopback → reflejar el Origin exacto.
    """
    if origin is None:
        return None
    raw = origin.strip()
    if not raw or raw == "*":
        return None
    if not is_loopback_origin(raw):
        return None
    return raw


def wants_api_no_store(path: str) -> bool:
    """True si la ruta es ``/api`` o bajo ``/api/`` (Cache-Control no-store)."""
    p = path.split("?", 1)[0]
    return p == "/api" or p.startswith("/api/")


def security_header_items(
    *,
    path: str = "/api/health",
    origin: str | None = None,
) -> list[tuple[str, str]]:
    """Lista ordenada de headers de seguridad (+ CORS/Cache-Control) a enviar."""
    items: list[tuple[str, str]] = list(SECURITY_HEADERS.items())
    if wants_api_no_store(path):
        items.append(("Cache-Control", CACHE_CONTROL_NO_STORE))
    allow = cors_allow_origin(origin)
    if allow is not None:
        items.append((ACCESS_CONTROL_ALLOW_ORIGIN, allow))
    return items


def assert_no_wildcard_acao(headers: Mapping[str, str]) -> None:
    """Fail-closed helper para tests: ACAO nunca es ``*``."""
    for key, value in headers.items():
        if key.lower() == ACCESS_CONTROL_ALLOW_ORIGIN.lower():
            assert value.strip() != "*", "Access-Control-Allow-Origin must not be *"
