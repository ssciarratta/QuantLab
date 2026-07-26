# QuantLab Project Memory

Actualizado: 2026-07-26 · tip funcional F94 · versión 0.86.0.

- TESTER/PAPER operativos; REAL es alias de PAPER; LIVE routing sigue bloqueado.
- `LIVE_BLOCKED=True`. F94 agrega el pane API Explorer read-only (navega
  `/api/openapi.json`; sin rutas nuevas ni mutaciones). F93 agregó el pane
  Venues / Broker Registry read-only (`/api/venues` enriquecido con contrato
  plugins v1).
- F17–F18 con certificación externa; F19–F93 aprobadas INTERNAL (noche
  F19–F93); F94 aprobada INTERNAL (noche F19–F94).
- F92 congeló el arco F79–F91 en `docs/audit/MILESTONE_V080_ARC_FREEZE.md`
  y sincronizó CHANGELOG (0.81.0/0.82.0/0.83.0/0.84.0).
- Loop ops paper vigente: panel Reconciliación (F90) → CLI rebuild offline
  (F88) → rehydrate con confirm (F91) → reconectar broker.
- Portabilidad Windows verificada (sqlite closing, guard i18n, fsync `rb+`,
  `/tmp` portable, env worker sandbox con SYSTEMROOT).
- DEC vigente: DEC-138.
- Auditoría noche vigente: `INTERNAL_AUDIT_F19_F94_NIGHT.md`.
- No crear `FASE_94_APPROVED.md`; requiere Meta-Auditor externo.
