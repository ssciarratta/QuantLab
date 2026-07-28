# Manual — Help / Docs

Navegador de markdown allowlist bajo `docs/`.

## Cómo abrir

1. Menú **QL** (barra inferior) → elegir el panel.
2. **Ctrl+K** (Command Palette) → escribir el nombre.
3. Presets: QL → Research / Trading Paper / Ops (abren conjuntos de paneles).

## Invariantes

- `LIVE_BLOCKED=True` por defecto: sin unlock no hay routing LIVE a venue.
- Modo **REAL** del producto = **PAPER** (fills simulados), no órdenes en exchange de producción.
- Este panel **no** garantiza rentabilidad ni es asesoramiento financiero.

## Para qué sirve

Leer guías e instructivos **dentro** del Workbench.

## Carpetas visibles

- `docs/*.md` (raíz)
- `docs/ops/*.md`
- `docs/manuales/*.md` ← estos manuales
- `docs/montecarlo/*.md`
- `docs/scanner/*.md`

## Cómo usar

1. Abrí **Help / Docs**.
2. Filtrá / elegí un archivo.
3. Empezá por `manuales/00-INDICE.md` o `GUIA_COMPLETA_QUANTLAB.md`.

## Seguridad

- Path traversal fail-closed.
- No lista `docs/audit/` ni otros subdirs no allowlist.
