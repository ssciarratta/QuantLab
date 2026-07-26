# Review Package — FASE 22 Chat IA

**Fecha:** 2026-07-26  
**Versión código:** 0.14.0  
**Tipo:** Review Package **INTERNAL** (Meta-Auditor INTERNO Zero-Trust)  
**Implementación:** commit `5ef9866`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F22.md`  
**Veredicto INTERNAL:** `docs/audit/INTERNAL_AUDIT_F22.md`  
**Implementation report:** `docs/audit/FASE_22_IMPLEMENTATION_REPORT.md`

> **Aclaración:** este paquete **NO** constituye `FASE_22_APPROVED` formal del Meta-Auditor **externo**.  
> Es evidencia + Lista A/B para auditoría interna y para un futuro Review Package externo.

---

## Architecture Review (resumen)

**Opción elegida:** ChatOrchestrator + ToolRegistry allowlist read-only + FakeProvider default (DEC-063..065).  
**Alternativa descartada:** LLM con tool-calling libre / mutaciones de trading / flip LIVE desde el panel.  
**Criterio:** research-safe — explicar salud/modo/lab/docs; **nunca** operar mercado ni cambiar `LIVE_BLOCKED`.

---

## Lista A — Entregables a auditar

| ID | Entregable | Path |
|----|------------|------|
| A1 | ToolRegistry allowlist | `src/quantlab/workbench/chat/tools.py` |
| A2 | FakeProvider + OptionalEnvProvider | `src/quantlab/workbench/chat/providers.py` |
| A3 | ChatAuditLog JSONL | `src/quantlab/workbench/chat/audit.py` |
| A4 | ChatOrchestrator | `src/quantlab/workbench/chat/orchestrator.py` |
| A5 | Handlers `/api/chat*` | `src/quantlab/workbench/api.py` + `server.py` |
| A6 | Panel Chat + banner + menú | `static/js/panes/chat.js`, `shell.js`, `index.html` |
| A7 | LIVE gate intacto | `src/quantlab/execution/live_gate.py` (`LIVE_BLOCKED=True`) |
| A8 | Spec DoD F22 | `docs/FASE_22_CHAT_IA.md` |
| A9 | DEC-063..065 | `learning/decisiones.txt` |
| A10 | Suite unit chat | `tests/unit/workbench/test_chat_*.py` |
| A11 | Implementation report | `docs/audit/FASE_22_IMPLEMENTATION_REPORT.md` |
| A12 | Version 0.14.0 + env placeholders | `pyproject.toml`, `.env.example` |

---

## Lista B — Evidencia QA

```
uv run mypy --strict src/quantlab     → Success (148 files)
uv run ruff check src/quantlab        → All checks passed
uv run pytest -q                      → 463 passed
uv run pytest tests/unit/workbench -q → 40 passed (17 chat)
uv run quantlab-health                → ok=true, live_blocked=true,
                                         operating_mode=tester, v0.14.0,
                                         venues=['a3','binance','paper']
```

Probes adicionales:

- `LIVE_BLOCKED is True`
- `build_default_provider()` → `FakeProvider`
- Illegal tools → `ValidationError` (`submit_order`, `set_live`, `place_order`, …)
- POST `/api/chat` con intent live → solo tools allowlist + `explain_live_policy`
- POST `/api/mode` `live` → 400
- GET `/api/chat/tools` → `safe_mode: true`, `mutations_allowed: false`

---

## Invariantes

- LIVE order routing: **BLOQUEADO**
- Workbench bind default: **127.0.0.1**
- Chat tools: **allowlist read-only**
- FakeProvider: **default CI**
- Chat mutations / flip LIVE: **imposible**
- Flip `LIVE_BLOCKED`: **NO ejecutado**
- Sin certificado externo hasta APROBADO Meta-Auditor externo

---

## Pedido al Meta-Auditor externo (futuro)

1. Revisar Lista A+B + `INTERNAL_AUDIT_F22.md` + arco `INTERNAL_AUDIT_F19_F22_ARC.md`.  
2. Emitir **APROBADO** / observaciones.  
3. Solo con APROBADO → generar `docs/audit/FASE_22_APPROVED.md` (y equivalentes F19–F21 si aplica).
