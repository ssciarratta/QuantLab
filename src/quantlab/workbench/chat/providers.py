"""Chat providers: FakeProvider (default CI) + OptionalEnvProvider (opt-in)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from quantlab.workbench.chat.tools import ToolRegistry

# Placeholders: nunca secretos reales. DISABLED = off en CI.
_DISABLED_KEYS = frozenset({"", "DISABLED", "0", "false", "FALSE", "none", "NONE"})


@dataclass(frozen=True, slots=True)
class ChatTurnResult:
    reply: str
    tools_used: list[str] = field(default_factory=list)
    provider: str = "fake"


@runtime_checkable
class ChatProvider(Protocol):
    """Protocolo mínimo de proveedor de chat."""

    def complete(self, message: str, tools: ToolRegistry) -> ChatTurnResult: ...


def llm_api_key_configured() -> bool:
    raw = os.environ.get("QUANTLAB_LLM_API_KEY", "DISABLED").strip()
    return raw not in _DISABLED_KEYS


class FakeProvider:
    """Proveedor determinista offline/CI: intents en español + tools allowlist."""

    name = "fake"

    def complete(self, message: str, tools: ToolRegistry) -> ChatTurnResult:
        text = message.strip()
        lower = text.lower()
        tools_used: list[str] = []
        parts: list[str] = []

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
        elif _match(lower, ("doc", "docs", "document", "ayuda", "help", "cómo", "como")):
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
                "Puedo explicar salud, modo, resumen de sesión, reportes, "
                "estrategias, backtest, scanner y política LIVE. "
                f"Paneles: {', '.join(ids[:8])}. No envío órdenes."
            )
            policy = use("explain_live_policy")
            parts.append(f"live_blocked={policy.get('live_blocked')} (siempre True aquí).")
        else:
            policy = use("explain_live_policy")
            caps = use("list_capabilities")
            parts.append(
                "Asistente QuantLab (FakeProvider). Preguntá por salud, modo, "
                "resumen de sesión, reportes, estrategias, backtest, scanner, "
                "venues, experimentos, docs o política LIVE. "
                f"live_blocked={policy.get('live_blocked')}. "
                f"features={len(caps.get('features') or [])}."
            )

        reply = " ".join(parts).strip()
        # Dedup tools_used preservando orden
        seen: set[str] = set()
        ordered: list[str] = []
        for t in tools_used:
            if t not in seen:
                seen.add(t)
                ordered.append(t)
        return ChatTurnResult(reply=reply, tools_used=ordered, provider=self.name)


class OptionalEnvProvider:
    """Opt-in vía QUANTLAB_LLM_API_KEY. No se usa en tests CI.

    Si la key está DISABLED/ausente → delega a FakeProvider.
    Si está configurada → anota provider=optional_env y reutiliza el routing
    safe-by-default (sin HTTP de mercado; sin flip LIVE). El endpoint LLM
    externo queda documentado en .env.example para fases futuras.
    """

    name = "optional_env"

    def __init__(self, fallback: FakeProvider | None = None) -> None:
        self._fallback = fallback if fallback is not None else FakeProvider()

    def complete(self, message: str, tools: ToolRegistry) -> ChatTurnResult:
        if not llm_api_key_configured():
            return self._fallback.complete(message, tools)
        # Key presente: mismo tool-routing seguro; marca provider.
        base = self._fallback.complete(message, tools)
        base_url = os.environ.get("QUANTLAB_LLM_BASE_URL", "").strip() or "(unset)"
        model = os.environ.get("QUANTLAB_LLM_MODEL", "").strip() or "(default)"
        note = (
            f"[optional_env model={model} base={base_url}] "
            "Respuesta safe-by-default (sin operar mercado). "
        )
        return ChatTurnResult(
            reply=note + base.reply,
            tools_used=list(base.tools_used),
            provider=self.name,
        )


def build_default_provider() -> ChatProvider:
    """CI/default: FakeProvider. Opt-in LLM solo si API key no está DISABLED."""
    if llm_api_key_configured():
        return OptionalEnvProvider()
    return FakeProvider()


def _match(lower: str, needles: tuple[str, ...]) -> bool:
    return any(n in lower for n in needles)


def _extract_query(message: str) -> str:
    # Quita palabras de ayuda y deja keywords útiles
    cleaned = re.sub(
        r"\b(ayuda|help|docs?|documentaci[oó]n|busca|buscar|sobre|de|el|la|los|las)\b",
        " ",
        message,
        flags=re.IGNORECASE,
    )
    return " ".join(cleaned.split())
