# FASE 47 — Review Package INTERNAL (Chat Context Awareness)

**Fecha:** 2026-07-26  
**Versión código (impl F47):** 0.39.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Impl SHA:** `afdf067`  
**LIVE:** BLOQUEADO  
**Certificado externo:** **NO** (`FASE_47_APPROVED.md` no emitido)

---

## Resumen ejecutivo

Chat context awareness: allowlist read-only ampliada con resumen de sesión, reports y catálogo de estrategias; FakeProvider intents en español; trading tools siguen rechazados. DEC-091.

**Opción elegida:** extender `ToolRegistry` + FakeProvider pattern-match; sin mutaciones; sin LLM HTTP; sin LIVE.

## Entregables

| ID | Entrega | Path |
|----|---------|------|
| A1 | Allowlist + handlers | `workbench/chat/tools.py` |
| A2 | FakeProvider ES | `workbench/chat/providers.py` |
| A3 | Spec | `docs/FASE_47_CHAT_CONTEXT.md` |
| A4 | Implementation report | `docs/audit/FASE_47_IMPLEMENTATION_REPORT.md` |
| A5 | DEC-091 | `learning/decisiones.txt` |
| A6 | Version 0.39.0 | `pyproject.toml` |
| A7 | Suite F47 | `tests/unit/workbench/test_chat_context_f47.py` |
| A8 | Smoke F47 | `scripts/internal_audit_smoke.py` |
| A9 | Bundle to-phase 47 | `scripts/build_internal_review_bundle.py` |

## Evidencia QA

```
uv run mypy --strict src/quantlab     → Success: 175 files
uv run ruff check                     → All checks passed
uv run pytest -q                      → 839 passed
uv run quantlab-health                → ok=true, live_blocked=true, version=0.39.0
uv run python scripts/internal_audit_smoke.py → 33/33 PASS
```

## Smoke tools (síntesis)

| # | Tool / intent | Esperado |
|---|---------------|----------|
| 1 | get_session_summary | mode · equity · positions · activity |
| 2 | list_reports | kind=reports · live_blocked |
| 3 | list_strategies | catalog ids |
| 4 | «¿cómo estoy?» | get_session_summary |
| 5 | submit_order / set_live | ValidationError rechazada |

## Fuera de alcance

LIVE · trading tools en chat · auth WAN · Electron · `FASE_47_APPROVED.md`

## Veredicto INTERNAL propuesto

**APROBADO_INTERNO** — ver `INTERNAL_AUDIT_F47.md`.
