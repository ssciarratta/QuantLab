"""Persistencia de settings del workbench (``settings.json`` por sesión) — F36.

Campos: theme, default_venue, default_strategy, slippage_bps, locale.
Sin LIVE / auth WAN.
"""

from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.workbench.strategy_catalog import CANONICAL_STRATEGY_IDS, normalize_strategy_id

SETTINGS_VERSION = 1
ALLOWED_THEMES: frozenset[str] = frozenset({"slate", "high-contrast"})
ALLOWED_LOCALES: frozenset[str] = frozenset({"es", "en"})
DEFAULT_THEME = "slate"
DEFAULT_VENUE = "paper"
DEFAULT_STRATEGY = "momentum"
DEFAULT_SLIPPAGE_BPS = Decimal("0")
DEFAULT_LOCALE = "es"

_VENUE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,31}$")
_MAX_SLIPPAGE_BPS = Decimal("9999.9999")


def default_settings() -> dict[str, Any]:
    """Settings canónicos por defecto (locale es)."""
    return {
        "version": SETTINGS_VERSION,
        "theme": DEFAULT_THEME,
        "default_venue": DEFAULT_VENUE,
        "default_strategy": DEFAULT_STRATEGY,
        "slippage_bps": str(DEFAULT_SLIPPAGE_BPS),
        "locale": DEFAULT_LOCALE,
    }


def settings_path_for(session_root: Path) -> Path:
    return Path(session_root) / "settings.json"


def _parse_slippage(raw: Any) -> Decimal:
    if raw is None:
        return DEFAULT_SLIPPAGE_BPS
    if isinstance(raw, bool):
        raise ValidationError("settings.slippage_bps inválido (bool)")
    try:
        value = Decimal(str(raw).strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValidationError(f"settings.slippage_bps inválido: {raw!r}") from exc
    if value < 0:
        raise ValidationError("settings.slippage_bps no puede ser negativo")
    if value >= _MAX_SLIPPAGE_BPS:
        raise ValidationError("settings.slippage_bps debe ser < 10000")
    return value


def _validate_venue(raw: Any) -> str:
    if not isinstance(raw, str):
        raise ValidationError("settings.default_venue debe ser string")
    venue = raw.strip()
    if not venue or not _VENUE_RE.fullmatch(venue):
        raise ValidationError(
            f"settings.default_venue inválido (solo [A-Za-z][A-Za-z0-9_-]{{0,31}}): {raw!r}"
        )
    return venue


def _validate_strategy(raw: Any) -> str:
    if not isinstance(raw, str):
        raise ValidationError("settings.default_strategy debe ser string")
    try:
        sid = normalize_strategy_id(raw.strip())
    except ValidationError as exc:
        raise ValidationError(f"settings.default_strategy inválido: {exc}") from exc
    if sid not in CANONICAL_STRATEGY_IDS:
        raise ValidationError(
            f"settings.default_strategy desconocido: {raw!r} "
            f"(válidos: {', '.join(CANONICAL_STRATEGY_IDS)})"
        )
    return sid


def normalize_settings(payload: dict[str, Any] | None) -> dict[str, Any]:
    """Valida y normaliza un payload de settings; fail-closed."""
    base = default_settings()
    if payload is None:
        return base
    if not isinstance(payload, dict):
        raise ValidationError("settings debe ser un objeto JSON")

    version = payload.get("version", SETTINGS_VERSION)
    if not isinstance(version, int) or isinstance(version, bool):
        raise ValidationError("settings.version debe ser int")
    if version != SETTINGS_VERSION:
        raise ValidationError(
            f"settings.version no soportada: {version} (esperado {SETTINGS_VERSION})"
        )

    theme = payload.get("theme", DEFAULT_THEME)
    if not isinstance(theme, str) or theme not in ALLOWED_THEMES:
        raise ValidationError(f"settings.theme inválido: {theme!r} (válidos: slate|high-contrast)")

    locale = payload.get("locale", DEFAULT_LOCALE)
    if not isinstance(locale, str) or locale not in ALLOWED_LOCALES:
        raise ValidationError(
            f"settings.locale inválido: {locale!r} (válidos: es|en; default es)"
        )

    venue = _validate_venue(payload.get("default_venue", DEFAULT_VENUE))
    strategy = _validate_strategy(payload.get("default_strategy", DEFAULT_STRATEGY))
    slip = _parse_slippage(payload.get("slippage_bps", DEFAULT_SLIPPAGE_BPS))

    return {
        "version": SETTINGS_VERSION,
        "theme": theme,
        "default_venue": venue,
        "default_strategy": strategy,
        "slippage_bps": format(slip, "f"),
        "locale": locale,
    }


def load_settings(path: Path) -> dict[str, Any]:
    """Carga ``settings.json``; defaults canónicos si no existe."""
    if not path.exists():
        return default_settings()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"settings.json ilegible: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValidationError("settings.json debe ser un objeto")
    return normalize_settings(raw)


def save_settings(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    """Persiste settings normalizados (escritura atómica)."""
    normalized = normalize_settings(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(normalized, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
    return normalized
