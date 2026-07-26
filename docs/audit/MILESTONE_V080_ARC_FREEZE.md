# Milestone Freeze — Workbench F79–F91 + F92 (arco v0.71–v0.84)

**Fecha freeze docs:** 2026-07-26  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Milestone tip:** **v0.84.0** (F92 Milestone Freeze Docs)  
**Último producto previo:** **v0.83.0** (F91 Paper Session Rehydrate · impl `5c34995`)  
**LIVE:** **BLOQUEADO** (`LIVE_BLOCKED=True`) · flip **NO**  
**Certificados externos F19–F92:** **NO emitidos** (reserva Meta-Auditor)

> Freeze documental del arco F79–F91 (producto) + F92 (milestone sync).  
> Arcos anteriores: `MILESTONE_V070_FREEZE.md` (F19–F78).  
> No habilita LIVE. Spec F92: `docs/FASE_92_MILESTONE_V080_ARC.md`.

---

## Inventario F79–F91 / F92

| Fase | Tema | Ver | Impl SHA | INTERNAL |
|------|------|-----|----------|----------|
| **79** | Watchlist Import/Export JSON | 0.71.0 | `7245ca4` | APROBADO_INTERNO |
| **80** | Custom Preset Save | 0.72.0 | `67fd498` | APROBADO_INTERNO |
| **81** | Custom Preset Delete | 0.73.0 | `2975729` | APROBADO_INTERNO |
| **82** | Window Snap to Edges | 0.74.0 | `bb57bed` | APROBADO_INTERNO |
| **83** | Minimize / Restore All | 0.75.0 | `4bfb18d` | APROBADO_INTERNO |
| **84** | Cascade / Tile Windows | 0.76.0 | `e82ebef` | APROBADO_INTERNO |
| **85** | Bring to Front / Send to Back | 0.77.0 | `c1b6d43` | APROBADO_INTERNO |
| **86** | Maximize / Restore Window | 0.78.0 | `b82485c` | APROBADO_INTERNO |
| **87** | Broker Plugin Contract v1 | 0.79.0 | `e0ff1d9` | APROBADO_INTERNO |
| **88** | Paper Journal authoritative + reconciliation | 0.80.0 | `54161f5` | APROBADO_INTERNO |
| **89** | A3 MD Read-only Certification | 0.81.0 | `a94b448` | APROBADO_INTERNO |
| **90** | Paper Reconciliation Status Panel | 0.82.0 | `9971366` | APROBADO_INTERNO |
| **91** | Paper Session Rehydrate post-rebuild | 0.83.0 | `5c34995` | APROBADO_INTERNO |
| **92** | Milestone Freeze Docs + CHANGELOG (arco) | 0.84.0 | — | este freeze |

## Invariantes del arco (no negociar)

1. `LIVE_BLOCKED is True` — ninguna fase del arco habilita routing LIVE.
2. REAL = alias de PAPER; fills siempre simulados; venue submit prohibido.
3. `journal.jsonl` autoritativo append-only (F88); book v2 proyección con
   checkpoint SHA-256; drift/corrupción bloquea submits.
4. Rebuild **solo** CLI offline con backup; rehydrate (F91) relee disco sin
   auto-recovery; UI de reconciliación (F90) con confirm y sin rebuild HTTP.
5. Plugins externos (F87) siempre detrás de `ReadOnlyBrokerPort`; metadata
   versionada; sin submit/cancel.
6. Certificación A3 MD (F89): fake lane PASS con cero writes; sandbox real
   `SKIPPED_NOT_REQUESTED` — no se afirma certificación real.
7. Sin `FASE_79`…`FASE_92_APPROVED.md` desde INTERNAL.

## Cómo operar el tip (v0.84.0)

```bash
uv run quantlab-workbench          # SPA loopback 127.0.0.1
uv run quantlab-health             # health JSON (live_blocked=true)
uv run python scripts/internal_audit_smoke.py
uv run python scripts/reconcile_paper_session.py --session PATH --check
uv run python scripts/a3_md_certify.py --lane fake
```

Loop de reconciliación paper: panel `Reconciliación` → si `rebuild_required`,
correr CLI `--rebuild` (crea backup) → botón «Releer sesión (post-rebuild)»
→ reconectar broker.

## Límites

- LIVE bloqueado; flip requiere checklist + Meta-Auditor + dueño + commit dedicado.
- Sin auth WAN (loopback default; non-loopback exige flag explícito).
- Plataformas verificadas: Windows (PC) + Linux (cloud/CI).
