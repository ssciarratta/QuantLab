# Trazabilidad Monte Carlo

Cadena objetivo: Scan → Instrumento → Backtest → MC → summary.json

Persistido en `session/montecarlo/<run_id>/summary.json`:

- `context` (strategy, venue, dataset, scan_id, backtest_id, …)
- `config` + `config_hash`
- `relations` (dataset_hash, strategy_params_hash, code_commit)
- `metrics`

Misma seed + misma config + mismo dataset_hash → mismos `final_equities` (tests F2).
