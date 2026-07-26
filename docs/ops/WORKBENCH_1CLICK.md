# Workbench 1-click (Linux) — Fase 25 Ops Desk

Arranque portable del QuantLab Workbench desde el escritorio o la terminal.
**LIVE sigue bloqueado** (`LIVE_BLOCKED=True`).

## Requisitos

- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/) **o** un `.venv` en la raíz del repo
- Entorno gráfico (abre el browser por defecto)

## Script

```bash
chmod +x scripts/launch_workbench.sh
./scripts/launch_workbench.sh
```

Opciones útiles:

| Variable / flag | Efecto |
|-----------------|--------|
| `QUANTLAB_SYNC=1` | Ejecuta `uv sync --extra dev` antes de arrancar |
| `--no-browser` | No abre el navegador |
| `--mode paper` | Modo PAPER (REAL = alias paper) |
| `--slippage-bps 5` | Slippage adverso paper (bps) |
| `--host 0.0.0.0 --allow-non-loopback` | Bind no-loopback (**requiere flag**; warning stderr) |

El script:

1. Ubica la raíz del repo relativa a `scripts/`
2. Prefiere `uv run quantlab-workbench` si `uv` está en `PATH`
3. Si no, usa `.venv/bin/quantlab-workbench` o `python -m quantlab.workbench.launch`

## Acceso directo `.desktop`

1. Copiá `packaging/quantlab-workbench.desktop` a `~/.local/share/applications/`
2. Editá `Path=` con la ruta absoluta del clone (p. ej. `/home/vos/QuantLab`)
3. `Exec=scripts/launch_workbench.sh` queda relativo a ese `Path`
4. Alternativa: `Exec=/home/vos/QuantLab/scripts/launch_workbench.sh` (absoluto) y omití `Path`

```bash
mkdir -p ~/.local/share/applications
cp packaging/quantlab-workbench.desktop ~/.local/share/applications/
# editar Path=…
update-desktop-database ~/.local/share/applications/ 2>/dev/null || true
```

Categoría: `Finance`. Comment en español (LIVE bloqueado).

## Seguridad

- Bind default: `127.0.0.1` (loopback)
- Host distinto de `127.0.0.1` / `::1` / `localhost` → abort exit 2 salvo `--allow-non-loopback`
- Sin auth HTTP (trust loopback); no exponer a WAN
