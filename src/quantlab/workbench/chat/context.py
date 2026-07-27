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


def _read_guide_excerpt(max_chars: int = 5000) -> str:
    root = default_docs_root().parent  # docs/
    guide = root / "GUIA_COMPLETA_QUANTLAB.md"
    if not guide.is_file():
        return "QuantLab = laboratorio cuantitativo. Guided Lab, Binance MD read-only, paper fills."
    try:
        text = guide.read_text(encoding="utf-8")
    except OSError:
        return ""
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

    return (
        "Sos el asistente instructor de QuantLab (laboratorio cuantitativo, NO bot de trading).\n"
        "Respondé en español, conversacional y claro — como un mentor que guía paso a paso.\n"
        "PRIORIDAD: explicá botones de la UI (Guided Lab), NO pegues listas de APIs /api/* "
        "salvo que el usuario pida API.\n"
        "Si el usuario dice ABRÍ / ABRIR un panel → usá tool open_pane.\n"
        "Si dice CORRÉ / EJECUTÁ alpha/ranking → usá run_binance_alpha.\n"
        "Si dice CORRÉ pipeline/backtest MM → usá run_binance_pipeline "
        "(strategy_id inventory_mm o avellaneda_stoikov o momentum).\n"
        "Si pregunta CÓMO HAGO (sin pedir ejecución) → explicá pasos Guided Lab, no ejecutes.\n"
        "Cómo correr alpha (solo explicación):\n"
        "1) QL → Guided Lab · 2) Venue=binance · 3) Ranking alpha Binance · "
        "4) inventory_mm → Backtest top 5 Binance.\n"
        "REGLAS IRRENUNCIABLES:\n"
        "- LIVE_BLOCKED=True: nunca enviás órdenes ni desbloqueás LIVE.\n"
        "- REAL=PAPER: fills simulados.\n"
        "- Binance MD público = read-only; demo solo post-unlock humano.\n"
        "- No inventes features: si no sabés, decí qué panel o botón usar en Guided Lab.\n"
        f"Versión: {ctx.get('version')}. Modo: {ctx.get('mode')}. Venue: {ctx.get('venue')}.\n"
        f"Último resultado lab: {lab_line}.\n"
        f"Contexto instructor: {ctx.get('instructor')}.\n"
        "Estrategias Market Making disponibles:\n"
        + ("\n".join(mm_lines) if mm_lines else "(ver catálogo)")
        + "\n\nFlujo típico alpha→MM: Guided Lab → venue binance → Ranking alpha Binance → "
        "elegir inventory_mm o avellaneda_stoikov → Backtest top 5 Binance.\n"
        "Usá la memoria de la conversación para continuar hilos ('dale', 'siguiente', 'y ahora').\n"
        "Conocimiento del proyecto (extracto):\n"
        + str(ctx.get("guide_excerpt", ""))[:3500]
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
