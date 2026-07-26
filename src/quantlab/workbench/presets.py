"""Workspace presets — layouts MDI nombrados (F40) + custom de sesión (F80).

Presets built-in research-safe. Aplicar escribe ``layout.json`` de sesión.
Custom: ``session/presets/{name}.json`` (copia del layout actual).
Sin flip LIVE · sin place_order venue.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.layout import LAYOUT_VERSION, load_layout, normalize_layout, save_layout

# Geometrías tipadas: cascada legible en desktop ~1280px.
_PRESETS: dict[str, dict[str, Any]] = {
    "research": {
        "name": "research",
        "label": "Research",
        "description": "Health + Backtest + Reports + Chat",
        "windows": {
            "health": {"x": 24, "y": 20, "w": 420, "h": 340, "z": 10},
            "backtest": {"x": 460, "y": 20, "w": 480, "h": 400, "z": 11},
            "reports": {"x": 24, "y": 380, "w": 560, "h": 420, "z": 12},
            "chat": {"x": 600, "y": 380, "w": 440, "h": 420, "z": 13},
        },
    },
    "trading_paper": {
        "name": "trading_paper",
        "label": "Trading Paper",
        "description": "Market + Blotter + Positions + Session + Risk",
        "windows": {
            "market": {"x": 24, "y": 20, "w": 440, "h": 360, "z": 10},
            "blotter": {"x": 480, "y": 20, "w": 500, "h": 380, "z": 11},
            "positions": {"x": 24, "y": 400, "w": 440, "h": 340, "z": 12},
            "paper_session": {"x": 480, "y": 420, "w": 480, "h": 400, "z": 13},
            "risk": {"x": 980, "y": 20, "w": 420, "h": 360, "z": 14},
        },
    },
    "ops": {
        "name": "ops",
        "label": "Ops",
        "description": "Health + Settings + Docs + Catalog",
        "windows": {
            "health": {"x": 24, "y": 20, "w": 420, "h": 340, "z": 10},
            "settings": {"x": 460, "y": 20, "w": 440, "h": 400, "z": 11},
            "docs": {"x": 24, "y": 380, "w": 540, "h": 440, "z": 12},
            "catalog": {"x": 580, "y": 380, "w": 540, "h": 400, "z": 13},
        },
    },
}

PRESET_NAMES: tuple[str, ...] = tuple(_PRESETS.keys())
BUILTIN_PRESET_NAMES: frozenset[str] = frozenset(PRESET_NAMES)

# Fail-closed: nombre = segmento de path (sin traversal / builtin shadow).
_PRESET_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
MAX_CUSTOM_PRESETS = 64
PRESETS_DIRNAME = "presets"


def validate_preset_name(name: str) -> str:
    """Valida nombre de preset custom (path-safe, no builtin)."""
    key = str(name or "").strip()
    if not key or key in {".", ".."} or not _PRESET_NAME_RE.fullmatch(key):
        raise ValidationError(
            f"preset name inválido (solo [A-Za-z][A-Za-z0-9_-]{{0,63}}): {name!r}"
        )
    if "/" in key or "\\" in key or ".." in key:
        raise ValidationError(f"preset name con path traversal rechazado: {name!r}")
    if key in BUILTIN_PRESET_NAMES:
        raise ValidationError(
            f"preset name reserva built-in: {key!r} (elegí otro nombre)"
        )
    return key


def presets_dir_for(session_root: Path) -> Path:
    """``<session>/presets/``."""
    return Path(session_root) / PRESETS_DIRNAME


def ensure_presets_dir(presets_dir: Path) -> Path:
    """Crea el directorio de presets custom si no existe."""
    path = Path(presets_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def custom_preset_path(presets_dir: Path, name: str) -> Path:
    """Path canónico ``presets/{name}.json`` (validado + anti-escape)."""
    key = validate_preset_name(name)
    root = ensure_presets_dir(presets_dir).resolve()
    path = (root / f"{key}.json").resolve()
    if not path.is_relative_to(root):
        raise ValidationError(f"preset path fuera de presets/: {path}")
    return path


def _catalog_item(
    *,
    name: str,
    label: str,
    description: str,
    windows: dict[str, Any],
    custom: bool,
) -> dict[str, Any]:
    return {
        "name": name,
        "label": label,
        "description": description,
        "window_ids": sorted(windows.keys()),
        "window_count": len(windows),
        "custom": custom is True,
    }


def _load_custom_file(path: Path) -> dict[str, Any]:
    """Lee y normaliza un preset custom desde disco."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"preset custom ilegible: {path.name}") from exc
    if not isinstance(raw, dict):
        raise ValidationError(f"preset custom inválido: {path.name}")
    stem = path.stem
    name = str(raw.get("name") or stem).strip() or stem
    # Re-validate against filename to avoid rename tricks.
    if name != stem:
        raise ValidationError(
            f"preset custom name≠filename: {name!r} vs {stem!r}"
        )
    layout = normalize_layout(
        {"version": raw.get("version", LAYOUT_VERSION), "windows": raw.get("windows", {})}
    )
    label = raw.get("label")
    if not isinstance(label, str) or not label.strip():
        label = name
    description = raw.get("description")
    if not isinstance(description, str) or not description.strip():
        description = "Custom preset"
    return {
        "name": name,
        "label": label.strip(),
        "description": description.strip(),
        "windows": dict(layout["windows"]),
        "window_ids": sorted(layout["windows"].keys()),
        "custom": True,
        "version": layout["version"],
    }


