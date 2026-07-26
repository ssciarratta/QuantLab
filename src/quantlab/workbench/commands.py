"""Command palette registry — paneles + acciones seguras (F35).

Solo comandos research-safe: abrir paneles y refresh health.
Prohibido: flip LIVE, place_order venue, set_live, mutaciones LIVE.
"""

from __future__ import annotations

from typing import Any

from quantlab.execution.live_gate import LIVE_BLOCKED

# Orden estable para Ctrl+1..9 (Sesión / paneles principales).
PANE_SHORTCUT_ORDER: tuple[str, ...] = (
    "health",
    "market",
    "universe",
    "catalog",
    "blotter",
    "journal",
    "paper_session",
    "positions",
    "risk",
)

_PANE_COMMANDS: tuple[dict[str, Any], ...] = (
    {
        "id": "open.health",
        "kind": "pane",
        "label": "Abrir Salud / Modo",
        "pane_id": "health",
        "keywords": ("health", "salud", "modo", "live_blocked"),
    },
    {
        "id": "open.market",
        "kind": "pane",
        "label": "Abrir Market Data",
        "pane_id": "market",
        "keywords": ("market", "md", "snapshot", "precio"),
    },
    {
        "id": "open.universe",
        "kind": "pane",
        "label": "Abrir Universe",
        "pane_id": "universe",
        "keywords": ("universe", "watchlist", "símbolos", "symbols"),
    },
    {
        "id": "open.catalog",
        "kind": "pane",
        "label": "Abrir Data Catalog",
        "pane_id": "catalog",
        "keywords": ("catalog", "datasets", "data"),
    },
    {
        "id": "open.blotter",
        "kind": "pane",
        "label": "Abrir Paper Blotter",
        "pane_id": "blotter",
        "keywords": ("blotter", "paper", "órdenes", "orders"),
    },
    {
        "id": "open.journal",
        "kind": "pane",
        "label": "Abrir Journal",
        "pane_id": "journal",
        "keywords": ("journal", "fills", "csv"),
    },
    {
        "id": "open.paper_session",
        "kind": "pane",
        "label": "Abrir Sesión Paper",
        "pane_id": "paper_session",
        "keywords": ("paper", "session", "sesión", "runner"),
    },
    {
        "id": "open.positions",
        "kind": "pane",
        "label": "Abrir Posiciones",
        "pane_id": "positions",
        "keywords": ("positions", "posiciones", "inventory"),
    },
    {
        "id": "open.risk",
        "kind": "pane",
        "label": "Abrir Riesgo",
        "pane_id": "risk",
        "keywords": ("risk", "riesgo", "límites", "limits"),
    },
    {
        "id": "open.chat",
        "kind": "pane",
        "label": "Abrir Chat IA",
        "pane_id": "chat",
        "keywords": ("chat", "ia", "asistente"),
    },
    {
        "id": "open.backtest",
        "kind": "pane",
        "label": "Abrir Backtest",
        "pane_id": "backtest",
        "keywords": ("backtest", "lab", "barras"),
    },
    {
        "id": "open.scanner",
        "kind": "pane",
        "label": "Abrir Alpha Scanner",
        "pane_id": "scanner",
        "keywords": ("scanner", "alpha"),
    },
    {
        "id": "open.metrics",
        "kind": "pane",
        "label": "Abrir Metrics / Último",
        "pane_id": "metrics",
        "keywords": ("metrics", "métricas", "resultado"),
    },
    {
        "id": "open.reports",
        "kind": "pane",
        "label": "Abrir Reports",
        "pane_id": "reports",
        "keywords": ("reports", "reportes", "html"),
    },
    {
        "id": "open.experiments",
        "kind": "pane",
        "label": "Abrir Experiments",
        "pane_id": "experiments",
        "keywords": ("experiments", "registry"),
    },
    {
        "id": "open.optimize",
        "kind": "pane",
        "label": "Abrir Optimizer",
        "pane_id": "optimize",
        "keywords": ("optimize", "optimizer", "pareto", "grid"),
    },
    {
        "id": "open.montecarlo",
        "kind": "pane",
        "label": "Abrir Monte Carlo",
        "pane_id": "montecarlo",
        "keywords": ("montecarlo", "mc", "ci"),
    },
    {
        "id": "open.features",
        "kind": "pane",
        "label": "Abrir Features",
        "pane_id": "features",
        "keywords": ("features", "pipeline", "store"),
    },
    {
        "id": "open.export_hb",
        "kind": "pane",
        "label": "Abrir Hummingbot Export",
        "pane_id": "export_hb",
        "keywords": ("hummingbot", "export", "hb"),
    },
    {
        "id": "open.validation",
        "kind": "pane",
        "label": "Abrir Validation Splits",
        "pane_id": "validation",
        "keywords": ("validation", "walk-forward", "splits", "leakage"),
    },
    {
        "id": "open.settings",
        "kind": "pane",
        "label": "Abrir Settings",
        "pane_id": "settings",
        "keywords": ("settings", "ajustes", "preferencias", "theme", "locale"),
    },
    {
        "id": "open.docs",
        "kind": "pane",
        "label": "Abrir Help / Docs",
        "pane_id": "docs",
        "keywords": ("docs", "help", "ayuda", "markdown", "manual", "ops"),
    },
    {
        "id": "open.about",
        "kind": "pane",
        "label": "Acerca de QuantLab",
        "pane_id": "about",
        "keywords": ("about", "acerca", "version", "versión", "info", "python"),
    },
    {
        "id": "open.sessions",
        "kind": "pane",
        "label": "Abrir Sessions",
        "pane_id": "sessions",
        "keywords": ("sessions", "sesión", "switch", "cambiar", "multi"),
    },
    {
        "id": "open.activity",
        "kind": "pane",
        "label": "Abrir Activity",
        "pane_id": "activity",
        "keywords": ("activity", "log", "toast", "eventos", "historial"),
    },
    {
        "id": "open.access_log",
        "kind": "pane",
        "label": "Abrir Access Log",
        "pane_id": "access_log",
        "keywords": ("access", "access-log", "http", "requests", "jsonl", "auditoría"),
    },
    {
        "id": "open.backups",
        "kind": "pane",
        "label": "Abrir Backups",
        "pane_id": "backups",
        "keywords": ("backups", "backup", "zip", "auto-backup", "respaldo", "sesión"),
    },
    {
        "id": "open.ops_metrics",
        "kind": "pane",
        "label": "Abrir Ops Metrics",
        "pane_id": "ops_metrics",
        "keywords": ("ops", "metrics", "prometheus", "counters", "live_gate"),
    },
)

