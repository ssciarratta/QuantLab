# Manual — Backups

Listado / disparo de backups de sesión o store (ops).

## Cómo abrir

1. Menú **QL** (barra inferior) → elegir el panel.
2. **Ctrl+K** (Command Palette) → escribir el nombre.
3. Presets: QL → Research / Trading Paper / Ops (abren conjuntos de paneles).

## Invariantes

- `LIVE_BLOCKED=True` por defecto: sin unlock no hay routing LIVE a venue.
- Modo **REAL** del producto = **PAPER** (fills simulados), no órdenes en exchange de producción.
- Este panel **no** garantiza rentabilidad ni es asesoramiento financiero.

## Para qué sirve

Respaldar estado antes de cambios estructurales.

## Cómo usar

1. Abrí **Backups**.
2. Listá backups existentes.
3. Creá uno nuevo si el panel lo permite; verificá ruta en disco.
