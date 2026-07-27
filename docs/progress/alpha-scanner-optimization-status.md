# Alpha Scanner optimization — status

**Actualizado:** 2026-07-27  
**Fase actual:** FASE 6 — Multi-venue **COMPLETA** (capabilities + ranking combinado)  
**Siguiente:** FASE 7 — Persistencia / reproducibilidad (`scan_id`, hashes, reload)

---

## Hecho 0–6

Default lab: `AlphaScanner` / `legacy_v1`.  
Nuevo path: features → profiles → scorer → multi-venue.

### FASE 6

- `research/alpha/venues.py`: capabilities Binance/HL/Bybit/OKX/lab
- Solo Binance+lab `fetch_implemented=True`
- `scan_multi_venue` omite venues sin fetch con warning (no silencio)
- Tests: `test_alpha_venues_f6.py`

### Limitación

Fetch real HL/Bybit/OKX **no** implementado (declarativo).

---

## Pendiente

7 Persistencia · 8 Workbench UX · 9 Perf · 10 Docs finales
