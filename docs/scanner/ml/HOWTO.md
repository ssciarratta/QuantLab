# HOWTO — Alpha ML ranking (GBM)

## Qué es

Un **complemento** del Ranking A: `signal_type=ml_ranking` con probabilidad de que la candidata pase `validate_candidate` (DSR). No forecast de precio. No reemplaza el scanner. No LIVE.

## Entrenar (research)

```bash
# Smoke con datos sintéticos
uv run python scripts/alpha_ml_bootstrap.py --synthetic --activate

# Con trials reales (después de varias validaciones)
uv run python scripts/alpha_ml_bootstrap.py --trials path/a/experiments --activate
```

Artefactos: `experiments/alpha_ml/{model_id}/` + `active.json`.

Opcional: `uv sync --extra ml` para LightGBM; sin él usa stub logístico (tests/CI).

## Usar en scanner

API body: `"include_ml": true` (default **false**).

Si no hay modelo activo → payload sin cambio de scores + nota `ml_ranking.active=false`.

## Validar igual que siempre

Las señales `ml_ranking` también deben pasar por **Validar** / `validate_candidate` + Ranking B. El AUC del modelo ≠ rentabilidad.
