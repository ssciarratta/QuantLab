# Alpha Scanner optimization — status

**Actualizado:** 2026-07-27  
**Fase actual:** FASE 0–10 **COMPLETAS** + walk-forward pipeline  
**Cierre formal auditoría:** pendiente de APROBADO externo (no generar certificado)

---

## Resumen

| Fase | Estado |
|------|--------|
| 0–10 | **DONE** (ver abajo) |
| Post | Walk-forward pipeline Binance (rank≠BT) **DONE** |

**Default lab:** `legacy_v1` / `AlphaScanner` (parity tests).  
**Pipeline:** `walk_forward=True` por defecto (~70% rank / 30% BT, sin overlap).

**Tests:** alpha + F111 + walk_forward.
### FASE 9

- `observe.py`: progreso, `CancellationToken`, `ScoreCache` TTL, métricas

### FASE 10

- Guía + limitaciones + changelog en `docs/scanner/alpha-scanner-guide.md`
