# QuantLab Project Memory

Actualizado: 2026-07-26 · tip funcional F93 · versión 0.85.0.

- TESTER/PAPER operativos; REAL es alias de PAPER; LIVE routing sigue bloqueado.
- `LIVE_BLOCKED=True`. F93 agrega el pane Venues / Broker Registry read-only
  (`/api/venues` enriquecido con contrato plugins v1; sin mutaciones).
- F17–F18 con certificación externa; F19–F92 aprobadas INTERNAL (noche
  F19–F92); F93 implementada, auditoría INTERNAL en curso.
- F92 congeló el arco F79–F91 en `docs/audit/MILESTONE_V080_ARC_FREEZE.md`
  y sincronizó CHANGELOG (0.81.0/0.82.0/0.83.0/0.84.0).
- Loop ops paper vigente: panel Reconciliación (F90) → CLI rebuild offline
  (F88) → rehydrate con confirm (F91) → reconectar broker.
- Portabilidad Windows verificada (sqlite closing, guard i18n, fsync `rb+`,
  `/tmp` portable, env worker sandbox con SYSTEMROOT).
- DEC vigente: DEC-137.
- Auditoría noche vigente: `INTERNAL_AUDIT_F19_F92_NIGHT.md` (F93 pendiente).
- No crear `FASE_93_APPROVED.md`; requiere Meta-Auditor externo.
