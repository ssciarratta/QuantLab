# INTERNAL AUDIT — F85 Bring to Front / Send to Back

**Veredicto:** `# APROBADO_INTERNO`  
**Fecha:** 2026-07-26  
**Código tip:** c1b6d43 · **v0.77.0** · F85 Bring to Front / Send to Back  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Versión:** **0.77.0** · F85 Bring to Front / Send to Back  
**LIVE_BLOCKED:** True  

## Checklist

| Check | Resultado |
|-------|-----------|
| Versión | **0.77.0** |
| LIVE_BLOCKED | **True** |
| Sin FASE_85_APPROVED | **PASS** |
| DEC-129 | **PASS** |
| phases_summary F19–F85 | **PASS** |
| bringToFront/sendToBack + scheduleSave | **PASS** |
| Context menu titlebar + dblclick | **PASS** |
| Commands bring/send | **PASS** |
| Menú Ventanas | **PASS** |
| Persist/restore `z` | **PASS** |
| Suite + smoke F85 | **PASS** |

## Evidencia

1. `wm.js` bringToFront/sendToBack + context menu; `mergeOpts`/`open` restauran `z`.  
2. Commands `action.bring_to_front` / `action.send_to_back` + menú Inicio.  
3. Persist layout vía `scheduleSave()` post z-order change.  
4. Suite + smoke F85 · DEC-129 · bump 0.77.0.  
5. Sin certificado externo · LIVE intacto.

## Resumen

Bring to Front / Send to Back · About≡`__version__` 0.77.0 · `phases_summary F19–F85` · sin flip LIVE.

---

Meta-Auditor INTERNO Zero-Trust · 2026-07-26 · QuantLab F85 · **APROBADO_INTERNO** · **sin** certificado externo · **LIVE_BLOCKED** intacto
