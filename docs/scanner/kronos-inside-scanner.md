# Kronos dentro del Alpha Scanner

**Actualizado:** 2026-08-03  
**Modelo:** `NeoQuasar/Kronos-small` + `NeoQuasar/Kronos-Tokenizer-base`  
**Código:** `src/quantlab/research/alpha/kronos/`

## Idea

El flujo externo **no cambia**:

`Alpha Scanner → Simulador/Backtest → Monte Carlo`

Kronos no es un panel ni una etapa. Es una fuente adicional **dentro** del
Scanner para re-rankear candidatos según el horizonte futuro estimado.

## Activar / desactivar

- UI Scanner: checkbox **Kronos** (ON por defecto) + Top 20/30 + horizonte + muestras  
- API: body `kronos: { kronos_enabled, kronos_top_n, kronos_pred_len, ... }`  
- `legacy_v1`: peso 0 (popup); checkbox “Kronos en legacy” → peso 0.05  

## Hardware

| Recurso | Notebook típico |
|---------|-----------------|
| Disco | ≥8 GB libres recomendados (torch + pesos) |
| RAM | ≥8 GB; liberar memoria antes de escanear |
| GPU | opcional CUDA; fallback CPU automático |
| Python | 3.11+ (QuantLab uv: 3.12.x OK) |

## Troubleshooting

| Síntoma | Qué hacer |
|---------|-----------|
| `kronos.status=unavailable` | `uv sync --extra kronos --extra dev` + clonar `third_party/kronos` |
| Timeout | bajar `kronos_top_n` / `sample_count` / `pred_len` |
| OOM | `kronos_device=cpu`, top_n=15, sample_count=2 |
| Scores Kronos `null` | no es bug: ausente ≠ 0; ranking tradicional válido |
| Legacy igual que antes | esperado (peso 0) |

## Reproducibilidad

Cada escaneo registra en `result.kronos`: modelo, tokenizer, device, seed,
lookback, pred_len, sample_count, status, inference_ms, data_hash por fila.
