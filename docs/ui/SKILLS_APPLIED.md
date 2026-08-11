# Skills aplicadas — Rediseño UI radical

**Fecha:** 2026-08-11  
**Rama:** `feature/ui-radical-simplification`  
**Worktree:** `../QuantLab-ui-redesign`

## Skills inspeccionadas

| Skill | Ubicación | ¿Aplicada? | Motivo |
|-------|-----------|-----------|--------|
| **Canvas** | cursor-skills/canvas | Fase 2+ | Prototipos visuales (Home, design system) cuando haya artefactos estáticos |
| **Create Rule** | cursor-skills/create-rule | Fase 3+ | Reglas de convención UI en `.cursor/rules` del worktree |
| **Architecture Reviewer** | skills/architecture-reviewer | Fase 2 (IA) | Validar PanelRegistry y capa frontend antes de implementar |
| **Project Memory Manager** | skills/project-memory-manager | Continuo | No duplicar memoria; delta en docs/ui |
| **Continuous Improvement** | skills/continuous-improvement | Fase 13 | Autoevaluación al cerrar fases |

## Skills buscadas y no encontradas

No hay skills dedicadas en el repo/Cursor para:

- UX research formal
- Design systems (tokens)
- WCAG audit automatizado
- Visual regression (Playwright)
- Dashboard simplification

**Acción:** aplicar prácticas profesionales documentadas en `UI_AUDIT.md` y gates de Fase 13; evaluar Playwright en worktree sin dependencias no verificadas hasta Fase 21.

## Resultado esperado por skill

| Skill | Parte afectada | Resultado |
|-------|----------------|-----------|
| Canvas | Home, layouts, design tokens | Mockups interactivos para validar jerarquía antes de codificar |
| Architecture Reviewer | PanelRegistry, APIClient wrapper | Un solo registro de paneles; menú/palette generados |
| Create Rule | Convenciones UI ES | Labels amigables, progressive disclosure obligatorio |

## Restricciones respetadas

- Ninguna skill modifica lógica cuantitativa, estrategias, brokers ni APIs.
- No se instalaron plugins externos en Fase 0–1.
