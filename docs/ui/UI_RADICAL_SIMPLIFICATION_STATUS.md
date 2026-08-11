# Estado — Simplificación radical UI

**Actualizado:** 2026-08-11  
**ESTADO:** ✅ **COMPLETO** (Fases 0–13 en worktree)

| Campo | Valor |
|-------|-------|
| **FASE** | 13 — Tests smoke |
| **RAMA** | `feature/ui-radical-simplification` |
| **WORKTREE** | `QuantLab-ui-redesign` |
| **REPO PRINCIPAL** | Intacto (UI solo en worktree) |

## Entregables por fase

| Fase | Entregable | Estado |
|------|------------|--------|
| 0–1 | Auditoría + worktree | ✓ |
| 2 | IA 7 grupos | ✓ `NAVIGATION_IA.md`, `panel_registry.js` |
| 3 | Design system | ✓ `design_tokens.css`, `ql_ui.js`, `DESIGN_SYSTEM.md` |
| 4 | Layouts por tarea | ✓ `layout_presets.js`, menú v6 |
| 5 | Home + boot 1 ventana | ✓ `home.js`, `shell.js` |
| 6 | Prototipos clave | ✓ Scanner/Sim/SLT/Monitor con headers + flujo |
| 7–11 | Rollout universal | ✓ `QLUi.enhancePaneRoot` en `wm.open` (todos los paneles) |
| 12 | Sync backend main | ✓ `src/quantlab/` + static UI preservado |
| 13 | Tests | ✓ `scripts/smoke_ui_redesign.sh`, `PHASE_13_TEST_REPORT.md` |

## Archivos clave

- `static/js/panel_registry.js` — 41 paneles, 7 grupos, NEXT_FLOW
- `static/js/ql_ui.js` — headers, flow rail, enhancePaneRoot
- `static/js/panes/home.js`, `monitor.js`
- `static/js/shell.js` — boot Inicio, wm.open patch, openMonitor
- `static/js/ql_menu.js` — menú desde registry

## Métricas

| Métrica | Valor |
|---------|-------|
| Paneles en registry | 41 |
| Con header QLUi automático | 40 (todos excepto home) |
| Con flow rail | 7 (scanner, sim, bt, mc, slt, monitor, sim_registry) |
| Backend tocado para UI | Solo sync Fase 12 (parity main) |

## Cómo probar

```bash
cd QuantLab-ui-redesign
bash scripts/smoke_ui_redesign.sh
uv run quantlab-workbench
# http://127.0.0.1:8765
```

## Bloqueos

- **Push/merge a main:** pendiente autorización explícita del usuario.
