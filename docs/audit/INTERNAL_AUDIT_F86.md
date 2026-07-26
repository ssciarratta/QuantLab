# INTERNAL AUDIT — F86 Maximize / Restore Window

**Veredicto:** `# APROBADO_INTERNO`  
**Fecha:** 2026-07-26  
**Código tip:** b82485c · **v0.78.0** · F86 Maximize / Restore Window  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Versión:** **0.78.0** · F86 Maximize / Restore Window  
**LIVE_BLOCKED:** True  

## Checklist

| Check | Resultado |
|-------|-----------|
| Versión | **0.78.0** |
| LIVE_BLOCKED | **True** |
| Sin FASE_86_APPROVED | **PASS** |
| DEC-130 | **PASS** |
| phases_summary F19–F86 | **PASS** |
| maximize/restoreFromMaximize + preMax + scheduleSave | **PASS** |
| Titlebar btn + dblclick toggle | **PASS** |
| Commands maximize/restore | **PASS** |
| Menú Ventanas | **PASS** |
| Persist/restore `maximized` | **PASS** |
| Suite + smoke F86 | **PASS** |

## Evidencia

1. `wm.js` maximize/restoreFromMaximize/toggleMaximize + store `preMax`; titlebar □/❐ + dblclick.  
2. Commands `action.maximize_window` / `action.restore_from_maximize` + menú Inicio.  
3. Persist layout vía `scheduleSave()`; `layout.py` valida `maximized: bool`; `mergeOpts`/`open` restauran.  
4. Suite + smoke F86 · DEC-130 · bump 0.78.0.  
5. Sin certificado externo · LIVE intacto.

## Resumen

Maximize / Restore Window · About≡`__version__` 0.78.0 · `phases_summary F19–F86` · sin flip LIVE.

---

Meta-Auditor INTERNO Zero-Trust · 2026-07-26 · QuantLab F86 · **APROBADO_INTERNO** · **sin** certificado externo · **LIVE_BLOCKED** intacto
