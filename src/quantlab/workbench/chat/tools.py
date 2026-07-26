"""ToolRegistry allowlist — solo lectura / explicación (Fase 22 / DEC-063)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from quantlab.brokers.mode import REAL_ALIAS
from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.infra.health import run_health_checks
from quantlab.workbench import lab_services
from quantlab.workbench.api import WorkbenchState

ALLOWED_TOOLS: frozenset[str] = frozenset(
    {
        "get_health",
        "get_mode",
        "list_capabilities",
        "list_venues",
        "explain_backtest",
        "search_docs",
        "list_experiments",
        "explain_live_policy",
    }
)

FORBIDDEN_TOOLS: frozenset[str] = frozenset(
    {
        "submit_order",
        "cancel_order",
        "set_live",
        "flip_live_blocked",
        "place_order",
        "set_mode_live",
        "enable_live",
        "send_order",
        "paper_submit",
    }
)

_TOOL_META: dict[str, dict[str, str]] = {
    "get_health": {
        "description": "Health checks del proceso (LIVE_BLOCKED, ledger, etc.)",
    },
    "get_mode": {
        "description": "Modo de sesión actual (tester|paper; REAL=PAPER)",
    },
    "list_capabilities": {
        "description": "Features del laboratorio workbench",
    },
    "list_venues": {
        "description": "Venues registrados en el broker registry",
    },
    "explain_backtest": {
        "description": "Guía de backtest + último summary de sesión si existe",
    },
    "search_docs": {
        "description": "Busca keywords en docs/*.md locales",
    },
    "list_experiments": {
        "description": "Lista experimentos del registry de sesión",
    },
    "explain_live_policy": {
        "description": "Política LIVE: siempre bloqueado; REAL=PAPER",
    },
}

_BACKTEST_GUIDE = (
    "Backtest en QuantLab Workbench: panel Backtest o POST /api/lab/backtest. "
    "Estrategias: GET /api/lab/strategies (dummy, buy_once, momentum, inventory_mm, "
    "avellaneda_stoikov). Parámetros típicos: strategy_id, n_bars, params "
    "(lookback/quantity/half_spread/gamma). "
    "Resultado queda en sesión (GET /api/lab/metrics). Nunca envía órdenes live."
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_DOCS = _REPO_ROOT / "docs"


class ToolRegistry:
    """Ejecuta solo tools allowlist; rechaza mutaciones / LIVE."""

    def __init__(
        self,
        state: WorkbenchState,
        *,
        docs_root: Path | None = None,
    ) -> None:
        self._state = state
        self._docs_root = docs_root if docs_root is not None else _DEFAULT_DOCS

    def list_allowlist(self) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        for name in sorted(ALLOWED_TOOLS):
            meta = _TOOL_META.get(name, {})
            items.append(
                {
                    "name": name,
                    "description": meta.get("description", ""),
                    "access": "read_only",
                }
            )
        return items

    def is_allowed(self, name: str) -> bool:
        return name in ALLOWED_TOOLS

    def is_forbidden(self, name: str) -> bool:
        return name in FORBIDDEN_TOOLS

    def call(self, name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        tool = name.strip().lower()
        params = args or {}
        if tool in FORBIDDEN_TOOLS or tool not in ALLOWED_TOOLS:
            raise ValidationError(
                f"tool rechazada (safe-by-default): {name!r}. "
                f"Allowlist: {', '.join(sorted(ALLOWED_TOOLS))}"
            )
        handler = {
            "get_health": self._get_health,
            "get_mode": self._get_mode,
            "list_capabilities": self._list_capabilities,
            "list_venues": self._list_venues,
            "explain_backtest": self._explain_backtest,
            "search_docs": self._search_docs,
            "list_experiments": self._list_experiments,
            "explain_live_policy": self._explain_live_policy,
        }[tool]
        return handler(params)

    def _get_health(self, _args: dict[str, Any]) -> dict[str, Any]:
        return run_health_checks().to_dict()

    def _get_mode(self, _args: dict[str, Any]) -> dict[str, Any]:
        return {
            "mode": self._state.mode.value,
            "live_blocked": LIVE_BLOCKED is True,
            "real_alias": REAL_ALIAS.value,
            "note": "REAL (producto) = PAPER; LIVE no permitido en workbench",
        }

    def _list_capabilities(self, _args: dict[str, Any]) -> dict[str, Any]:
        return lab_services.lab_capabilities()

    def _list_venues(self, _args: dict[str, Any]) -> dict[str, Any]:
        return {"venues": self._state.registry.list_venues()}

    def _explain_backtest(self, _args: dict[str, Any]) -> dict[str, Any]:
        last = self._state.last_lab_result
        summary: dict[str, Any] | None = None
        if isinstance(last, dict):
            summary = {
                "kind": last.get("kind"),
                "ok": last.get("ok"),
                "strategy_id": last.get("strategy_id"),
                "metrics": last.get("metrics"),
                "live_routing": last.get("live_routing", False),
            }
        return {
            "guide": _BACKTEST_GUIDE,
            "last_summary": summary,
            "has_last": summary is not None,
            "live_routing": False,
        }

    def _search_docs(self, args: dict[str, Any]) -> dict[str, Any]:
        raw_q = args.get("query") or args.get("q") or args.get("keywords") or ""
        if not isinstance(raw_q, str):
            raise ValidationError("search_docs: query debe ser string")
        keywords = [k for k in re.split(r"\s+", raw_q.strip().lower()) if k]
        if not keywords:
            return {"query": "", "matches": [], "docs_root": str(self._docs_root)}
        root = self._docs_root
        matches: list[dict[str, Any]] = []
        if root.is_dir():
            for path in sorted(root.glob("*.md")):
                try:
                    text = path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                lower = text.lower()
                hits = [kw for kw in keywords if kw in lower]
                if not hits:
                    continue
                snippet = _snippet_for(text, hits[0])
                matches.append(
                    {
                        "file": path.name,
                        "hits": hits,
                        "snippet": snippet,
                    }
                )
                if len(matches) >= 8:
                    break
        return {
            "query": " ".join(keywords),
            "matches": matches,
            "docs_root": str(root),
        }

    def _list_experiments(self, _args: dict[str, Any]) -> dict[str, Any]:
        path = self._state.ensure_lab_registry_path()
        return lab_services.list_lab_experiments(path)

    def _explain_live_policy(self, _args: dict[str, Any]) -> dict[str, Any]:
        return {
            "live_blocked": LIVE_BLOCKED is True,
            "live_allowed": False,
            "real_alias": REAL_ALIAS.value,
            "policy": (
                "LIVE siempre bloqueado en QuantLab workbench (LIVE_BLOCKED=True). "
                "REAL (producto) = PAPER: market data/cuenta pueden ser reales, "
                "fills simulados — nunca place_order al venue. "
                "El chat NO puede set_live / flip_live_blocked / submit_order."
            ),
            "chat_mutations": False,
        }


def _snippet_for(text: str, keyword: str, radius: int = 80) -> str:
    lower = text.lower()
    idx = lower.find(keyword.lower())
    if idx < 0:
        return text[:160].replace("\n", " ").strip()
    start = max(0, idx - radius)
    end = min(len(text), idx + len(keyword) + radius)
    chunk = text[start:end].replace("\n", " ").strip()
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{chunk}{suffix}"
