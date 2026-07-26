# Fase 22 — Chat IA safe-by-default

**Estado:** IMPLEMENTADO (v0.14.0)  
**Prerrequisito:** F21 Lab Panels (v0.13.0)  
**Decisión:** DEC-063 (providers DEC-064, audit DEC-065)

## Objetivo

Chat en el panel del workbench para conversar **qué hacer** y **cómo implementarlo**
en QuantLab — **sin** poder operar mercado ni flippear LIVE.

## Stack

```text
src/quantlab/workbench/chat/
├── __init__.py
├── orchestrator.py    # ChatOrchestrator
├── tools.py           # ToolRegistry allowlist read-only
├── providers.py       # ChatProvider + FakeProvider + OptionalEnvProvider
└── audit.py           # append-only chat_audit.jsonl
```

## Tools allowlist (solo lectura / explicación)

| Tool | Rol |
|------|-----|
| `get_health` | Health checks locales |
| `get_mode` | Modo sesión + LIVE_BLOCKED |
| `list_capabilities` | Features lab |
| `list_venues` | Venues registry |
| `explain_backtest` | Guía + último summary de sesión |
| `search_docs` | Keywords en `docs/*.md` |
| `list_experiments` | Registry sesión |
| `explain_live_policy` | LIVE bloqueado; REAL=PAPER |
| `get_session_summary` | Resumen sesión (F47): mode/venue/equity/posiciones/activity |
| `list_reports` | Reports lab de sesión (F47) |
| `list_strategies` | Catálogo de estrategias (F47) |

## Tools PROHIBIDOS

`submit_order`, `cancel_order`, `set_live`, `flip_live_blocked`, `place_order`
y cualquier mutación de trading — **rechazados** por `ToolRegistry`.

## API

| Método | Ruta | Body / respuesta |
|--------|------|------------------|
| POST | `/api/chat` | `{"message":"..."}` → `{reply, tools_used, mode, live_blocked}` |
| GET | `/api/chat/tools` | allowlist + `safe_mode: true` |

## Providers

- **FakeProvider** (default CI/offline): pattern-match intents ES (salud, modo,
  backtest, scanner, live, ayuda) → llama tools allowlist → responde en español.
- **OptionalEnvProvider**: si `QUANTLAB_LLM_API_KEY` ≠ `DISABLED` (placeholders
  en `.env.example`). **No** usado en tests CI.

## UI

- Panel **Chat IA** (input + historial + badge `safe-mode`)
- Menú Inicio → Chat IA
- Banner sistema: *Asistente research — no envía órdenes*

## Seguridad

- `LIVE_BLOCKED is True` (sin flip)
- Chat no puede `set_live` / enviar órdenes
- Audit JSONL append-only por turno

## Definition of Done

- [x] Módulo `workbench/chat/*`
- [x] Endpoints `/api/chat` + `/api/chat/tools`
- [x] Panel JS + banner + menú
- [x] Tests `tests/unit/workbench/test_chat_*.py`
- [x] Version 0.14.0
- [x] Docs + implementation report + DEC-061..065
- [x] `.env.example` con `QUANTLAB_LLM_*=DISABLED`
- [x] QA: ruff / mypy --strict / pytest workbench / quantlab-health

## Fuera de alcance

Flip LIVE, órdenes live, Electron, LLM HTTP de producción.
