# Guía Monte Carlo (QuantLab)

**No predice el futuro.** Mide dispersión bajo shocks de precio en un dataset.

## Qué simula (lab actual)

1. Dataset sintético: `n_bars` velas **1m** (`WB:SYN`).
2. Por escenario: shock gaussiano OHLC (σ = `noise_bps/10000`) + re-run `BuyOnce`.
3. Agrega equities finales → media, desvío, **IC de la media** (Wald).

## Parámetros

| Campo UI | Código | Significado |
|----------|--------|-------------|
| Escenarios | `n_scenarios` | Cantidad de re-runs |
| Barras del dataset | `n_bars` | Velas 1m del sintético (horizonte) |
| Ruido bps | `noise_bps` | 10 bps = 0.10% |
| Seed | `seed` | Reproducibilidad |

## CI95

Es el intervalo de confianza de la **media** de equities finales, no una banda de un solo escenario.

## Trazabilidad

Payload schema v2: `context`, `config`, `metrics`, `relations`, hashes.  
Legacy v1 se lee con `normalize_montecarlo_payload` (campos ausentes → No disponible).

## Limitaciones

- Sin trayectorias por defecto (opt-in `store_paths`).
- Demo lab no usa Scan/BT reales salvo que pases IDs.
- N≤20 en modo mini.
