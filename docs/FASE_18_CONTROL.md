# Fase 18 — Control Total (research-ops)

Post F0–F17 certificado. Objetivo: endurecer operación de laboratorio **sin** habilitar trading live.

## Incluye
- Paths FeatureStore sin colisión
- LogReturn Decimal puro
- Paper ledger local (auditoría de sims)
- Health check CLI
- Convención de fees/PnL documentada

## No incluye
- Order routing LIVE / A3 real
- Cluster / ledger multi-nodo (TD-03)
- Certificado automático (requiere Meta-Auditor)

## Uso rápido
```bash
uv run quantlab-health
uv run pytest tests/unit/fase18 -q
```