def list_custom_presets(presets_dir: Path | None) -> list[dict[str, Any]]:
    """Lista presets custom bajo ``presets/`` (ignora ilegibles)."""
    if presets_dir is None:
        return []
    root = Path(presets_dir)
    if not root.is_dir():
        return []
    items: list[dict[str, Any]] = []
    for child in sorted(root.glob("*.json"), key=lambda p: p.stem.lower()):
        if not child.is_file():
            continue
        try:
            validate_preset_name(child.stem)
        except ValidationError:
            continue
        try:
            preset = _load_custom_file(child)
        except ValidationError:
            continue
        items.append(
            _catalog_item(
                name=preset["name"],
                label=preset["label"],
                description=preset["description"],
                windows=preset["windows"],
                custom=True,
            )
        )
        if len(items) >= MAX_CUSTOM_PRESETS:
            break
    return items


def list_presets(presets_dir: Path | None = None) -> dict[str, Any]:
    """Catálogo de presets built-in + custom de sesión (sin mutar layout)."""
    items: list[dict[str, Any]] = []
    for name in PRESET_NAMES:
        preset = _PRESETS[name]
        windows = preset["windows"]
        assert isinstance(windows, dict)
        items.append(
            _catalog_item(
                name=preset["name"],
                label=preset["label"],
                description=preset["description"],
                windows=windows,
                custom=False,
            )
        )
    custom = list_custom_presets(presets_dir)
    items.extend(custom)
    names = [p["name"] for p in items]
    return {
        "ok": True,
        "kind": "presets",
        "count": len(items),
        "builtin_count": len(PRESET_NAMES),
        "custom_count": len(custom),
        "presets": items,
        "names": names,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }


def get_preset(name: str, presets_dir: Path | None = None) -> dict[str, Any]:
    """Devuelve definición de preset; fail-closed si nombre desconocido."""
    key = str(name or "").strip()
    if key in _PRESETS:
        preset = _PRESETS[key]
        windows = dict(preset["windows"])
        return {
            "name": preset["name"],
            "label": preset["label"],
            "description": preset["description"],
            "windows": windows,
            "window_ids": sorted(windows.keys()),
            "custom": False,
        }
    if presets_dir is not None:
        try:
            path = custom_preset_path(presets_dir, key)
        except ValidationError:
            path = None
        if path is not None and path.is_file():
            return _load_custom_file(path)
    known = ", ".join(PRESET_NAMES)
    raise ValidationError(f"preset desconocido: {name!r} (válidos: {known} + custom)")


def layout_for_preset(name: str, presets_dir: Path | None = None) -> dict[str, Any]:
    """Construye payload ``layout.json`` (version + windows) para un preset."""
    preset = get_preset(name, presets_dir)
    return {"version": LAYOUT_VERSION, "windows": dict(preset["windows"])}


def apply_preset(
    layout_path: Path, name: str, presets_dir: Path | None = None
) -> dict[str, Any]:
    """Escribe ``layout.json`` con las ventanas del preset (reemplazo total)."""
    layout = layout_for_preset(name, presets_dir)
    saved = save_layout(Path(layout_path), layout)
    preset = get_preset(name, presets_dir)
    return {
        "ok": True,
        "kind": "preset_applied",
        "preset": {
            "name": preset["name"],
            "label": preset["label"],
            "description": preset["description"],
            "window_ids": list(preset["window_ids"]),
            "custom": preset.get("custom") is True,
        },
        "layout": saved,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }


def save_custom_preset(
    layout_path: Path,
    presets_dir: Path,
    name: str,
    *,
    label: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Guarda el ``layout.json`` actual como preset custom ``presets/{name}.json``."""
    key = validate_preset_name(name)
    ensure_presets_dir(presets_dir)
    existing = list_custom_presets(presets_dir)
    path = custom_preset_path(presets_dir, key)
    if not path.is_file() and len(existing) >= MAX_CUSTOM_PRESETS:
        raise ValidationError(
            f"máximo de presets custom alcanzado ({MAX_CUSTOM_PRESETS})"
        )
    layout = load_layout(Path(layout_path))
    windows = dict(layout.get("windows") or {})
    disp_label = (label or key).strip() if isinstance(label, str) else key
    if not disp_label:
        disp_label = key
    desc = (
        description.strip()
        if isinstance(description, str) and description.strip()
        else "Custom preset"
    )
    payload: dict[str, Any] = {
        "version": int(layout.get("version", LAYOUT_VERSION)),
        "name": key,
        "label": disp_label,
        "description": desc,
        "custom": True,
        "windows": windows,
    }
    # Round-trip normalize before write.
    normalized = normalize_layout(
        {"version": payload["version"], "windows": payload["windows"]}
    )
    payload["version"] = normalized["version"]
    payload["windows"] = normalized["windows"]
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")
    return {
        "ok": True,
        "kind": "preset_saved",
        "preset": {
            "name": key,
            "label": disp_label,
            "description": desc,
            "window_ids": sorted(windows.keys()),
            "window_count": len(windows),
            "custom": True,
            "path": str(path),
        },
        "layout": normalized,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }
