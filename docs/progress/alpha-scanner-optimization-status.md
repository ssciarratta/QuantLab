# Alpha Scanner optimization — status

**Actualizado:** 2026-07-27  
**Fase actual:** FASE 0–10 **COMPLETAS** + walk-forward pipeline + UX Guided Lab  
**Cierre formal auditoría:** pendiente de APROBADO externo (no generar certificado)

---

## Resumen

| Fase | Estado |
|------|--------|
| 0–10 | **DONE** (ver abajo) |
| Post | Walk-forward pipeline Binance (rank≠BT) **DONE** |
| Post UX | Guided Lab opt-out WF + rank_fraction + legend + label_es **DONE** |

**Default lab:** `legacy_v1` / `AlphaScanner` (parity tests).  
**Pipeline:** `walk_forward=True` por defecto (~70% rank / 30% BT, sin overlap).  
**UI:** checkbox walk-forward (ON), `rank_fraction`, leyenda; perfiles con `label_es`.

**Tests:** alpha + F111 + walk_forward + Guided Lab estáticos.

### FASE 9

- `observe.py`: progreso, `CancellationToken`, `ScoreCache` TTL, métricas

### FASE 10

- Guía + limitaciones + changelog en `docs/scanner/alpha-scanner-guide.md` (incluye walk-forward)
