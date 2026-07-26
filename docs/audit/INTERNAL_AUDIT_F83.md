# INTERNAL AUDIT — F83 Minimize / Restore All

**Fecha:** 2026-07-26  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Código tip:** 4bfb18d · **v0.75.0** · F83 Minimize / Restore All  

**Versión:** **0.75.0** · F83 Minimize / Restore All  
**LIVE_BLOCKED:** True  
**Veredicto:** **APROBADO_INTERNO**  
**Certificado externo:** `FASE_83_APPROVED.md` **NO** emitido

## Checklist

| Check | Resultado |
|-------|-----------|
| Versión | **0.75.0** |
| LIVE_BLOCKED | **True** |
| Sin FASE_83_APPROVED | **PASS** |
| DEC-127 | **PASS** |
| phases_summary F19–F83 | **PASS** |
| commands minimize/restore all | **PASS** |
| wm.js minimizeAll/restoreAll + scheduleSave | **PASS** |
| Menú Ventanas | **PASS** |

## Evidencia

1. `GET /api/commands` incluye `action.minimize_all` + `action.restore_all`.  
2. `wm.js` batch min/restore + persist layout.  
3. Palette + menú Inicio cableados.  
4. Suite + smoke F83 · DEC-127 · bump 0.75.0.  

## Resumen

Minimize / Restore All · About≡`__version__` 0.75.0 · `phases_summary F19–F83` · sin flip LIVE.

---

Meta-Auditor INTERNO Zero-Trust · 2026-07-26 · QuantLab F83 · **APROBADO_INTERNO** · **sin** certificado externo · **LIVE_BLOCKED** intacto
