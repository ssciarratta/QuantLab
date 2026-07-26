# Milestone Freeze — Arco Ops Visibility v0.90 (F93–F97)

**Fecha:** 2026-07-26  
**Versión tip:** 0.90.0 · **Fase:** F98  
**Branch:** `cursor/modo-real-workbench-aafd`  
**LIVE_BLOCKED:** True  
**Estado:** freeze documental · `APROBADO_INTERNO` pendiente de esta fase

---

## 1. Alcance congelado

Inventario del arco de **visibilidad operativa / soporte** (sin ejecución LIVE):

| Fase | Tema | Ver | Notas |
|------|------|-----|-------|
| F93 | Venues / Broker Registry Panel | 0.85.0 | `/api/venues` enriquecido + pane read-only |
| F94 | API Explorer Panel | 0.86.0 | navega `/api/openapi.json` |
| F95 | Diagnostics Snapshot | 0.87.0 | `GET /api/diagnostics` |
| F96 | Diagnostics Download | 0.88.0 | `GET /api/diagnostics.json` |
| F97 | Support Bundle ZIP | 0.89.0 | `GET /api/support-bundle.zip` |

Congelado junto con el tip F98 (esta fase documental) en **0.90.0**.

## 2. Invariantes Zero-Trust (no negociar)

1. `LIVE_BLOCKED=True` — flip **NO** ejecutado
2. REAL = alias de PAPER (nunca LIVE)
3. Paneles/endpoints del arco: **solo lectura** (sin submit/cancel venue)
4. Support bundle **excluye** journal/book y credenciales
5. Plugins externos siempre detrás de `ReadOnlyBrokerPort`
6. Sin emitir `FASE_93`…`FASE_98_APPROVED.md` desde INTERNAL

## 3. Loop operativo paper (previo, intacto)

Panel Reconciliación (F90) → CLI rebuild offline (F88) → rehydrate (F91) →
reconectar broker. El arco F93–F97 **no** altera ese loop; solo aporta
visibilidad/soporte.

## 4. Operación / evidencia

- Smoke tip: version starts with `0.90` + check F98
- Bundle INTERNAL default: F19–F98
- Noche: `INTERNAL_AUDIT_F19_F97_NIGHT.md` (extendida a F98 en docs tip)

## 5. Fuera de freeze

- Flip LIVE / order routing venue
- Certificados externos `FASE_*_APPROVED.md`
- Nuevas capacidades de ejecución en plugins
