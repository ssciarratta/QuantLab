# QuantLab Project Memory

Actualizado: 2026-07-26 · tip funcional F89 · versión 0.81.0.

- TESTER/PAPER operativos; REAL es alias de PAPER; LIVE routing sigue bloqueado.
- `LIVE_BLOCKED=True` y ningún cambio de F89 autoriza un flip.
- F17–F18 tienen certificación externa; F19–F89 están aprobadas INTERNAL.
- F89 certifica el contrato A3 MD read-only en lanes independientes:
  - fake-contract obligatoria CI/offline, PASS local y cero writes.
  - sandbox-env sólo opt-in + simulation + pyRofex strict, sin fallback.
  - `SKIPPED_NOT_REQUESTED` no es PASS.
  - reporte sin secretos, account IDs ni payloads raw.
- Sandbox real no fue ejecutado por ausencia de opt-in/credenciales; no hay
  afirmación de certificación real.
- DEC vigente: DEC-133.
- Auditoría noche vigente: `INTERNAL_AUDIT_F19_F89_NIGHT.md`.
- No crear `FASE_89_APPROVED.md`; requiere Meta-Auditor externo.
