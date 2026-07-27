"""Cliente LLM HTTP OpenAI-compatible (stdlib) — opt-in con QUANTLAB_LLM_API_KEY."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.workbench.chat.tools import ALLOWED_TOOLS, ToolRegistry

_DEFAULT_BASE = "https://api.openai.com/v1"
_DEFAULT_MODEL = "gpt-4o-mini"
_MAX_TOOL_ROUNDS = 3
_TIMEOUT = 60.0

# Presets OpenAI-compatible (NVIDIA NIM, Gemini AI Studio, OpenAI).
# QUANTLAB_LLM_PROVIDER=nvidia|gemini|openai|assistant
_PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
    },
    "nvidia": {
        # https://build.nvidia.com → API key (gratis con cuenta)
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "meta/llama-3.1-70b-instruct",
    },
    "gemini": {
        # https://aistudio.google.com/apikey → gratis
        # Endpoint OpenAI-compatible de Google AI Studio
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "model": "gemini-2.0-flash",
    },
}


def resolve_llm_endpoint() -> tuple[str, str]:
    """Resuelve (base_url, model) desde env + preset de proveedor."""
    provider = os.environ.get("QUANTLAB_LLM_PROVIDER", "").strip().lower()
    if provider in {"", "assistant", "fake", "optional_env"}:
        provider = "openai"

    preset = _PROVIDER_PRESETS.get(provider, _PROVIDER_PRESETS["openai"])
    base = os.environ.get("QUANTLAB_LLM_BASE_URL", "").strip() or preset["base_url"]
    model = os.environ.get("QUANTLAB_LLM_MODEL", "").strip() or preset["model"]
    base = base.rstrip("/")
    # No forzar /v1: Gemini usa .../v1beta/openai (sin /v1 al final).
    return base, model


def _tool_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for name in sorted(ALLOWED_TOOLS):
        specs.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": f"QuantLab read-only tool: {name}",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "goal": {"type": "string"},
                            "lesson": {"type": "string"},
                            "limit": {"type": "integer"},
                        },
                        "additionalProperties": True,
                    },
                },
            }
        )
    return specs


def _post_json(url: str, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise ValidationError(f"LLM HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise ValidationError(f"LLM red: {exc.reason}") from exc
    except TimeoutError as exc:
        raise ValidationError("LLM timeout") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationError("LLM JSON inválido") from exc
    if not isinstance(data, dict):
        raise ValidationError("LLM respuesta inválida")
    return data


def complete_with_llm(
    *,
    system_prompt: str,
    history: list[dict[str, str]],
    user_message: str,
    tools: ToolRegistry,
) -> tuple[str, list[str], list[dict[str, Any]]]:
    """Una o más rondas chat/completions. Retorna (reply, tools_used, ui_actions)."""
    api_key = os.environ.get("QUANTLAB_LLM_API_KEY", "").strip()
    if not api_key or api_key in {"DISABLED", "0", "false", "FALSE", "none", "NONE"}:
        raise ValidationError("QUANTLAB_LLM_API_KEY no configurada")

    base, model = resolve_llm_endpoint()

    messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    tools_used: list[str] = []
    ui_actions: list[dict[str, Any]] = []
    url = f"{base}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    provider = os.environ.get("QUANTLAB_LLM_PROVIDER", "").strip().lower()
    prefer_plain = provider in {"nvidia", "gemini"} or "nvidia.com" in base or "googleapis.com" in base

    for round_i in range(_MAX_TOOL_ROUNDS):
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": 0.4,
        }
        use_tools = (not prefer_plain) or (round_i > 0 and tools_used)
        # Si el usuario pide abrir/correr, forzar tools aunque sea nvidia/gemini
        lower_msg = user_message.lower()
        if any(
            w in lower_msg
            for w in (
                "corré",
                "corre ",
                "ejecut",
                "haceme",
                "abrí",
                "abri ",
                "abrir",
                "run alpha",
                "run pipeline",
            )
        ):
            use_tools = True
        if use_tools:
            payload["tools"] = _tool_specs()
            payload["tool_choice"] = "auto"
        try:
            data = _post_json(url, headers, payload)
        except ValidationError as exc:
            if "tools" in payload:
                payload.pop("tools", None)
                payload.pop("tool_choice", None)
                data = _post_json(url, headers, payload)
            else:
                raise exc
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValidationError("LLM sin choices")
        choice0 = choices[0]
        if not isinstance(choice0, dict):
            raise ValidationError("LLM choice inválido")
        msg = choice0.get("message")
        if not isinstance(msg, dict):
            raise ValidationError("LLM message inválido")

        tool_calls = msg.get("tool_calls")
        if isinstance(tool_calls, list) and tool_calls:
            messages.append(msg)
            for tc in tool_calls:
                if not isinstance(tc, dict):
                    continue
                fn = tc.get("function")
                if not isinstance(fn, dict):
                    continue
                name = str(fn.get("name") or "")
                raw_args = fn.get("arguments") or "{}"
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else {}
                except json.JSONDecodeError:
                    args = {}
                if not isinstance(args, dict):
                    args = {}
                result = tools.call(name, args)
                tools_used.append(name)
                raw_actions = result.get("ui_actions") if isinstance(result, dict) else None
                if isinstance(raw_actions, list):
                    for act in raw_actions:
                        if isinstance(act, dict):
                            ui_actions.append(act)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.get("id"),
                        "content": json.dumps(result, ensure_ascii=False)[:8000],
                    }
                )
            continue

        content = msg.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip(), tools_used, ui_actions
        raise ValidationError("LLM respuesta vacía")

    raise ValidationError("LLM excedió rondas de tools")
