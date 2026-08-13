# HOWTO — Alpha ML ranking (GBM)

## Qué es

Un **complemento** del Ranking A: `signal_type=ml_ranking` con probabilidad de que la candidata pase `validate_candidate` (DSR). No forecast de precio. No reemplaza el scanner. No LIVE.

**Manual de panel:** [`../../manuales/03-alpha-scanner.md`](../../manuales/03-alpha-scanner.md)

## Automático (día a día)

No hace falta correr scripts. El Workbench ya está configurado así:

1. **Escanear** con checkbox **ML ranking** (default ON). Si no hay modelo, se crea uno sintético de arranque.
2. **Validar** (individual, pares OOS, o pipeline) escribe el trial en `experiments/alpha_trials/`.
3. Cada **5** trials, con ≥30 filas y ≥8 positivas, se entrena un **candidato**. El activo **no se pisa** si el AUC empeora. El modelo sintético de arranque se marca en UI.

API: `"include_ml": true` (default **true**). Desmarcar el checkbox o mandar `false` = no adjuntar `ml_ranking`.

## Entrenar a mano (opcional)

```bash
# Smoke con datos sintéticos
uv run python scripts/alpha_ml_bootstrap.py --synthetic --activate

# Con trials reales
uv run python scripts/alpha_ml_bootstrap.py --trials path/a/experiments --activate
```

Artefactos: `experiments/alpha_ml/{model_id}/` + `active.json`.

Opcional: `uv sync --extra ml` para LightGBM; sin él usa stub logístico (tests/CI).

## Validar igual que siempre

Las señales `ml_ranking` también deben pasar por **Validar** / `validate_candidate` + Ranking B. El AUC del modelo ≠ rentabilidad.
