# QuantLab Project Memory

Actualizado: 2026-07-26 · tip funcional F92 · versión 0.84.0.

- TESTER/PAPER operativos; REAL es alias de PAPER; LIVE routing sigue bloqueado.
- `LIVE_BLOCKED=True`; F92 es freeze documental, sin cambios de runtime.
- F17–F18 con certificación externa; F19–F91 aprobadas INTERNAL; F92
  implementada con auditoría INTERNAL en curso.
- F92 congela el arco F79–F91 en `docs/audit/MILESTONE_V080_ARC_FREEZE.md`
  y sincroniza CHANGELOG (0.81.0/0.82.0/0.83.0/0.84.0 faltaban).
- Loop ops paper vigente: panel Reconciliación (F90) → CLI rebuild offline
  (F88) → rehydrate con confirm (F91) → reconectar broker.
- Portabilidad Windows verificada (sqlite closing, guard i18n, fsync `rb+`,
  `/tmp` portable, env worker sandbox con SYSTEMROOT).
- DEC vigente: DEC-136.
- Auditoría noche vigente: `INTERNAL_AUDIT_F19_F91_NIGHT.md` (F92 pendiente).
- No crear `FASE_92_APPROVED.md`; requiere Meta-Auditor externo.
