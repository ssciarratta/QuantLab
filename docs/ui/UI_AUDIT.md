# Auditoría UX/UI — QuantLab Workbench

**Fecha:** 2026-08-11  
**Alcance:** Frontend estático `src/quantlab/workbench/static/`  
**Método:** Revisión de código (shell, menú, wm, 39 paneles). Sin modificar UI.  
**Worktree:** `QuantLab-ui-redesign` @ `feature/ui-radical-simplification`

---

## 1. Resumen ejecutivo

La interfaz actual es **funcionalmente completa** pero **cognitivamente sobrecargada**:

- **39 ventanas MDI** + modal About + ventanas dinámicas `sim_memo_*`.
- Organización por **módulos técnicos** (Lab / Sesión paper / Avanzado / Sistema), no por tareas.
- **Duplicación fuerte** en paper (3–4 paneles), testnet (4 puntos de unlock), resultados (JSON vs informes).
- **Bilingüismo** ES/EN mezclado en labels, botones y estados WM.
- **Densidad extrema** en Scanner (~2156 LOC), Simulador (~3084), Guided Lab, Corrida en vivo.
- **Window manager** (`wm.js`) ya soporta mover/redimensionar/minimizar/persistir — base sólida para Fase 4.
- **Boot agresivo:** abre health + market + blotter sin pedir tarea al usuario.

**Veredicto:** simplificación radical viable **sin quitar funciones** — reorganizar, unificar copy, PanelRegistry, Home, progressive disclosure.

---

## 2. Problemas priorizados (P0–P2)

### P0 — Confusión inmediata

| # | Problema | Evidencia | Impacto |
|---|----------|-----------|---------|
| P0.1 | Tres formas de "correr estrategia" | paper_session, strategy_live_test, blotter submit | Usuario no sabe cuál usar |
| P0.2 | "Corrida finalizada" / estados contradictorios | strategy_live_test closure vs live (fix en rama paralela) | Desconfianza en el sistema |
| P0.3 | Boot 3 ventanas técnicas | shell.js auto-open health/market/blotter | Sobrecarga día 1 |
| P0.4 | LIVE_BLOCKED repetido | Banners en N paneles | Ruido visual |

### P1 — Navegación y nombres

| # | Problema | Evidencia |
|---|----------|-----------|
| P1.1 | Labels EN (`Journal`, `Metrics`, `Settings`) | i18n incompleto |
| P1.2 | IDs técnicos visibles (`scan_id`, `n_bars`, F65) | Formularios research |
| P1.3 | Menú 4 secciones × 10+ ítems | ql_menu.js |
| P1.4 | Guided Lab monolito | Duplica medio producto |

### P2 — Densidad y accesibilidad

| # | Problema | Evidencia |
|---|----------|-----------|
| P2.1 | Toolbars 15+ controles | scanner.js |
| P2.2 | JSON crudo como UI | metrics, experiments |
| P2.3 | Atajos Ctrl+1–9 desalineados | Solo subset sesión |
| P2.4 | Contraste / foco variable | workbench.css extenso sin tokens únicos |

---

## 3. Fortalezas a conservar

1. **MDI completo** — arrastrar, redimensionar, layouts, persistencia (`wm.js`).
2. **Handoffs** — `nav.js` + prefill entre Scanner → Sim → MC → Corrida en vivo.
3. **Menú personalizable** — ql_menu v5 (base para PanelRegistry).
4. **Command palette** — `/api/commands`.
5. **Seguridad visible** — LIVE_BLOCKED (compactar, no eliminar).
6. **Vanilla JS** — sin build step; alineado con stack del proyecto.

---

## 4. Arquitectura de información propuesta

Ver `USER_TASK_MAP.md`. Siete grupos:

1. Inicio  
2. Investigar  
3. Probar  
4. Ejecutar en prueba  
5. Monitorear  
6. Resultados  
7. Sistema  

---

## 5. Componentes comunes a crear (Fase 3)

- `SystemStatus` / `SafetyBadge`
- `PanelHeader` (título, ayuda, cerrar/min/max)
- `PrimaryAction`
- `AdvancedSettings` (colapsado)
- `MetricCard`, `StatusBadge`, `EmptyState`, `ErrorState`, `NextStep`

---

## 6. Panel Registry (Fase 20 preview)

Fuente única en JS:

```text
src/quantlab/workbench/static/js/panel_registry.js
```

Campos: `id`, `friendly_name`, `description`, `category`, `component`, `default_size`, `singleton`, `feature_flag`.

Generar menú, palette y layouts desde ahí — eliminar listas duplicadas en shell + ql_menu.

---

## 7. Capa frontend (Fase 19)

- `api.js` ya centraliza — extender con adaptadores ViewModel por panel.
- Prohibido nuevo `fetch` disperso en paneles migrados.
- Feature flags para Home y PanelRegistry.

---

## 8. Accesibilidad — checklist mínimo

- [ ] Foco visible en todos los controles WM  
- [ ] Tab order lógico por panel  
- [ ] Labels en `<label>` o `aria-label`  
- [ ] Estados no solo por color (icono + texto)  
- [ ] Contraste WCAG AA en tema oscuro  
- [ ] `prefers-reduced-motion`  
- [ ] Zoom 125–150% sin rotura  

---

## 9. Rendimiento — observaciones

- Polling en access_log (5s), Corrida en vivo (1.2s) — pausar si ventana minimizada/cerrada (Fase 18).
- Paneles enormes (simulator) — lazy render al first open.
- workbench.css ~4200 líneas — tokenizar y deduplicar en Fase 3.

---

## 10. Compatibilidad con desarrollo paralelo

| Área | Riesgo | Mitigación |
|------|--------|------------|
| Backend / execution | Alto | Solo UI en worktree; adaptadores API |
| strategy_live_test | Medio | Rebase frecuente; merge UI-only |
| ql_menu / shell | Alto | PanelRegistry reemplaza gradualmente |

**No modificar** en este epic: `execution_api.py`, estrategias, brokers, tests de dominio.

---

## 11. Prototipos prioritarios (Fase 6)

1. **Home** (nuevo)  
2. **Buscar oportunidades** (Scanner simplificado)  
3. **Ejecutar en prueba** (Corrida en vivo)  
4. **Monitorear** (vista unificada operación activa)

---

## 12. Referencias

- Inventario detallado: `PANEL_INVENTORY.md`  
- Mapa tareas: `USER_TASK_MAP.md`  
- Terminología: `UI_TERMINOLOGY.md`  
- Progreso: `UI_RADICAL_SIMPLIFICATION_STATUS.md`
