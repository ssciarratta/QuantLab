"""Contexto del asistente: sesión + memoria + conocimiento del proyecto."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.chat.memory import ChatMemory
from quantlab.workbench.docs_browser import default_docs_root
from quantlab.workbench.strategy_catalog import list_strategy_catalog

if TYPE_CHECKING:
    from quantlab.workbench.chat.tools import ToolRegistry

# Mapa mental del Workbench (fuente de verdad para el prompt).
PRODUCT_MAP = """
MAPA DE PANELES (no son intercambiables):
• Guided Lab = aprender / wizard en UN venue (Binance, paper o A3). Paso a paso.
• Alpha Scanner = ranking de monedas multi-mercado con MD real. Score ≠ predicción ni PnL.
• Simulador = comparar exchanges × monedas × leverage × fees (Comparar / Ranking / memo).
• Estrategias = catálogo con guías; «Abrir en Simulador».
• Monte Carlo = estrés estadístico (N escenarios). NO es predicción ni trading automático.
• Mis simulaciones = historial local (Comparar/Ranking/MC) · Reabrir = mismos params · Memo.
• Backtest = motor técnico sobre velas SINTÉTICAS (debug), no mercado real.
• Reports / Metrics = resultados de sesión.

MENÚ: botón QL (abajo izq) o click en QUANTLAB (arriba) · Ctrl+K = palette.
FAVORITOS tip: Chat IA · Scanner · Simulador · Estrategias.

INVARIANTES:
• LIVE_BLOCKED=True — nunca órdenes a venue real; el chat NO puede desbloquear LIVE.
• REAL (producto) = PAPER — fills simulados.
• Score/ranking ≠ rentabilidad garantizada · research, no asesoramiento financiero.
""".strip()


def _read_guide_excerpt(max_chars: int = 2800) -> str:
    root = default_docs_root().parent  # docs/
    guide = root / "GUIA_COMPLETA_QUANTLAB.md"
    if not guide.is_file():
        return PRODUCT_MAP
    try:
        text = guide.read_text(encoding="utf-8")
    except OSError:
        return PRODUCT_MAP
    return text[:max_chars]


def _summarize_last_lab(last: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(last, dict):
        return None
    kind = last.get("kind")
    out: dict[str, Any] = {"kind": kind, "ok": last.get("ok")}
    if kind == "binance_scanner":
        out["selected_symbols"] = list(last.get("selected_symbols") or [])
    elif kind == "binance_pipeline":
        scanner = last.get("scanner")
        if isinstance(scanner, dict):
            out["selected_symbols"] = list(scanner.get("selected_symbols") or [])
        out["strategy_id"] = last.get("strategy_id")
    elif kind == "backtest":
        out["strategy_id"] = last.get("strategy_id")
        out["instrument_id"] = last.get("instrument_id")
        out["final_equity"] = last.get("final_equity")
    elif kind in {"venue_scanner", "sim_compare", "montecarlo"}:
        out["note"] = f"último lab kind={kind}"
    return out


def build_assistant_context(
    state: WorkbenchState,
    memory: ChatMemory,
    *,
    ui_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Snapshot read-only para el asistente (sin secretos)."""
    session = state.session
    strategies = list_strategy_catalog()
    mm = [s for s in strategies if isinstance(s, dict) and "mm" in (s.get("tags") or [])]

    ctx: dict[str, Any] = {
        "product": "QuantLab Workbench",
        "version": __version__,
        "live_blocked": LIVE_BLOCKED is True,
        "real_is_paper": True,
        "mode": state.mode.value,
        "venue": state.venue,
        "session_id": session.session_id if session else None,
        "instructor": dict(state.chat_instructor_ctx),
        "last_lab": _summarize_last_lab(state.last_lab_result),
        "memory_turns": len(memory.messages),
        "memory_summary": memory.summary_text(8),
        "mm_strategies": mm,
        "strategy_ids": [s.get("id") for s in strategies if isinstance(s, dict)],
        "ui_context": ui_context or {},
        "product_map": PRODUCT_MAP,
        "guide_excerpt": _read_guide_excerpt(),
    }
    return ctx


def build_system_prompt(ctx: dict[str, Any]) -> str:
    """System prompt para LLM o referencia del asistente local."""
    mm_lines = []
    for s in ctx.get("mm_strategies") or []:
        if isinstance(s, dict):
            mm_lines.append(f"- {s.get('id')}: {s.get('description', '')}")

    last_lab = ctx.get("last_lab")
    lab_line = "ninguno"
    if isinstance(last_lab, dict) and last_lab.get("kind"):
        lab_line = str(last_lab)

    product_map = str(ctx.get("product_map") or PRODUCT_MAP)

    return (
        "Sos el asistente instructor de QuantLab Workbench "
        "(laboratorio cuantitativo, NO bot de trading).\n"
        "Respondé en español, claro y útil — mentor práctico, no menú de keywords.\n"
        "\n"
        f"{product_map}\n"
        "\n"
        "CÓMO RESPONDER:\n"
        "1) Contestá primero la pregunta (1–3 párrafos o pasos numerados).\n"
        "2) Si falta un dato clave (qué panel, qué moneda, N escenarios), "
        "repreguntá UNA sola cosa concreta al final.\n"
        "3) Ofrecé el siguiente paso actionable (ej. «¿Abrimos el Simulador?»).\n"
        "4) NO pegues listas de /api/* salvo que pidan API.\n"
        "5) NO inventes paneles ni botones: usá el mapa de arriba.\n"
        "\n"
        "TOOLS:\n"
        "• Abrí / abrir / mostrá panel → open_pane "
        "(simulator, montecarlo, scanner, strategies, sim_registry, guided_lab, …).\n"
        "• Explicar Monte Carlo / Simulador / Scanner / Guided → "
        "explain_montecarlo / explain_simulator / explain_scanner / explain_guided_lab.\n"
        "• Mapa general → explain_workbench_map.\n"
        "• CORRÉ alpha/ranking (imperativo) → run_binance_alpha.\n"
        "• CORRÉ pipeline/backtest MM → run_binance_pipeline.\n"
        "• «Cómo hago…» sin pedir ejecución → explicá pasos, no ejecutes.\n"
        "\n"
        f"Versión: {ctx.get('version')}. Modo: {ctx.get('mode')}. Venue: {ctx.get('venue')}.\n"
        f"Último resultado lab: {lab_line}.\n"
        f"Contexto instructor: {ctx.get('instructor')}.\n"
        "Estrategias Market Making:\n"
        + ("\n".join(mm_lines) if mm_lines else "(ver list_strategies)")
        + "\nUsá la memoria para continuar hilos («dale», «siguiente», «y ahora»).\n"
        "Extracto guía:\n"
        + str(ctx.get("guide_excerpt", ""))[:2200]
    )


def prefetch_tool_context(tools: ToolRegistry) -> tuple[list[str], dict[str, Any]]:
    """Pre-carga contexto útil (solo lectura) para respuestas más ricas."""
    used: list[str] = []
    bundle: dict[str, Any] = {}
    prefetch: list[tuple[str, dict[str, Any]]] = [
        ("get_mode", {}),
        ("list_strategies", {}),
    ]
    for name, args in prefetch:
        try:
            bundle[name] = tools.call(name, args)
            used.append(name)
        except Exception:  # noqa: BLE001 — prefetch best-effort
            continue
    return used, bundle
