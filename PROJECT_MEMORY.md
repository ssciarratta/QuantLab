# QuantLab Project Memory

Actualizado: 2026-07-26 · tip funcional F91 · versión 0.83.0.

- TESTER/PAPER operativos; REAL es alias de PAPER; LIVE routing sigue bloqueado.
- `LIVE_BLOCKED=True` y ningún cambio de F91 autoriza un flip.
- F17–F18 con certificación externa; F19–F91 aprobadas INTERNAL.
- F91 cierra el loop ops de F88/F90: `POST /api/paper/reconciliation/rehydrate`
  hace teardown del runtime y relee journal/book desde disco (reusa
  `switch_session`). Sin auto-recovery; journal nunca mutado; broker queda
  desconectado y la reconexión es explícita. Botón con confirm en el panel
  Reconciliación; evento `rehydrate` en el activity allowlist.
- Portabilidad Windows verificada en PC (sqlite closing, guard i18n por Path,
  fsync `rb+`, `/tmp` portable, env worker sandbox con SYSTEMROOT).
- DEC vigente: DEC-135.
- Auditoría noche vigente: `INTERNAL_AUDIT_F19_F91_NIGHT.md`.
- No crear `FASE_91_APPROVED.md`; requiere Meta-Auditor externo.
