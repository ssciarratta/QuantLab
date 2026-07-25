# Architecture Review — Fase 5 Oficial Módulo 1 (Feature Transformers)

## 1. Estado actual
- `core/types` tiene `Bar` OHLCV; no hay capa `features/`.
- Research tiene AlphaScanner/estrategias; no pipelines de features.
- La “F5 local” previa fue ejecución (slippage/fees/artifacts), no Features.

## 2. Archivos afectados
| Archivo | Tipo | Impacto |
|---------|------|---------|
| `src/quantlab/features/**` | crear | alto |
| `tests/unit/features/**` | crear | medio |
| `docs/FASE_05_FEATURES.md` | crear | bajo |
| `docs/ROADMAP_ALIGNED.md` | modificar | bajo |

## 3. Riesgos
- Lookahead → solo barras `≤ i` al calcular punto `i`.
- Contaminar `core` → features importa core; core nunca importa features.
- Confusión con F5 local → documentar como “F5 Oficial Features”.

## 4. Alternativas
### A — `quantlab.features`
- Pros: capa clara, alineada a Arquitectura. Contras: nuevo paquete.
### B — `quantlab.research.features`
- Pros: junto a research. Contras: mezcla scanner/estrategias con feature store futuro.

## 5. Recomendación
**A — `src/quantlab/features/`**. Contratos Protocol + dataclasses frozen; transformers precio/retorno/volumen; tests anti-lookahead.
