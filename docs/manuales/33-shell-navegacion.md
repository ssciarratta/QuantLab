# Manual — Shell, menú QL y navegación

Escritorio flotante del Workbench.

## Cómo abrir

1. Menú **QL** (barra inferior) → elegir el panel.
2. **Ctrl+K** (Command Palette) → escribir el nombre.
3. Presets: QL → Research / Trading Paper / Ops (abren conjuntos de paneles).

## Invariantes

- `LIVE_BLOCKED=True` por defecto: sin unlock no hay routing LIVE a venue.
- Modo **REAL** del producto = **PAPER** (fills simulados), no órdenes en exchange de producción.
- Este panel **no** garantiza rentabilidad ni es asesoramiento financiero.

## Layout

- Banner superior: modo, LIVE_BLOCKED, session, avisos
- Escritorio: ventanas (paneles)
- Barra inferior: status + **QL**

## Abrir paneles

- Menú **QL**
- **Ctrl+K** Command Palette
- Atajos numéricos (orden del shell) cuando estén documentados en About/Settings
- Presets Research / Trading Paper / Ops

## Ventanas

- Snap a bordes, minimize/restore all, cascade/tile, bring to front/back, maximize (F82–F86)
- Resize por bordes; tooltips en controles

## Deep-links (QLNav)

Flujos conectados:

- Reports / Backtest / Guided Lab → **Monte Carlo** (prefill ids)
- Monte Carlo → Reports / Guided Lab enfocando id

Implementación: `static/js/nav.js` + `QLShell.open(pane, opts)`.
