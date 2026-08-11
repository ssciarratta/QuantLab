# Design system ligero — Fase 3

**Sin build step** · Vanilla JS + CSS tokens

## Archivos

| Archivo | Rol |
|---------|-----|
| `static/css/design_tokens.css` | Espaciado, radios, colores semánticos |
| `static/js/ql_ui.js` | Componentes DOM reutilizables |
| `static/css/workbench.css` | Estilos Home + banner compacto |

## Componentes (`QLUi`)

| API | Uso |
|-----|-----|
| `panelHeader({ title, subtitle, actions[] })` | Cabecera de panel unificada |
| `safetyBadge({ mode, liveBlocked, venue })` | Línea PAPER · DATOS · BLOQUEADO |
| `primaryAction({ label, variant, onClick })` | Botón CTA |
| `statusChip({ label, tone })` | ok / bad / neutral |
| `flowRail({ steps, onStep })` | Flujo horizontal clickeable |
| `actionCard({ title, subtitle, onClick })` | Tarjeta en grilla Home |

## Banner compacto

Con `body[data-ui-simplify="1"]`:

- Visible: modo + `#banner-safety` (una línea).
- Oculto: LIVE badge duplicado, chat banner (detalle en Home).

## Estados unificados

Ver `UI_TERMINOLOGY.md` § Términos de estado.

## Próximo (Fase 6+)

Aplicar `QLUi.panelHeader` progresivamente en scanner, simulator, strategy_live_test sin tocar lógica cuantitativa.
