# QuantLab Project Memory

Actualizado: 2026-07-26 · tip funcional F90 · versión 0.82.0.

- TESTER/PAPER operativos; REAL es alias de PAPER; LIVE routing sigue bloqueado.
- `LIVE_BLOCKED=True` y ningún cambio de F90 autoriza un flip.
- F17–F18 tienen certificación externa; F19–F89 aprobadas INTERNAL; F90
  implementada con auditoría INTERNAL en curso.
- F90 agrega el panel `Reconciliación` (workbench) **read-only** sobre
  `GET /api/paper/reconciliation` (estado journal/book de F88):
  - badge ok/status, record_count, checkpoint, issues y `rebuild_via`.
  - la UI no expone mutaciones HTTP; el rebuild sigue siendo CLI offline.
- Portabilidad Windows verificada en PC: sqlite closing en ExperimentRegistry,
  guard i18n por Path, fsync `rb+`, `/tmp` → `tempfile.gettempdir()`,
  env worker sandbox con SYSTEMROOT. Suite verde en Windows y Linux.
- DEC vigente: DEC-134.
- Auditoría noche vigente: `INTERNAL_AUDIT_F19_F89_NIGHT.md` (F90 pendiente).
- No crear `FASE_90_APPROVED.md`; requiere Meta-Auditor externo.
