"""Workspace presets — layouts MDI nombrados (F40).

Presets built-in research-safe. Aplicar escribe ``layout.json`` de sesión.
Sin flip LIVE · sin place_order venue.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.layout import LAYOUT_VERSION, save_layout

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


def list_presets() -> dict[str, Any]:
    """Catálogo de presets (sin mutar layout)."""
    items: list[dict[str, Any]] = []
    for name in PRESET_NAMES:
        preset = _PRESETS[name]
        windows = preset["windows"]
        assert isinstance(windows, dict)
        items.append(
            {
                "name": preset["name"],
                "label": preset["label"],
                "description": preset["description"],
                "window_ids": sorted(windows.keys()),
                "window_count": len(windows),
            }
        )
    return {
        "ok": True,
        "kind": "presets",
        "count": len(items),
        "presets": items,
        "names": list(PRESET_NAMES),
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }


def get_preset(name: str) -> dict[str, Any]:
    """Devuelve definición de preset; fail-closed si nombre desconocido."""
    key = str(name or "").strip()
    if not key or key not in _PRESETS:
        known = ", ".join(PRESET_NAMES)
        raise ValidationError(f"preset desconocido: {name!r} (válidos: {known})")
    preset = _PRESETS[key]
    windows = dict(preset["windows"])
    return {
        "name": preset["name"],
        "label": preset["label"],
        "description": preset["description"],
        "windows": windows,
        "window_ids": sorted(windows.keys()),
    }


def layout_for_preset(name: str) -> dict[str, Any]:
    """Construye payload ``layout.json`` (version + windows) para un preset."""
    preset = get_preset(name)
    return {"version": LAYOUT_VERSION, "windows": dict(preset["windows"])}


def apply_preset(layout_path: Path, name: str) -> dict[str, Any]:
    """Escribe ``layout.json`` con las ventanas del preset (reemplazo total)."""
    layout = layout_for_preset(name)
    saved = save_layout(Path(layout_path), layout)
    preset = get_preset(name)
    return {
        "ok": True,
        "kind": "preset_applied",
        "preset": {
            "name": preset["name"],
            "label": preset["label"],
            "description": preset["description"],
            "window_ids": list(preset["window_ids"]),
        },
        "layout": saved,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }
