"""Resolución de backend MD A3: fake (CI) vs env opt-in read-only (Fase 24).

``submit``/``cancel`` del port siguen gated vía ``assert_live_routing_blocked``.
El backend env solo se usa para MD / account / positions read.
"""

from __future__ import annotations

import os
from typing import Any

from quantlab.data.exchanges.a3.constants import A3EnvironmentName
from quantlab.data.exchanges.a3.exceptions import A3ConfigurationError
from quantlab.data.exchanges.a3.fake_backend import FakeA3Backend
from quantlab.data.exchanges.a3.protocols import A3Backend
from quantlab.infra.logging import get_logger

logger = get_logger(__name__)

MD_SOURCE_FAKE = "fake"
MD_SOURCE_ENV = "env"
MD_READONLY_ENV = "QUANTLAB_A3_MD_READONLY"
VALID_MD_SOURCES = frozenset({MD_SOURCE_FAKE, MD_SOURCE_ENV})


def md_readonly_flag_enabled() -> bool:
    return os.environ.get(MD_READONLY_ENV, "").strip() == "1"


def has_a3_credentials() -> bool:
    user = os.environ.get("QUANTLAB_A3_USER", "").strip()
    password = os.environ.get("QUANTLAB_A3_PASSWORD", "").strip()
    account = os.environ.get("QUANTLAB_A3_ACCOUNT", "").strip()
    return bool(user and password and account)


def _resolve_a3_environment(*, strict: bool = False) -> A3EnvironmentName:
    raw = os.environ.get("QUANTLAB_A3_ENVIRONMENT", "simulation").strip().lower()
    try:
        return A3EnvironmentName(raw)
    except ValueError as exc:
        if strict:
            raise A3ConfigurationError("QUANTLAB_A3_ENVIRONMENT inválido") from exc
        return A3EnvironmentName.SIMULATION


def try_build_env_md_backend(*, strict: bool = False) -> tuple[A3Backend | None, str]:
    """Intenta PyRofexBackend para MD read-only. No conecta aún.

    Retorna ``(backend, reason)``; backend None si no aplica.
    """
    if not md_readonly_flag_enabled():
        return None, f"{MD_READONLY_ENV}!=1"
    if not has_a3_credentials():
        return None, "faltan QUANTLAB_A3_USER|PASSWORD|ACCOUNT"
    try:
        from quantlab.data.exchanges.a3.client import PyRofexBackend
        from quantlab.data.exchanges.a3.config import load_credentials_from_env

        creds = load_credentials_from_env()
        env = _resolve_a3_environment(strict=strict)
        backend: A3Backend = PyRofexBackend(creds, env)
        return backend, "ok"
    except A3ConfigurationError:
        return None, "a3_configuration_error"
    except Exception:  # noqa: BLE001 — frontera pyRofex/creds
        # No incluir el texto externo: puede contener datos sensibles.
        logger.warning("a3_env_md_backend_build_failed")
        return None, "backend_build_failed"


def resolve_a3_md_backend(
    md_source: str = MD_SOURCE_FAKE,
    *,
    allow_fallback: bool = True,
) -> tuple[A3Backend, dict[str, Any]]:
    """Resuelve backend MD + metadata de health (provider, fallback).

    - ``fake`` → FakeA3Backend (default CI)
    - ``env`` → intenta backend real SOLO si flag + creds; si no, fallback fake
    """
    source = (md_source or MD_SOURCE_FAKE).strip().lower()
    if source not in VALID_MD_SOURCES:
        if not allow_fallback:
            raise A3ConfigurationError("md_source inválido para resolución strict")
        source = MD_SOURCE_FAKE

    detail: dict[str, Any] = {
        "md_source_requested": source,
        "md_source": source,
        "md_readonly_flag": md_readonly_flag_enabled(),
        "fallback": False,
        "fallback_reason": "",
    }

    if source == MD_SOURCE_ENV:
        backend, reason = try_build_env_md_backend(strict=not allow_fallback)
        if backend is not None:
            detail["md_provider"] = "a3-env-readonly"
            detail["md_source"] = MD_SOURCE_ENV
            detail["build"] = reason
            return backend, detail
        if not allow_fallback:
            raise A3ConfigurationError(f"A3 env MD backend no disponible: {reason}")
        detail["fallback"] = True
        detail["fallback_reason"] = reason
        detail["md_provider"] = "a3-fake"
        detail["md_source"] = MD_SOURCE_FAKE
        logger.info(
            "a3_md_fallback_fake",
            requested=MD_SOURCE_ENV,
            reason=reason,
        )
        return FakeA3Backend(), detail

    detail["md_provider"] = "a3-fake"
    detail["md_source"] = MD_SOURCE_FAKE
    return FakeA3Backend(), detail
