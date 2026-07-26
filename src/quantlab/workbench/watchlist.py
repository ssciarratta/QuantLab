"""Watchlist de símbolos por sesión (``watchlist.json``) — F30."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError

WATCHLIST_VERSION = 1
MAX_SYMBOLS = 256
_SYMBOL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$")


def empty_watchlist() -> dict[str, Any]:
    """Watchlist canónica vacía."""
    return {"version": WATCHLIST_VERSION, "symbols": []}


def watchlist_path_for(session_root: Path) -> Path:
    return Path(session_root) / "watchlist.json"


def validate_symbol(symbol: str) -> str:
    """Valida símbolo fail-closed (charset sin path separators)."""
    if not isinstance(symbol, str):
        raise ValidationError(f"symbol inválido (tipo): {type(symbol).__name__}")
    sym = symbol.strip().upper()
    if not sym or sym in {".", ".."} or not _SYMBOL_RE.fullmatch(sym):
        raise ValidationError(
            f"symbol inválido (charset ^[A-Za-z0-9][A-Za-z0-9._-]{{0,31}}$): {symbol!r}"
        )
    if "/" in sym or "\\" in sym or ".." in sym:
        raise ValidationError(f"symbol con path traversal rechazado: {symbol!r}")
    return sym


def normalize_watchlist(payload: dict[str, Any] | None) -> dict[str, Any]:
    """Valida y normaliza un payload de watchlist (dedupe, orden estable)."""
    if payload is None:
        return empty_watchlist()
    if not isinstance(payload, dict):
        raise ValidationError("watchlist debe ser un objeto JSON")
    version = payload.get("version", WATCHLIST_VERSION)
    if not isinstance(version, int) or isinstance(version, bool):
        raise ValidationError("watchlist.version debe ser int")
    if version != WATCHLIST_VERSION:
        raise ValidationError(
            f"watchlist.version no soportada: {version} (esperado {WATCHLIST_VERSION})"
        )
    raw_symbols = payload.get("symbols", [])
    if not isinstance(raw_symbols, list):
        raise ValidationError("watchlist.symbols debe ser una lista")
    if len(raw_symbols) > MAX_SYMBOLS:
        raise ValidationError(f"watchlist.symbols excede máximo ({MAX_SYMBOLS})")
    seen: set[str] = set()
    symbols: list[str] = []
    for item in raw_symbols:
        if not isinstance(item, str):
            raise ValidationError("watchlist.symbols items deben ser string")
        sym = validate_symbol(item)
        if sym in seen:
            continue
        seen.add(sym)
        symbols.append(sym)
    return {"version": WATCHLIST_VERSION, "symbols": symbols}


def load_watchlist(path: Path) -> dict[str, Any]:
    """Carga ``watchlist.json``; vacío canónico si no existe."""
    if not path.exists():
        return empty_watchlist()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"watchlist.json ilegible: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValidationError("watchlist.json debe ser un objeto")
    return normalize_watchlist(raw)


def save_watchlist(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    """Persiste watchlist normalizada (escritura atómica)."""
    normalized = normalize_watchlist(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(normalized, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
    return normalized


def add_symbols(current: dict[str, Any], to_add: list[str]) -> dict[str, Any]:
    """Devuelve watchlist con símbolos añadidos (dedupe)."""
    base = list(normalize_watchlist(current)["symbols"])
    seen = set(base)
    for raw in to_add:
        sym = validate_symbol(raw)
        if sym not in seen:
            seen.add(sym)
            base.append(sym)
    if len(base) > MAX_SYMBOLS:
        raise ValidationError(f"watchlist.symbols excede máximo ({MAX_SYMBOLS})")
    return {"version": WATCHLIST_VERSION, "symbols": base}


def remove_symbols(current: dict[str, Any], to_remove: list[str]) -> dict[str, Any]:
    """Devuelve watchlist sin los símbolos indicados."""
    drop = {validate_symbol(s) for s in to_remove}
    kept = [s for s in normalize_watchlist(current)["symbols"] if s not in drop]
    return {"version": WATCHLIST_VERSION, "symbols": kept}
