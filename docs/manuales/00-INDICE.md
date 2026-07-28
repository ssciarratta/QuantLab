# Manuales de uso — QuantLab Workbench

**Versión tip:** 1.01.0 · **Actualizado:** 2026-07-27
**UI:** http://127.0.0.1:8765 · Help: QL → Help / Docs → carpeta `manuales/`

Este índice lista **todas las funciones de panel** del Workbench. Cada archivo es un manual operativo (cómo usar, límites, invariantes).

## Arranque rápido

Ver también: [`../GUIA_COMPLETA_QUANTLAB.md`](../GUIA_COMPLETA_QUANTLAB.md) · [`../ops/WORKBENCH_1CLICK.md`](../ops/WORKBENCH_1CLICK.md)

```bash
uv sync --extra dev
uv run quantlab-workbench
# browser → http://127.0.0.1:8765
```

## Invariantes globales

- `LIVE_BLOCKED` · `REAL = PAPER` · secrets nunca en git/logs/chat
- Chat IA: safe-mode (no envía órdenes)
- Alpha Scanner / Monte Carlo / Backtest: investigación; no predicen el futuro

## Manuales por panel

### Laboratorio / investigación

| Manual | Panel |
|--------|-------|
| [01-guided-lab.md](01-guided-lab.md) | Guided Lab |
| [02-backtest.md](02-backtest.md) | Backtest |
| [03-alpha-scanner.md](03-alpha-scanner.md) | Alpha Scanner |
| [04-montecarlo.md](04-montecarlo.md) | Monte Carlo |
| [05-validation.md](05-validation.md) | Validation Splits |
| [06-optimizer.md](06-optimizer.md) | Optimizer |
| [07-features.md](07-features.md) | Features |
| [08-export-hb.md](08-export-hb.md) | Hummingbot Export |
| [09-metrics.md](09-metrics.md) | Metrics / Último |
| [10-reports.md](10-reports.md) | Reports |
| [11-experiments.md](11-experiments.md) | Experiments |

### Datos / mercado

| Manual | Panel |
|--------|-------|
| [12-health.md](12-health.md) | Salud / Modo |
| [13-market.md](13-market.md) | Market Data |
| [14-universe.md](14-universe.md) | Universe |
| [15-catalog.md](15-catalog.md) | Data Catalog |

### Paper trading

| Manual | Panel |
|--------|-------|
| [16-blotter.md](16-blotter.md) | Paper Blotter |
| [17-journal.md](17-journal.md) | Journal |
| [18-paper-session.md](18-paper-session.md) | Sesión Paper |
| [19-positions.md](19-positions.md) | Posiciones |
| [20-risk.md](20-risk.md) | Riesgo |
| [21-reconciliation.md](21-reconciliation.md) | Reconciliación |

### Ops / soporte

| Manual | Panel |
|--------|-------|
| [22-venues.md](22-venues.md) | Venues |
| [23-api-explorer.md](23-api-explorer.md) | API Explorer |
| [24-diagnostics.md](24-diagnostics.md) | Diagnostics |
| [25-docs.md](25-docs.md) | Help / Docs |
| [26-chat.md](26-chat.md) | Chat IA |
| [27-settings.md](27-settings.md) | Settings |
| [28-sessions.md](28-sessions.md) | Sessions |
| [29-activity.md](29-activity.md) | Activity |
| [30-access-log.md](30-access-log.md) | Access Log |
| [31-backups.md](31-backups.md) | Backups |
| [32-ops-metrics.md](32-ops-metrics.md) | Ops Metrics |

### Shell / navegación

| Manual | Tema |
|--------|------|
| [33-shell-navegacion.md](33-shell-navegacion.md) | Menú QL, presets, ventanas, deep-links |
| [34-about.md](34-about.md) | About / versión |

## Guías técnicas (subdirs Help)

- `docs/montecarlo/*.md` — Monte Carlo (métodos, interpretación, corrección)
- `docs/scanner/*.md` — Alpha Scanner
- `docs/ops/*.md` — Runbooks ops
