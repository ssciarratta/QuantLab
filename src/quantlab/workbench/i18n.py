"""i18n scaffold del workbench (F60) — locale default ``es``, stub ``en``.

Sirve diccionarios UI desde ``static/i18n/{locale}.json``. Sin flip LIVE.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED

DEFAULT_LOCALE = "es"
SUPPORTED_LOCALES: frozenset[str] = frozenset({"es", "en"})
_LOCALE_RE = re.compile(r"^[a-z]{2}(?:-[A-Za-z]{2})?$")

_I18N_DIR = Path(__file__).resolve().parent / "static" / "i18n"


def normalize_locale(raw: str | None) -> str:
    """Valida locale; fail-closed (solo es|en)."""
    if raw is None or not str(raw).strip():
        return DEFAULT_LOCALE
    locale = str(raw).strip().lower().replace("_", "-")
    # Acepta es / en; ignora región (es-ar → es).
    base = locale.split("-", 1)[0]
    if base not in SUPPORTED_LOCALES:
        raise ValidationError(
            f"locale no soportado: {raw!r} (válidos: {', '.join(sorted(SUPPORTED_LOCALES))})"
        )
    if not _LOCALE_RE.fullmatch(locale) and locale != base:
        raise ValidationError(f"locale inválido: {raw!r}")
    return base


def i18n_json_path(locale: str) -> Path:
    """Path canónico del JSON de mensajes (bajo static/i18n)."""
    loc = normalize_locale(locale)
    path = (_I18N_DIR / f"{loc}.json").resolve()
    root = _I18N_DIR.resolve()
    # Comparación por Path (portable Windows/POSIX), no por prefijo string.
    if path.parent != root:
        raise ValidationError("i18n path traversal bloqueado")
    return path


def load_messages(locale: str = DEFAULT_LOCALE) -> dict[str, str]:
    """Carga el diccionario de mensajes para ``locale``."""
    loc = normalize_locale(locale)
    path = i18n_json_path(loc)
    if not path.is_file():
        raise ValidationError(f"diccionario i18n no encontrado: {loc}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"diccionario i18n ilegible ({loc}): {exc}") from exc
    if not isinstance(raw, dict):
        raise ValidationError(f"diccionario i18n debe ser objeto JSON ({loc})")
    out: dict[str, str] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValidationError(f"i18n entries deben ser string→string ({loc})")
        out[key] = value
    return out


def build_i18n_payload(locale: str = DEFAULT_LOCALE) -> dict[str, Any]:
    """Payload JSON de GET /api/i18n/{locale}."""
    loc = normalize_locale(locale)
    messages = load_messages(loc)
    return {
        "ok": True,
        "kind": "i18n",
        "locale": loc,
        "default_locale": DEFAULT_LOCALE,
        "supported_locales": sorted(SUPPORTED_LOCALES),
        "messages": messages,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }


def list_supported_locales() -> list[str]:
    return sorted(SUPPORTED_LOCALES)
