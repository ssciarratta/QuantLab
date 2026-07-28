# Guía Monte Carlo (QuantLab)

**Actualizado:** 2026-07-27 · tip 1.01.0  
**No predice el futuro.** Mide dispersión bajo shocks de precio en un dataset.

Manual de panel: [`../manuales/04-montecarlo.md`](../manuales/04-montecarlo.md) · estado corrección: [`../progress/montecarlo-correction-status.md`](../progress/montecarlo-correction-status.md)

## Qué simula (lab actual)

1. Dataset: sintético `n_bars` velas **1m** (`WB:SYN`) y/o referencia a BT/scan (`DatasetReference`).
2. Por escenario: shock gaussiano OHLC (σ = `noise_bps/10000`) + re-run estrategia lab (BuyOnce demo en technical_lab).
3. Agrega equities finales con batching (Welford / histograma / reservoir) → media, desvío, **IC de la media** (Wald).
4. Jobs async cancelables para N grandes.

## Parámetros

| Campo UI | Código | Significado |
|----------|--------|-------------|
| Escenarios | `n_scenarios` | **2 … 1_000_000** (default tip ~1000; presets 100 / 1k / 10k / 100k / 1M) |
| Velas por escenario | `n_bars` | Velas 1m del sintético **por** escenario (horizonte) |
| Ruido bps | `noise_bps` | 10 bps = 0.10% |
| Seed | `seed` | Reproducibilidad |
| Confirmación grande | `confirm_large` | Obligatoria si N ≥ 100_000 |
| Trayectorias guardadas | `max_persisted_trajectories` | Tope de paths persistidos (~16); **no** limita N |

## Modos

| Modo | Requisito | Uso |
|------|-----------|-----|
| `technical_lab` | — | Demo sintético |
| `normal` | `backtest_id` | Ligado a un backtest de sesión |

Deep-link: desde **Reports / Backtest / Guided Lab** → Monte Carlo (prefill ids). Desde MC → Reports / Guided Lab por id.

## Capital y fees

El panel puede mostrar capital inicial/final y fee por lado (lab tip VIP0 Spot **10 bps** / 0.10% por lado) para validar el modelo de costos.

## CI95

Es el intervalo de confianza de la **media** de equities finales, no una banda de un solo escenario.

## Trazabilidad

Payload con `context`, `config`, `metrics`, `relations`, hashes (schema legible v1/v2 según normalizer).  
Legacy se lee con `normalize_montecarlo_payload` (campos ausentes → No disponible).

Detalle: [`montecarlo-traceability.md`](montecarlo-traceability.md) · métodos [`montecarlo-methods.md`](montecarlo-methods.md) · interpretación [`montecarlo-interpretation.md`](montecarlo-interpretation.md).

## Limitaciones

- Sin trayectorias por defecto (opt-in `store_paths` / reservoir acotado).
- Mode `normal` exige `backtest_id`; no inventa ligazón a Scan/BT.
- N=1e6 es viable con batching, pero consume CPU/tiempo; usá cancel y confirmación grande.
- Moneda sintética lab tip: **LAB**.
- Investigación: no es predicción ni garantía de PnL.
