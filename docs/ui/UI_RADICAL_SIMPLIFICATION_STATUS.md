# Estado — Simplificación radical UI

**Actualizado:** 2026-08-11 (v2 friendly UI)  
**ESTADO:** 🔄 En curso — tema amigable + Monte Carlo en Inicio

| Campo | Valor |
|-------|-------|
| **FASE** | 14 — Friendly UI v2 |
| **RAMA** | `feature/ui-radical-simplification` |
| **WORKTREE** | `QuantLab-ui-redesign` |

## Última implementación (2026-08-11)

- **`friendly_ui.css`** — paleta cálida (coral/mint), bordes redondeados, botones pill, paneles con cajas suaves
- **Monte Carlo** en Inicio (grupo «Probar y estresar»), barra rápida y flujo Simulador → Backtest → MC
- **Home** agrupado por tarea con iconos en tarjetas
- **ql_ui.js** — badges en español claro, flow rail con paso activo
- **Launcher Windows** — smoke nativo `.bat` (sin Git Bash)

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
| 13 | Tests | ✓ `scripts/smoke_ui_redesign.bat` (Windows) / `.sh` (Git Bash), `PHASE_13_TEST_REPORT.md` |

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

**Windows (recomendado):** doble clic en `cambio entorno prueba.bat` (smoke `.bat` + arranque).  
**Git Bash / Linux:** `bash scripts/smoke_ui_redesign.sh`

## Bloqueos

- **Push/merge a main:** pendiente autorización explícita del usuario.
