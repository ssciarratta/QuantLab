# FASE 47 — Implementation Report (Chat Context Awareness)

**Fecha:** 2026-07-26  
**Versión:** 0.39.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F46 Multi-Session Switcher  
**Impl SHA:** _(tip post-commit)_  
**Alcance:** chat tools context read-only — **sin flip LIVE** · **sin trading tools**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| T1 | Allowlist + handlers | `workbench/chat/tools.py` |
| T2 | FakeProvider intents ES | `workbench/chat/providers.py` |
| T3 | Suite F47 | `tests/unit/workbench/test_chat_context_f47.py` |
| T4 | Smoke F47 | `scripts/internal_audit_smoke.py` |
| D1 | Spec + DEC-091 + bump | `docs/FASE_47_CHAT_CONTEXT.md` · `0.39.0` |
| D2 | Implementation report | este doc |
| D3 | Bundle default to-phase 47 | `scripts/build_internal_review_bundle.py` |

## Invariantes

- `LIVE_BLOCKED is True`
- Sin `FASE_47_APPROVED.md`
- Sin flip LIVE / place_order venue
- Chat sin trading tools (`submit_order` / `set_live` / … rechazados)
- DEC-091
- `phases_summary == "F19–F47 INTERNAL"`

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff format src/quantlab tests/unit/workbench
uv run ruff check src/quantlab tests/unit/workbench
uv run mypy --strict src/quantlab
uv run pytest tests/unit/workbench/test_chat_context_f47.py -q
uv run pytest tests/unit/workbench -q
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- Trading tools en chat
- Auth WAN / Electron
- Certificado externo `FASE_47_APPROVED.md`
