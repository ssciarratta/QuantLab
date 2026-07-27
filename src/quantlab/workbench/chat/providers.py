"""Chat providers: asistente con memoria + LLM opt-in (OpenAI-compatible)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from quantlab.workbench.chat.memory import ChatMessage
from quantlab.workbench.chat.tools import ToolRegistry

def format_instructor_reply(data: dict[str, Any]) -> str:
    """Formatea lección instructor en texto legible (multi-línea)."""
    lines: list[str] = [str(data.get("title", "Instructor QuantLab")), ""]
    steps = data.get("steps") or []
    if isinstance(steps, list):
        for i, step in enumerate(steps, 1):
            lines.append(f"Paso {i}: {step}")
    symbols = data.get("detected_symbols") or []
    if isinstance(symbols, list) and symbols:
        lines.append("")
        lines.append("Monedas de tu último scan en sesión: " + ", ".join(str(s) for s in symbols))
    recs = data.get("mm_recommendations") or []
    if isinstance(recs, list) and recs:
        lines.append("")
        lines.append("Estrategias Market Making que podés probar:")
        for rec in recs:
            if not isinstance(rec, dict):
                continue
            sid = rec.get("id", "?")
            name = rec.get("name", sid)
            when = rec.get("when", "")
            params = rec.get("params", "")
            note = rec.get("note", "")
            lines.append(f"  • {name} ({sid}): {when}")
            if params:
                lines.append(f"    Parámetros: {params}")
            if note:
                lines.append(f"    {note}")
    nxt = data.get("next_prompt")
    if nxt:
        lines.append("")
        lines.append(str(nxt))
    return "\n".join(lines).strip()

# Placeholders: nunca secretos reales. DISABLED = off en CI.
_DISABLED_KEYS = frozenset({"", "DISABLED", "0", "false", "FALSE", "none", "NONE"})


@dataclass(frozen=True, slots=True)
class ChatRequest:
    """Turno del chat con memoria y contexto de sesión."""

    message: str
    history: tuple[ChatMessage, ...] = ()
    ui_context: dict[str, Any] | None = None
    assistant_context: dict[str, Any] | None = None
    system_prompt: str = ""


@dataclass(frozen=True, slots=True)
class ChatTurnResult:
    reply: str
    tools_used: list[str] = field(default_factory=list)
    provider: str = "fake"


@runtime_checkable
class ChatProvider(Protocol):
    """Protocolo mínimo de proveedor de chat."""

    def complete(self, request: ChatRequest, tools: ToolRegistry) -> ChatTurnResult: ...


def llm_api_key_configured() -> bool:
    raw = os.environ.get("QUANTLAB_LLM_API_KEY", "DISABLED").strip()
    return raw not in _DISABLED_KEYS


class FakeProvider:
    """Asistente local offline: intents + memoria conversacional (CI/default)."""

    name = "fake"

    def complete(self, request: ChatRequest | str, tools: ToolRegistry) -> ChatTurnResult:
        if isinstance(request, str):
            request = ChatRequest(message=request)
        text = _normalize_user_text(_resolve_followup(request))
        lower = text.lower()
        tools_used: list[str] = []
        parts: list[str] = []

        # Contexto de sesión en cada turno (memoria operativa)
        try:
            ctx_data = tools.call("get_assistant_context", {})
            tools_used.append("get_assistant_context")
            prefix = _memory_aware_prefix(request, ctx_data)
            if prefix:
                parts.append(prefix)
        except Exception:  # noqa: BLE001 — best effort
            pass

        def use(tool_name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
            result = tools.call(tool_name, args)
            tools_used.append(tool_name)
            return result

        # Intents (orden importa: live antes que modo; resumen antes que docs/cómo)
        if _match(lower, ("live", "orden", "órdenes", "ordenes", "flip", "routing")):
            data = use("explain_live_policy")
            parts.append(
                "Política LIVE: "
                + str(data.get("policy", ""))
                + f" live_blocked={data.get('live_blocked')}."
            )
        elif _match(
            lower,
            (
                "cómo estoy",
                "como estoy",
                "resumen sesión",
                "resumen sesion",
                "resumen de sesión",
                "resumen de sesion",
                "resumen de la sesión",
                "resumen de la sesion",
            ),
        ):
            data = use("get_session_summary")
            parts.append(
                "Resumen de sesión: "
                f"mode={data.get('mode')}, venue={data.get('venue')}, "
                f"equity={data.get('book_equity')} {data.get('currency')}, "
                f"posiciones={data.get('positions_count')}, "
                f"activity_last={data.get('activity_count')} "
                f"(limit={data.get('activity_limit')}). "
                f"live_blocked={data.get('live_blocked')}."
            )
        # Instructor (antes de intents genéricos alpha/binance)
        elif _is_alpha_mm_flow(lower):
            lesson = "full_alpha_mm"
            if _match(lower, ("market mak", "market-mak", " mm", "inventory", "avellaneda", "stoikov")):
                if not _match(lower, ("alpha", "binance", "detectar", "moneda", "correr", "corramos", "vamos")):
                    lesson = "mm_after_alpha"
            elif _match(lower, ("alpha", "ranking", "scanner", "detectar", "moneda")):
                if not _match(lower, ("market mak", " mm", "inventory", "avellaneda")):
                    lesson = "alpha_binance"
            data = use("instructor_guide", {"lesson": lesson})
            parts.append(format_instructor_reply(data))
        elif _match(
            lower,
            (
                "market mak",
                "market-mak",
                "market making",
                " mm",
                "inventory_mm",
                "avellaneda",
                "stoikov",
                "cotizador",
            ),
        ) and _match(lower, ("estrateg", "probar", "cuál", "cual", "qué", "que", "recomend")):
            data = use("instructor_guide", {"lesson": "mm_after_alpha"})
            parts.append(format_instructor_reply(data))
        elif _match(
            lower,
            (
                "ya tengo el ranking",
                "ya corrí alpha",
                "ya corri alpha",
                "tengo las monedas",
                "listo el ranking",
            ),
        ):
            data = use("instructor_guide", {"lesson": "mm_after_alpha"})
            parts.append(format_instructor_reply(data))
        elif _match(lower, ("reportes", "qué reportes", "que reportes", "lista de reportes")):
            data = use("list_reports")
            reports = data.get("reports") or []
            n = data.get("count", len(reports) if isinstance(reports, list) else 0)
            ids: list[str] = []
            if isinstance(reports, list):
                for item in reports[:5]:
                    if isinstance(item, dict) and item.get("report_id"):
                        ids.append(str(item["report_id"]))
            preview = ", ".join(ids) if ids else "(ninguno)"
            parts.append(f"Reportes en sesión: {n}. Últimos: {preview}.")
        elif _match(
            lower,
            (
                "estrategias",
                "qué estrategias",
                "que estrategias",
                "listar estrategias",
                "catálogo de estrategias",
                "catalogo de estrategias",
            ),
        ):
            data = use("list_strategies")
            strategies = data.get("strategies") or []
            ids = [
                str(s.get("id"))
                for s in strategies
                if isinstance(s, dict) and s.get("id") is not None
            ]
            parts.append(
                f"Estrategias del catálogo ({data.get('count', len(ids))}): "
                + (", ".join(ids) if ids else "(vacío)")
                + "."
            )
        elif _match(
            lower,
            (
                "guided lab",
                "guidedlab",
                "wizard",
                "paso a paso",
                "cómo uso",
                "como uso",
                "cómo se usa",
                "como se usa",
            ),
        ):
            data = use("explain_guided_lab")
            parts.append(str(data.get("guide", "")))
        elif _match(
            lower,
            (
                "binance",
                "usdt",
                "ranking alpha",
                "pipeline binance",
                "scan binance",
                "top 5",
                "top5",
            ),
        ):
            data = use("explain_binance_lab")
            parts.append(str(data.get("guide", "")))
            apis = data.get("apis") or []
            if apis:
                parts.append("APIs: " + ", ".join(str(a) for a in apis) + ".")
        elif _match(
            lower,
            (
                "cómo empiezo",
                "como empiezo",
                "por dónde empiezo",
                "por donde empiezo",
                "primeros pasos",
                "quiero probar",
                "empezar",
                "no sé usar",
                "no se usar",
            ),
        ):
            goal = "estrategia" if _match(lower, ("estrategia", "backtest", "momentum")) else "aprender"
            if _match(lower, ("binance", "usdt", "crypto")):
                goal = "binance"
            elif _match(lower, ("a3", "remarkets", "rofex")):
                goal = "a3"
            data = use("suggest_workflow", {"goal": goal})
            parts.append(str(data.get("workflow", "")))
            parts.append(f"Objetivos disponibles: {', '.join(data.get('available_goals') or [])}.")
        elif _match(lower, ("salud", "health", "estado", "checks")):
            data = use("get_health")
            ok = data.get("ok")
            ver = data.get("version")
            live_b = data.get("live_blocked")
            parts.append(
                f"Salud del sistema: ok={ok}, version={ver}, live_blocked={live_b}. "
                "Checks locales sin probes LIVE."
            )
        elif _match(lower, ("modo", "mode", "tester", "paper", "real")):
            data = use("get_mode")
            parts.append(
                f"Modo actual: {data.get('mode')}. "
                f"LIVE_BLOCKED={data.get('live_blocked')}. "
                f"REAL alias → {data.get('real_alias')} (PAPER)."
            )
        elif _match(lower, ("backtest", "back test", "estrategia", "momentum")):
            data = use("explain_backtest")
            parts.append(str(data.get("guide", "")))
            if data.get("has_last"):
                summary = data.get("last_summary") or {}
                parts.append(
                    "Último resultado de sesión: "
                    f"kind={summary.get('kind')}, ok={summary.get('ok')}, "
                    f"strategy={summary.get('strategy_id')}."
                )
            else:
                parts.append("Aún no hay backtest en esta sesión.")
        elif _match(lower, ("scanner", "alpha", "optimize", "montecarlo", "capacidad")):
            if _match(lower, ("binance", "usdt", "moneda", "crypto")):
                data = use("instructor_guide", {"lesson": "alpha_binance"})
                parts.append(format_instructor_reply(data))
            else:
                data = use("list_capabilities")
                feats = data.get("features") or []
                ids = [str(f.get("id")) for f in feats if isinstance(f, dict)]
                parts.append(
                    "Capacidades del laboratorio: "
                    + (", ".join(ids) if ids else "(vacío)")
                    + ". Usá el menú Laboratorio o /api/lab/*."
                )
        elif _match(lower, ("venue", "venues", "broker", "exchange")):
            data = use("list_venues")
            venues = data.get("venues") or []
            parts.append("Venues disponibles: " + (", ".join(venues) if venues else "(ninguno)"))
        elif _match(lower, ("experimento", "experiment", "registry")):
            data = use("list_experiments")
            exps = data.get("experiments") or data.get("items") or []
            n = len(exps) if isinstance(exps, list) else 0
            parts.append(f"Experimentos en registry de sesión: {n}.")
        elif _match(lower, ("doc", "docs", "document", "ayuda", "help")) or (
            _match(lower, ("cómo", "como"))
            and not _match(lower, ("binance", "alpha", "scanner", "guided", "mm", "market"))
        ):
            # search_docs + capabilities para ayuda
            q = _extract_query(text) or "workbench LIVE"
            docs = use("search_docs", {"query": q})
            caps = use("list_capabilities")
            matches = docs.get("matches") or []
            if matches:
                first = matches[0]
                parts.append(f"Docs: {first.get('file')} — {first.get('snippet', '')[:200]}")
            else:
                parts.append("No encontré coincidencias fuertes en docs/*.md.")
            feats = caps.get("features") or []
            ids = [str(f.get("id")) for f in feats if isinstance(f, dict)]
            parts.append(
                "Ayuda rápida: soy el asistente research (safe-mode). "
                "Preguntá por Guided Lab, Binance lab, salud, modo, resumen de sesión, "
                "reportes, estrategias, backtest, scanner y política LIVE. "
                f"Paneles: {', '.join(ids[:8])}. No envío órdenes."
            )
            policy = use("explain_live_policy")
            parts.append(f"live_blocked={policy.get('live_blocked')} (siempre True aquí).")
        else:
            policy = use("explain_live_policy")
            caps = use("list_capabilities")
            parts.append(
                "Asistente QuantLab (FakeProvider). Preguntá por Guided Lab, Binance, "
                "cómo empiezo, salud, modo, resumen de sesión, reportes, estrategias, "
                "backtest, scanner, venues, experimentos, docs o política LIVE. "
                f"live_blocked={policy.get('live_blocked')}. "
                f"features={len(caps.get('features') or [])}."
            )

        reply = "\n\n".join(p for p in parts if p).strip()
        if not reply:
            reply = "No tengo una respuesta para eso todavía. Probá reformular o pedime «cómo empiezo»."
        # Dedup tools_used preservando orden
        seen: set[str] = set()
        ordered: list[str] = []
        for t in tools_used:
            if t not in seen:
                seen.add(t)
                ordered.append(t)
        return ChatTurnResult(reply=reply, tools_used=ordered, provider=self.name)


class AssistantProvider:
    """Asistente principal: LLM HTTP si hay API key; si no, FakeProvider con memoria."""

    name = "assistant"

    def __init__(self, fallback: FakeProvider | None = None) -> None:
        self._fallback = fallback if fallback is not None else FakeProvider()

    def complete(self, request: ChatRequest | str, tools: ToolRegistry) -> ChatTurnResult:
        if isinstance(request, str):
            request = ChatRequest(message=request)
        if llm_api_key_configured():
            try:
                from quantlab.workbench.chat.llm_http import complete_with_llm

                history = [
                    {"role": m.role, "content": m.content}
                    for m in request.history
                    if m.role in {"user", "assistant"}
                ][-16:]
                # El último user ya está en memoria; evitar duplicar en history
                if history and history[-1]["role"] == "user":
                    history = history[:-1]
                reply, tools_used = complete_with_llm(
                    system_prompt=request.system_prompt or "Sos el asistente QuantLab.",
                    history=history,
                    user_message=request.message,
                    tools=tools,
                )
                return ChatTurnResult(
                    reply=reply,
                    tools_used=tools_used,
                    provider="llm",
                )
            except Exception as exc:  # noqa: BLE001 — fallback a offline
                base = self._fallback.complete(request, tools)
                note = (
                    f"(NVIDIA/Gemini no respondió: {type(exc).__name__}. "
                    "Uso instructor local.)\n\n"
                )
                return ChatTurnResult(
                    reply=note + base.reply,
                    tools_used=list(base.tools_used),
                    provider="fake_fallback",
                )
        return self._fallback.complete(request, tools)


class OptionalEnvProvider(AssistantProvider):
    """Alias retrocompatible F22 → AssistantProvider."""

    name = "optional_env"


def build_default_provider() -> ChatProvider:
    """Default: AssistantProvider (LLM opt-in + memoria offline)."""
    return AssistantProvider()


def _match(lower: str, needles: tuple[str, ...]) -> bool:
    return any(n in lower for n in needles)


def _normalize_user_text(text: str) -> str:
    """Corrige typos frecuentes del operador (schaner→scanner, etc.)."""
    out = text
    replacements = (
        ("schaner", "scanner"),
        ("scannner", "scanner"),
        ("scaner", "scanner"),
        ("alpah", "alpha"),
        ("binace", "binance"),
        ("binanse", "binance"),
        ("maket making", "market making"),
        ("market makin", "market making"),
    )
    lower = out.lower()
    for bad, good in replacements:
        if bad in lower:
            # reemplazo case-insensitive simple
            idx = lower.find(bad)
            out = out[:idx] + good + out[idx + len(bad) :]
            lower = out.lower()
    return out


def _is_alpha_mm_flow(lower: str) -> bool:
    has_alpha = _match(
        lower,
        ("alpha", "ranking", "scanner", "detectar moneda", "detectar monedas", "monedas"),
    )
    has_binance = _match(lower, ("binance", "usdt", "crypto"))
    has_mm = _match(
        lower,
        ("market mak", "market-mak", "market making", " mm", "inventory", "avellaneda", "stoikov"),
    )
    has_run = _match(lower, ("correr", "corramos", "vamos", "quiero", "necesito", "probemos"))
    if has_alpha and has_binance and has_mm:
        return True
    if has_alpha and has_binance and has_run:
        return True
    if has_binance and has_mm and has_run:
        return True
    return False


def _extract_query(message: str) -> str:
    # Quita palabras de ayuda y deja keywords útiles
    cleaned = re.sub(
        r"\b(ayuda|help|docs?|documentaci[oó]n|busca|buscar|sobre|de|el|la|los|las)\b",
        " ",
        message,
        flags=re.IGNORECASE,
    )
    return " ".join(cleaned.split())


def _is_followup(lower: str) -> bool:
    return _match(
        lower,
        (
            "dale",
            "ok",
            "okay",
            "sí",
            "si",
            "listo",
            "siguiente",
            "continuá",
            "continua",
            "y ahora",
            "y después",
            "y despues",
            "seguimos",
            "perfecto",
            "bien",
            "hecho",
            "ya está",
            "ya esta",
        ),
    )


def _resolve_followup(request: ChatRequest) -> str:
    """Expande mensajes cortos usando memoria (ej. «dale» → siguiente paso)."""
    text = request.message.strip()
    lower = text.lower()
    if not _is_followup(lower) and len(lower) > 12:
        return text

    _last_user, last_assistant = _last_exchange_from_request(request)
    instructor = {}
    if isinstance(request.assistant_context, dict):
        instructor = request.assistant_context.get("instructor") or {}
    lesson = instructor.get("lesson") if isinstance(instructor, dict) else None

    asst_text = (last_assistant.content if last_assistant else "").lower()

    if _match(lower, ("dale", "sí", "si", "ok", "vamos", "siguiente", "continu", "seguimos", "bien", "listo", "hecho")):
        if lesson == "alpha_binance" or "ranking alpha" in asst_text:
            return "ya tengo el ranking, ¿qué estrategia de market making probamos?"
        if lesson == "mm_after_alpha" or "inventory_mm" in asst_text:
            return "explicame cómo tunear inventory_mm para las monedas del ranking"
        if "paso 1" in asst_text or "paso a" in asst_text:
            return "vamos a correr alpha en binance y detectar monedas"
        if _match(lower, ("listo", "hecho", "ya está", "ya esta")):
            return "ya tengo el ranking, ¿qué MM probamos?"

    if _match(lower, ("mm", "market")) and len(lower) < 20:
        return "qué estrategia de market making recomendás para el ranking binance"

    return text


def _last_exchange_from_request(
    request: ChatRequest,
) -> tuple[ChatMessage | None, ChatMessage | None]:
    last_user: ChatMessage | None = None
    last_assistant: ChatMessage | None = None
    for msg in reversed(request.history):
        if msg.role == "assistant" and last_assistant is None:
            last_assistant = msg
        elif msg.role == "user" and last_user is None:
            last_user = msg
        if last_user and last_assistant:
            break
    return last_user, last_assistant


def _memory_aware_prefix(request: ChatRequest, ctx: dict[str, Any]) -> str:
    """Saludo contextual breve si hay memoria o lab previo."""
    lines: list[str] = []
    turns = int(ctx.get("memory_turns") or 0)
    if turns > 2:
        lines.append(f"(Recuerdo nuestra conversación — {turns} mensajes en sesión.)")

    last_lab = ctx.get("last_lab")
    if isinstance(last_lab, dict) and last_lab.get("kind"):
        syms = last_lab.get("selected_symbols")
        if isinstance(syms, list) and syms:
            lines.append(f"Tu último scan Binance: {', '.join(str(s) for s in syms[:5])}.")
        elif last_lab.get("strategy_id"):
            lines.append(f"Último backtest: {last_lab.get('strategy_id')}.")

    if not lines:
        return ""
    return " ".join(lines)
