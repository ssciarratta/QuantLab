# FASE 22 — Implementation Report (Chat IA safe-by-default)

**Fecha:** 2026-07-26  
**Versión:** 0.14.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F21 Lab Panels v0.13.0  
**Alcance:** chat research-safe — **sin operar mercado**, **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| C1 | ToolRegistry allowlist | `workbench/chat/tools.py` |
| C2 | FakeProvider + OptionalEnvProvider | `workbench/chat/providers.py` |
| C3 | ChatAuditLog JSONL | `workbench/chat/audit.py` |
| C4 | ChatOrchestrator | `workbench/chat/orchestrator.py` |
| C5 | Handlers `/api/chat*` | `workbench/api.py` + `server.py` |
| C6 | Panel Chat + banner | `static/js/panes/chat.js`, `shell.js`, `index.html` |
| C7 | Suite unit | `tests/unit/workbench/test_chat_*.py` |
| C8 | Spec DoD | `docs/FASE_22_CHAT_IA.md` |
| C9 | Bump | `pyproject.toml` + `__version__` → 0.14.0 |
| C10 | DEC-062..065 | `learning/decisiones.txt` |
| C11 | Env placeholders | `.env.example` `QUANTLAB_LLM_*=DISABLED` |

## Invariantes

- `LIVE_BLOCKED is True`
- Allowlist-only tools; ilegales → `ValidationError`
- Chat no puede set_live / place_order / submit_order
- FakeProvider default en CI
- Audit append-only por turno

## QA

```text
uv sync --extra dev
uv run ruff check src/quantlab tests/unit/workbench
uv run mypy --strict src/quantlab
uv run pytest tests/unit/workbench -q
uv run quantlab-health
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- Órdenes live / credenciales exchange
- LLM HTTP de producción (solo placeholder env)
