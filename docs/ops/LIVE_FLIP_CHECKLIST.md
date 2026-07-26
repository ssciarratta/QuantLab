# LIVE Flip Checklist — QuantLab

**Estado:** FLIP **NO** EJECUTADO  
**Fecha:** 2026-07-26  
**`LIVE_BLOCKED`:** debe permanecer `True` hasta Meta-Auditor + dueño.

## Prerrequisitos (todos obligatorios)

- [ ] F0–F18 certificados vigentes
- [ ] F19 Operating Modes APROBADO (Meta-Auditor)
- [ ] `docs/A3_PRODUCTION_READINESS.md` ítems críticos en verde
- [ ] Risk limits + kill switch probados en PAPER
- [ ] Allowlists de símbolos/cuentas revisadas
- [ ] Credenciales solo vía `.env` (remote git limpio)
- [ ] Red-team tests: cada gate individual rechaza órdenes
- [ ] DEC-060 registrada y Review Package LIVE dedicado
- [ ] APROBADO explícito Meta-Auditor + Director
- [ ] Commit dedicado que cambie `LIVE_BLOCKED` (único cambio de esa constante)

## Prohibido

- Flip por chat IA / workbench / script opaco
- Flip “temporal” en CI
- Órdenes LIVE sin ModeGuard + env confirm `I_UNDERSTAND_THIS_SENDS_REAL_ORDERS`

## Post-flip (si algún día ocurre)

1. Health debe reportar `live_blocked=false` y `operating_mode=live` solo con config explícita.
2. Observabilidad: contadores `live_gate.*` y journal live.
3. Runbook de kill switch publicado.
