# Manual — Reports

Historial de reportes de backtest / lab de la sesión.

## Cómo abrir

1. Menú **QL** (barra inferior) → elegir el panel.
2. **Ctrl+K** (Command Palette) → escribir el nombre.
3. Presets: QL → Research / Trading Paper / Ops (abren conjuntos de paneles).

## Invariantes

- `LIVE_BLOCKED=True` por defecto: sin unlock no hay routing LIVE a venue.
- Modo **REAL** del producto = **PAPER** (fills simulados), no órdenes en exchange de producción.
- Este panel **no** garantiza rentabilidad ni es asesoramiento financiero.

## Para qué sirve

Listar, abrir y enfocar reportes por `report_id`.

## Cómo usar

1. Abrí **Reports** y refrescá.
2. Seleccioná un reporte para detalle.
3. **→ Monte Carlo** abre MC en modo normal con ese `report_id` / backtest ligado.
4. Deep-link inverso: desde MC podés volver a Reports enfocando el id.

## Tips

- Tras F5, la sesión puede reiniciar; persistencia depende del store de sesión.
