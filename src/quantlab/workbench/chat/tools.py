"""ToolRegistry allowlist — solo lectura / explicación (Fase 22 / F47 / DEC-063)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quantlab.brokers.mode import REAL_ALIAS
from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.infra.health import run_health_checks
from quantlab.workbench import lab_services
from quantlab.workbench.activity import clamp_limit, list_activity
from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.chat.context import build_assistant_context
from quantlab.workbench.docs_browser import default_docs_root, search_docs_files
from quantlab.workbench.reports import list_lab_reports
from quantlab.workbench.strategy_catalog import list_strategy_catalog

ALLOWED_TOOLS: frozenset[str] = frozenset(
    {
        "get_health",
        "get_mode",
        "list_capabilities",
        "list_venues",
        "explain_backtest",
        "explain_guided_lab",
        "explain_binance_lab",
        "suggest_workflow",
        "instructor_guide",
        "get_assistant_context",
        "search_docs",
        "list_experiments",
        "explain_live_policy",
        "get_session_summary",
        "list_reports",
        "list_strategies",
        "open_pane",
        "run_binance_alpha",
        "run_binance_pipeline",
    }
)

DEFAULT_SESSION_ACTIVITY_LIMIT = 10

ALLOWED_PANES: frozenset[str] = frozenset(
    {
        "guided_lab",
        "chat",
        "health",
        "backtest",
        "scanner",
        "reports",
        "settings",
        "docs",
        "market",
        "blotter",
        "journal",
        "paper_session",
        "positions",
        "risk",
        "metrics",
        "venues",
        "diagnostics",
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
    "explain_guided_lab": {
        "description": "Guía paso a paso del panel Guided Lab (venue, scan, simular)",
    },
    "explain_binance_lab": {
        "description": "Binance MD público, alpha scanner y pipeline scan→backtest",
    },
    "suggest_workflow": {
        "description": "Sugiere flujo según objetivo del operador (aprender, binance, a3)",
    },
    "instructor_guide": {
        "description": "Lección paso a paso: alpha Binance, market making, flujo completo",
    },
    "get_assistant_context": {
        "description": "Memoria de sesión, último lab, instructor y resumen conversación",
    },
    "search_docs": {
        "description": "Busca keywords en docs/*.md y docs/ops/*.md locales",
    },
    "list_experiments": {
        "description": "Lista experimentos del registry de sesión",
    },
    "explain_live_policy": {
        "description": "Política LIVE: siempre bloqueado; REAL=PAPER",
    },
    "get_session_summary": {
        "description": (
            "Resumen de sesión: mode, venue, book equity, posiciones, activity last N (read-only)"
        ),
    },
    "list_reports": {
        "description": "Lista reports lab persistidos de la sesión",
    },
    "list_strategies": {
        "description": "Catálogo de estrategias workbench (ids/tags/defaults)",
    },
    "open_pane": {
        "description": "Abrir panel UI (guided_lab, chat, backtest, scanner, etc.)",
    },
    "run_binance_alpha": {
        "description": "Ejecutar ranking alpha Binance (MD público) y abrir Guided Lab",
    },
    "run_binance_pipeline": {
        "description": "Ejecutar pipeline scan+backtest top-N Binance (read-only MD)",
    },
}

_BACKTEST_GUIDE = (
    "Backtest en QuantLab Workbench: panel Backtest o POST /api/lab/backtest. "
    "Estrategias: GET /api/lab/strategies (espectro por familia; "
    "runnable=binance-ready para backtest/paper/demo post-unlock; stubs no ejecutan). "
    "Parámetros típicos: strategy_id, n_bars, params "
    "(lookback/quantity/half_spread/gamma). "
    "Resultado queda en sesión (GET /api/lab/metrics). Nunca envía órdenes live."
)

_GUIDED_LAB_GUIDE = (
    "Guided Lab (QL → Guided Lab): wizard paso a paso. "
    "0) Unlock LIVE opcional (QUANTLAB_LIVE_USER/PASSWORD en .env). "
    "1) Venue: binance | paper | a3. "
    "2) Escanear: lab sintético, Scan Binance USDT, Ranking alpha Binance. "
    "3) Estrategia momentum/buy_once. "
    "4) Simular backtest sintético O botón 'Backtest top 5 Binance' (pipeline F111). "
    "5) Demo order solo binance+unlock. A3: connect paper, snapshot, paper submit."
)

_BINANCE_LAB_GUIDE = (
    "Para correr Alpha Scanner en Binance desde la UI:\n"
    "1) QL (abajo izquierda) → Guided Lab\n"
    "2) Venue = binance\n"
    "3) Clic «Ranking alpha Binance» (klines USDT reales, read-only)\n"
    "4) Revisá el top de monedas\n"
    "5) Para probar estrategia: elegí inventory_mm o momentum → "
    "«Backtest top 5 Binance»\n"
    "APIs (solo si las necesitás): "
    "POST /api/lab/binance/scan · /scanner · /pipeline. "
    "Demo órdenes solo post-unlock. Producción bloqueada."
)

_WORKFLOW_HINTS: dict[str, str] = {
    "aprender": (
        "Empezá: 1) uv run quantlab-workbench 2) QL→Guided Lab venue paper "
        "3) Scan lab sintético 4) Simular backtest 5) Chat IA para dudas."
    ),
    "binance": (
        "Binance sin operar: Guided Lab venue binance → Scan Binance USDT → "
        "Ranking alpha Binance → Backtest top 5 Binance. Demo solo con unlock."
    ),
    "estrategia": (
        "Probar estrategia: Guided Lab → elegir momentum/buy_once → Simular backtest. "
        "Con datos reales Binance: Backtest top 5 Binance (pipeline)."
    ),
    "a3": (
        "A3: .env QUANTLAB_A3_MD_READONLY=1 + creds → Guided Lab venue a3 → "
        "connect paper → instrumentos → snapshot → paper submit."
    ),
    "alpha_mm": (
        "Flujo alpha→MM: Guided Lab venue binance → Ranking alpha Binance → "
        "elegir inventory_mm o avellaneda_stoikov → Backtest top 5 Binance."
    ),
}

_MM_STRATEGIES: tuple[dict[str, str], ...] = (
    {
        "id": "inventory_mm",
        "name": "Inventory MM",
        "when": "Primera prueba MM: simple, bid/ask alrededor del mid con skew por inventario.",
        "params": "quantity, half_spread (ej. 0.5), max_pos (ej. 10)",
        "best_for": "Pares líquidos del ranking (BTCUSDT, ETHUSDT) — spreads estables.",
    },
    {
        "id": "avellaneda_stoikov",
        "name": "Avellaneda–Stoikov",
        "when": "Después de inventory_mm: cotizador con reserva óptima e inventario.",
        "params": "gamma, sigma, kappa, horizon_events, max_pos",
        "best_for": "Monedas con volatilidad moderada del top alpha; requiere tunear sigma.",
    },
)

_INSTRUCTOR_LESSONS: dict[str, dict[str, Any]] = {
    "alpha_binance": {
        "title": "Lección 1 — Detectar monedas con Alpha en Binance",
        "steps": (
            "Abrí el Workbench en http://127.0.0.1:8765 (si no corre: uv run quantlab-workbench).",
            "QL (abajo izq) → Guided Lab.",
            "Sección 1 Venue: elegí binance.",
            "Sección 2 Escanear: clic en Ranking alpha Binance (lee klines USDT reales, read-only).",
            "Esperá el resultado: verás hasta 5 símbolos con score composite (volatilidad, volumen, liquidez).",
            "Anotá los símbolos (ej. BTCUSDT, ETHUSDT…). Opcional: Scan Binance USDT para bid/ask actual.",
        ),
        "next_prompt": "Cuando termines, escribime: «ya tengo el ranking, ¿qué MM probamos?»",
    },
    "mm_after_alpha": {
        "title": "Lección 2 — Elegir estrategia Market Making para las monedas detectadas",
        "steps": (
            "Volvé a Guided Lab (venue binance).",
            "Sección 3 Estrategia: elegí inventory_mm (empezá simple) o avellaneda_stoikov (avanzada).",
            "Sección 4: clic Backtest top 5 Binance — corre la estrategia elegida sobre las monedas del ranking.",
            "Revisá equity y fills por símbolo en el resultado del pipeline.",
            "Compará: inventory_mm en pares muy volátiles del ranking puede necesitar half_spread más amplio.",
            "Paper session automática con MM: panel Sesión Paper (después de validar backtest).",
        ),
        "next_prompt": "Si querés, preguntame: «explicame inventory_mm» o «qué parámetros tunear».",
    },
    "full_alpha_mm": {
        "title": "Flujo completo — Alpha Binance → Market Making",
        "steps": (
            "PASO A — Detectar monedas: Guided Lab → venue binance → Ranking alpha Binance.",
            "PASO B — Revisá el top 5: priorizá pares con buen composite y volumen (BTC/ETH suelen aparecer).",
            "PASO C — Estrategia MM: empezá con inventory_mm; si ya la dominás, probá avellaneda_stoikov.",
            "PASO D — Backtest: mismo Guided Lab → elegí la estrategia MM → Backtest top 5 Binance.",
            "PASO E — Interpretá: compará final_equity y n_fills entre símbolos; no es asesoramiento financiero.",
            "Recordá: LIVE_BLOCKED=True; esto es laboratorio paper, sin órdenes reales.",
        ),
        "next_prompt": "Decime «vamos al paso A» si querés que te guíe uno por uno.",
    },
}


class ToolRegistry:
    """Ejecuta solo tools allowlist; rechaza mutaciones / LIVE."""

    def __init__(
        self,
        state: WorkbenchState,
        *,
        docs_root: Path | None = None,
    ) -> None:
        self._state = state
        self._docs_root = docs_root if docs_root is not None else default_docs_root()

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
            "explain_guided_lab": self._explain_guided_lab,
            "explain_binance_lab": self._explain_binance_lab,
            "suggest_workflow": self._suggest_workflow,
            "instructor_guide": self._instructor_guide,
            "get_assistant_context": self._get_assistant_context,
            "search_docs": self._search_docs,
            "list_experiments": self._list_experiments,
            "explain_live_policy": self._explain_live_policy,
            "get_session_summary": self._get_session_summary,
            "list_reports": self._list_reports,
            "list_strategies": self._list_strategies,
            "open_pane": self._open_pane,
            "run_binance_alpha": self._run_binance_alpha,
            "run_binance_pipeline": self._run_binance_pipeline,
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

    def _explain_guided_lab(self, _args: dict[str, Any]) -> dict[str, Any]:
        return {
            "guide": _GUIDED_LAB_GUIDE,
            "panel": "guided_lab",
            "steps": ["unlock", "venue", "scan", "strategy", "simulate", "demo_a3"],
            "live_routing": False,
            "chat_mutations": False,
        }

    def _explain_binance_lab(self, _args: dict[str, Any]) -> dict[str, Any]:
        return {
            "guide": _BINANCE_LAB_GUIDE,
            "apis": [
                "/api/lab/binance/scan",
                "/api/lab/binance/scanner",
                "/api/lab/binance/pipeline",
            ],
            "read_only_md": True,
            "live_routing": False,
            "chat_mutations": False,
        }

    def _suggest_workflow(self, args: dict[str, Any]) -> dict[str, Any]:
        goal = str(args.get("goal") or args.get("objective") or "aprender").strip().lower()
        if goal not in _WORKFLOW_HINTS:
            for key in _WORKFLOW_HINTS:
                if key in goal:
                    goal = key
                    break
            else:
                goal = "aprender"
        return {
            "goal": goal,
            "workflow": _WORKFLOW_HINTS[goal],
            "available_goals": sorted(_WORKFLOW_HINTS.keys()),
            "live_routing": False,
            "chat_mutations": False,
        }

    def _extract_last_binance_symbols(self) -> list[str]:
        last = self._state.last_lab_result
        if not isinstance(last, dict):
            return []
        kind = str(last.get("kind") or "")
        if kind == "binance_scanner":
            raw = last.get("selected_symbols")
            return [str(s) for s in raw] if isinstance(raw, list) else []
        if kind == "binance_pipeline":
            scanner = last.get("scanner")
            if isinstance(scanner, dict):
                raw = scanner.get("selected_symbols")
                return [str(s) for s in raw] if isinstance(raw, list) else []
        if kind == "binance_backtest_batch":
            runs = last.get("runs")
            if isinstance(runs, list):
                return [str(r["symbol"]) for r in runs if isinstance(r, dict) and r.get("symbol")]
        return []

    def _instructor_guide(self, args: dict[str, Any]) -> dict[str, Any]:
        lesson = str(args.get("lesson") or "full_alpha_mm").strip().lower()
        if lesson not in _INSTRUCTOR_LESSONS:
            for key in _INSTRUCTOR_LESSONS:
                if key in lesson:
                    lesson = key
                    break
            else:
                lesson = "full_alpha_mm"

        payload = dict(_INSTRUCTOR_LESSONS[lesson])
        symbols = self._extract_last_binance_symbols()
        mm_only = [dict(s) for s in _MM_STRATEGIES]

        recommendations: list[dict[str, str]] = []
        for s in _MM_STRATEGIES:
            rec = dict(s)
            if symbols:
                rec["note"] = (
                    f"Probar en {', '.join(symbols[:3])}"
                    + ("…" if len(symbols) > 3 else "")
                )
            recommendations.append(rec)

        self._state.chat_instructor_ctx = {
            "lesson": lesson,
            "symbols": symbols,
            "awaiting": "mm_pick" if lesson == "alpha_binance" else None,
        }

        return {
            "ok": True,
            "kind": "instructor",
            "lesson": lesson,
            "title": payload["title"],
            "steps": list(payload["steps"]),
            "next_prompt": payload.get("next_prompt"),
            "detected_symbols": symbols,
            "mm_strategies": mm_only,
            "mm_recommendations": recommendations,
            "has_prior_scan": len(symbols) > 0,
            "live_routing": False,
            "chat_mutations": False,
        }

    def _get_assistant_context(self, args: dict[str, Any]) -> dict[str, Any]:
        from quantlab.workbench.chat.memory import ChatMemory

        memory = self._state.chat_memory if isinstance(self._state.chat_memory, ChatMemory) else ChatMemory()
        ui = args.get("ui_context")
        ui_ctx = ui if isinstance(ui, dict) else None
        ctx = build_assistant_context(self._state, memory, ui_context=ui_ctx)
        ctx["chat_mutations"] = False
        ctx["live_routing"] = False
        return ctx

    def _search_docs(self, args: dict[str, Any]) -> dict[str, Any]:
        raw_q = args.get("query") or args.get("q") or args.get("keywords") or ""
        if not isinstance(raw_q, str):
            raise ValidationError("search_docs: query debe ser string")
        return search_docs_files(raw_q, docs_root=self._docs_root, limit=8)

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

    def _get_session_summary(self, args: dict[str, Any]) -> dict[str, Any]:
        raw_limit = args.get("limit")
        if raw_limit is None:
            raw_limit = args.get("n")
        if raw_limit is None:
            raw_limit = args.get("activity_limit")
        if raw_limit is None:
            limit = DEFAULT_SESSION_ACTIVITY_LIMIT
        elif isinstance(raw_limit, bool) or not isinstance(raw_limit, int):
            raise ValidationError("get_session_summary: limit debe ser int")
        else:
            limit = clamp_limit(raw_limit)

        session = self._state.ensure_session()
        book = self._state.ensure_book()
        account = book.get_account()
        positions = book.get_positions()
        activity = list_activity(session.activity_path, limit=limit)
        raw_events = activity.get("events")
        events: list[Any] = raw_events if isinstance(raw_events, list) else []
        return {
            "ok": True,
            "kind": "session_summary",
            "session_id": session.session_id,
            "mode": self._state.mode.value,
            "venue": self._state.venue,
            "md_provider": self._state.md_provider,
            "book_equity": str(account.equity),
            "cash": str(account.cash),
            "currency": account.currency,
            "positions_count": len(positions),
            "activity_limit": limit,
            "activity_count": len(events),
            "activity": events,
            "live_blocked": LIVE_BLOCKED is True,
            "live_routing": False,
            "chat_mutations": False,
        }

    def _list_reports(self, args: dict[str, Any]) -> dict[str, Any]:
        raw_limit = args.get("limit")
        limit = 50 if raw_limit is None else raw_limit
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise ValidationError("list_reports: limit debe ser int")
        reports_root = self._state.ensure_lab_reports_dir()
        payload = list_lab_reports(reports_root, limit=limit)
        payload["chat_mutations"] = False
        return payload

    def _list_strategies(self, _args: dict[str, Any]) -> dict[str, Any]:
        strategies = list_strategy_catalog()
        return {
            "ok": True,
            "kind": "strategies",
            "count": len(strategies),
            "strategies": strategies,
            "live_blocked": LIVE_BLOCKED is True,
            "live_routing": False,
            "chat_mutations": False,
        }

    def _open_pane(self, args: dict[str, Any]) -> dict[str, Any]:
        raw = args.get("pane") or args.get("pane_id") or args.get("panel") or "guided_lab"
        if not isinstance(raw, str) or not raw.strip():
            raise ValidationError("open_pane: pane requerido")
        pane = raw.strip().lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "guided": "guided_lab",
            "lab": "guided_lab",
            "guide": "guided_lab",
            "alpha": "guided_lab",
            "binance": "guided_lab",
            "ia": "chat",
            "asistente": "chat",
        }
        pane = aliases.get(pane, pane)
        if pane not in ALLOWED_PANES:
            raise ValidationError(
                f"open_pane: panel no permitido {pane!r}. "
                f"Válidos: {', '.join(sorted(ALLOWED_PANES))}"
            )
        return {
            "ok": True,
            "kind": "open_pane",
            "pane": pane,
            "ui_actions": [{"type": "open_pane", "pane": pane}],
            "live_routing": False,
            "chat_mutations": False,
        }

    def _run_binance_alpha(self, args: dict[str, Any]) -> dict[str, Any]:
        top_n = args.get("top_n", 5)
        if not isinstance(top_n, int):
            top_n = 5
        result = lab_services.run_binance_lab_scanner(top_n=top_n, symbol_limit=15)
        stored = self._state.store_lab_result(result)
        symbols = list(stored.get("selected_symbols") or [])
        self._state.chat_instructor_ctx = {
            "lesson": "alpha_binance",
            "symbols": symbols,
            "awaiting": "mm_pick",
        }
        return {
            "ok": True,
            "kind": "binance_scanner",
            "selected_symbols": symbols,
            "n_symbols_fetched": stored.get("n_symbols_fetched"),
            "scores_preview": (stored.get("scores") or [])[:5],
            "ui_actions": [
                {"type": "open_pane", "pane": "guided_lab"},
                {"type": "toast", "message": "Alpha Binance listo: " + ", ".join(symbols[:5])},
            ],
            "live_routing": False,
            "read_only": True,
            "chat_mutations": False,
        }

    def _run_binance_pipeline(self, args: dict[str, Any]) -> dict[str, Any]:
        strategy_id = str(args.get("strategy_id") or args.get("strategy") or "inventory_mm")
        top_n = args.get("top_n", 5)
        if not isinstance(top_n, int):
            top_n = 5
        result = lab_services.run_binance_lab_pipeline(
            strategy_id=strategy_id,
            top_n=top_n,
            symbol_limit=15,
            experiment_id_prefix="wb-chat-pipe",
            reports_dir=self._state.ensure_lab_reports_dir(),
        )
        stored = self._state.store_lab_result(result)
        scanner = stored.get("scanner") if isinstance(stored.get("scanner"), dict) else {}
        symbols = list(scanner.get("selected_symbols") or [])
        batch = stored.get("backtests") if isinstance(stored.get("backtests"), dict) else {}
        return {
            "ok": stored.get("ok") is True,
            "kind": "binance_pipeline",
            "strategy_id": stored.get("strategy_id"),
            "selected_symbols": symbols,
            "n_ok": batch.get("n_ok"),
            "n_requested": batch.get("n_requested"),
            "ui_actions": [
                {"type": "open_pane", "pane": "guided_lab"},
                {
                    "type": "toast",
                    "message": (
                        f"Pipeline {strategy_id}: "
                        f"{batch.get('n_ok', 0)}/{batch.get('n_requested', 0)} ok"
                    ),
                },
            ],
            "live_routing": False,
            "read_only": True,
            "chat_mutations": False,
        }
