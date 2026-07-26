"""Gate de credenciales para LIVE — unlock efímero en memoria (F100).

Reglas:
- Nunca persistir password en disco ni logs.
- Credenciales esperadas vía env local del operador:
  ``QUANTLAB_LIVE_USER`` + ``QUANTLAB_LIVE_PASSWORD``.
- Sin esas env, el unlock falla (fail-closed): el agente no tiene tus secrets.
- ``LIVE_BLOCKED`` sigue True por defecto; el unlock es el único corte humano.
"""

from __future__ import annotations

import hmac
import os
import secrets
import threading
import time
from dataclasses import dataclass
from typing import Any

from quantlab.core.exceptions import ValidationError

_ENV_USER = "QUANTLAB_LIVE_USER"
_ENV_PASSWORD = "QUANTLAB_LIVE_PASSWORD"
_DEFAULT_TTL_SECONDS = 30 * 60

_lock = threading.RLock()
_active: LiveUnlockSession | None = None


@dataclass(frozen=True, slots=True)
class LiveUnlockSession:
    """Sesión LIVE desbloqueada en memoria (sin password)."""

    username: str
    token: str
    unlocked_at: float
    expires_at: float
    venue_scope: str  # p.ej. "binance_demo"

    def is_expired(self, *, now: float | None = None) -> bool:
        ts = time.time() if now is None else now
        return ts >= self.expires_at


def configured_live_user() -> str | None:
    raw = os.environ.get(_ENV_USER, "").strip()
    return raw or None


def live_credentials_configured() -> bool:
    user = configured_live_user()
    password = os.environ.get(_ENV_PASSWORD, "")
    return bool(user) and bool(password)


def unlock_live_session(
    *,
    username: str,
    password: str,
    venue_scope: str = "binance_demo",
    ttl_seconds: int = _DEFAULT_TTL_SECONDS,
) -> LiveUnlockSession:
    """Valida user/pass contra env y abre sesión LIVE efímera en memoria."""
    if not isinstance(username, str) or not username.strip():
        raise ValidationError("username requerido para unlock LIVE")
    if not isinstance(password, str) or not password:
        raise ValidationError("password requerido para unlock LIVE")
    if ttl_seconds < 60 or ttl_seconds > 8 * 3600:
        raise ValidationError("ttl_seconds fuera de rango (60..28800)")

    expected_user = os.environ.get(_ENV_USER, "")
    expected_pass = os.environ.get(_ENV_PASSWORD, "")
    if not expected_user or not expected_pass:
        raise ValidationError(
            "LIVE unlock no configurado: definí QUANTLAB_LIVE_USER y "
            "QUANTLAB_LIVE_PASSWORD en el entorno local (nunca en git)."
        )

    user_ok = hmac.compare_digest(username.strip(), expected_user.strip())
    pass_ok = hmac.compare_digest(password, expected_pass)
    if not (user_ok and pass_ok):
        raise ValidationError("credenciales LIVE inválidas")

    scope = venue_scope.strip().lower() or "binance_demo"
    if scope not in {"binance_demo", "binance", "a3"}:
        raise ValidationError(f"venue_scope no permitido: {venue_scope!r}")

    now = time.time()
    session = LiveUnlockSession(
        username=username.strip(),
        token=secrets.token_urlsafe(24),
        unlocked_at=now,
        expires_at=now + float(ttl_seconds),
        venue_scope=scope,
    )
    with _lock:
        global _active
        _active = session
    return session


def lock_live_session() -> None:
    """Cierra la sesión LIVE desbloqueada."""
    with _lock:
        global _active
        _active = None


def get_live_unlock_session() -> LiveUnlockSession | None:
    global _active
    with _lock:
        session = _active
        if session is None:
            return None
        if session.is_expired():
            _active = None
            return None
        return session


def is_live_session_unlocked() -> bool:
    return get_live_unlock_session() is not None


def live_unlock_status() -> dict[str, Any]:
    session = get_live_unlock_session()
    return {
        "unlocked": session is not None,
        "credentials_configured": live_credentials_configured(),
        "username": None if session is None else session.username,
        "venue_scope": None if session is None else session.venue_scope,
        "expires_at": None if session is None else session.expires_at,
        "env_user_key": _ENV_USER,
        "env_password_key": _ENV_PASSWORD,
        "note": (
            "Sin unlock, LIVE permanece bloqueado. "
            "Password nunca se persiste ni se loguea."
        ),
    }


def reset_live_unlock_for_tests() -> None:
    """Solo tests — limpia unlock en memoria."""
    lock_live_session()