_ACTION_COMMANDS: tuple[dict[str, Any], ...] = (
    {
        "id": "action.health_refresh",
        "kind": "action",
        "label": "Refresh Health / Mode",
        "action": "health_refresh",
        "keywords": ("refresh", "health", "reload", "actualizar"),
    },
    {
        "id": "action.close_focused",
        "kind": "action",
        "label": "Cerrar ventana enfocada",
        "action": "close_focused",
        "keywords": ("close", "cerrar", "ventana", "window"),
        "shortcut": "Ctrl+W",
    },
    {
        "id": "action.minimize_all",
        "kind": "action",
        "label": "Minimize all",
        "action": "minimize_all",
        "keywords": (
            "minimize",
            "minimizar",
            "all",
            "todas",
            "windows",
            "ventanas",
            "hide",
        ),
    },
    {
        "id": "action.restore_all",
        "kind": "action",
        "label": "Restore all windows",
        "action": "restore_all",
        "keywords": (
            "restore",
            "restaurar",
            "all",
            "todas",
            "windows",
            "ventanas",
            "show",
        ),
    },
    {
        "id": "action.cascade_windows",
        "kind": "action",
        "label": "Cascade windows",
        "action": "cascade_windows",
        "keywords": (
            "cascade",
            "cascada",
            "windows",
            "ventanas",
            "stack",
            "apilar",
            "layout",
        ),
    },
    {
        "id": "action.tile_windows",
        "kind": "action",
        "label": "Tile windows",
        "action": "tile_windows",
        "keywords": (
            "tile",
            "mosaico",
            "grid",
            "windows",
            "ventanas",
            "arrange",
            "organizar",
            "layout",
        ),
    },
    {
        "id": "action.bring_to_front",
        "kind": "action",
        "label": "Bring to Front",
        "action": "bring_to_front",
        "keywords": (
            "bring",
            "front",
            "adelante",
            "frente",
            "z-order",
            "zorder",
            "windows",
            "ventanas",
            "raise",
        ),
    },
    {
        "id": "action.send_to_back",
        "kind": "action",
        "label": "Send to Back",
        "action": "send_to_back",
        "keywords": (
            "send",
            "back",
            "atrás",
            "detras",
            "detrás",
            "z-order",
            "zorder",
            "windows",
            "ventanas",
            "lower",
        ),
    },
)


def _shortcut_for_pane(pane_id: str) -> str | None:
    try:
        idx = PANE_SHORTCUT_ORDER.index(pane_id)
    except ValueError:
        return None
    return f"Ctrl+{idx + 1}"


def list_commands() -> dict[str, Any]:
    """GET /api/commands — paneles + acciones seguras (sin LIVE)."""
    commands: list[dict[str, Any]] = []
    for raw in _PANE_COMMANDS:
        cmd = dict(raw)
        cmd["keywords"] = list(raw["keywords"])
        shortcut = _shortcut_for_pane(str(raw["pane_id"]))
        if shortcut:
            cmd["shortcut"] = shortcut
        cmd["safe"] = True
        cmd["live"] = False
        commands.append(cmd)
    for raw in _ACTION_COMMANDS:
        cmd = dict(raw)
        cmd["keywords"] = list(raw["keywords"])
        cmd["safe"] = True
        cmd["live"] = False
        commands.append(cmd)
    return {
        "ok": True,
        "kind": "commands",
        "count": len(commands),
        "commands": commands,
        "pane_shortcut_order": list(PANE_SHORTCUT_ORDER),
        "palette_shortcuts": ["Ctrl+K", "Ctrl+Shift+P"],
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }
