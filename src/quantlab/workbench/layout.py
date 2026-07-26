"""Persistencia de layout MDI del workbench (``layout.json`` por sesión)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError

LAYOUT_VERSION = 1
MAX_WINDOWS = 64
_WINDOW_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")

# Bounds fail-closed (px) — evita valores absurdos / DoS de JSON.
_MIN_X, _MAX_X = -500, 10_000
_MIN_Y, _MAX_Y = -100, 10_000
_MIN_W, _MAX_W = 200, 5_000
_MIN_H, _MAX_H = 120, 5_000


def empty_layout() -> dict[str, Any]:
    """Layout canónico vacío."""
    return {"version": LAYOUT_VERSION, "windows": {}}


def layout_path_for(session_root: Path) -> Path:
    return Path(session_root) / "layout.json"


def _validate_window_id(window_id: str) -> str:
    wid = window_id.strip()
    if not wid or not _WINDOW_ID_RE.fullmatch(wid):
        raise ValidationError(
            f"window id inválido (solo [A-Za-z][A-Za-z0-9_-]{{0,63}}): {window_id!r}"
        )
    return wid


def _as_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"layout.{field} debe ser int")
    return value


def _clamp_int(value: int, lo: int, hi: int, field: str) -> int:
    if value < lo or value > hi:
        raise ValidationError(f"layout.{field} fuera de rango [{lo}, {hi}]: {value}")
    return value


def normalize_window_geom(raw: dict[str, Any], *, window_id: str) -> dict[str, Any]:
    """Normaliza geometría de una ventana; fail-closed ante tipos/rangos inválidos."""
    if not isinstance(raw, dict):
        raise ValidationError(f"layout.windows[{window_id!r}] debe ser objeto")
    x = _clamp_int(
        _as_int(raw.get("x"), f"windows.{window_id}.x"), _MIN_X, _MAX_X, f"{window_id}.x"
    )
    y = _clamp_int(
        _as_int(raw.get("y"), f"windows.{window_id}.y"), _MIN_Y, _MAX_Y, f"{window_id}.y"
    )
    w = _clamp_int(
        _as_int(raw.get("w"), f"windows.{window_id}.w"), _MIN_W, _MAX_W, f"{window_id}.w"
    )
    h = _clamp_int(
        _as_int(raw.get("h"), f"windows.{window_id}.h"), _MIN_H, _MAX_H, f"{window_id}.h"
    )
    out: dict[str, Any] = {"x": x, "y": y, "w": w, "h": h}
    if "minimized" in raw:
        if not isinstance(raw["minimized"], bool):
            raise ValidationError(f"layout.windows.{window_id}.minimized debe ser bool")
        out["minimized"] = raw["minimized"]
    if "z" in raw:
        z = _as_int(raw["z"], f"windows.{window_id}.z")
        if z < 0 or z > 100_000:
            raise ValidationError(f"layout.windows.{window_id}.z fuera de rango")
        out["z"] = z
    return out


def normalize_layout(payload: dict[str, Any] | None) -> dict[str, Any]:
    """Valida y normaliza un payload de layout completo."""
    if payload is None:
        return empty_layout()
    if not isinstance(payload, dict):
        raise ValidationError("layout debe ser un objeto JSON")
    version = payload.get("version", LAYOUT_VERSION)
    if not isinstance(version, int) or isinstance(version, bool):
        raise ValidationError("layout.version debe ser int")
    if version != LAYOUT_VERSION:
        raise ValidationError(f"layout.version no soportada: {version} (esperado {LAYOUT_VERSION})")
    windows_raw = payload.get("windows", {})
    if not isinstance(windows_raw, dict):
        raise ValidationError("layout.windows debe ser un objeto")
    if len(windows_raw) > MAX_WINDOWS:
        raise ValidationError(f"layout.windows excede máximo ({MAX_WINDOWS})")
    windows: dict[str, Any] = {}
    for key, value in windows_raw.items():
        if not isinstance(key, str):
            raise ValidationError("layout.windows keys deben ser string")
        wid = _validate_window_id(key)
        windows[wid] = normalize_window_geom(value, window_id=wid)
    return {"version": LAYOUT_VERSION, "windows": windows}


def load_layout(path: Path) -> dict[str, Any]:
    """Carga ``layout.json``; vacío canónico si no existe."""
    if not path.exists():
        return empty_layout()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"layout.json ilegible: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValidationError("layout.json debe ser un objeto")
    return normalize_layout(raw)


def save_layout(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    """Persiste layout normalizado (escritura atómica)."""
    normalized = normalize_layout(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(normalized, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
    return normalized
