# Alpha Scanner optimization — status

**Actualizado:** 2026-07-27  
**Fase actual:** FASE 1 — Modelos y contratos **COMPLETA** (legacy_v1 sin cambio de scores)  
**Siguiente:** FASE 2 — UniverseBuilder + elegibilidad + DataQualityReport

---

## FASE 0 — hecho

| Ítem | Estado |
|------|--------|
| Mapa del scanner real | OK — ver auditoría |
| Fórmula composite documentada | OK — 0.35/0.35/0.30 min-max |
| Origen `fetched` / `top` | OK — `fetched` = label UI de `n_symbols_fetched` |
| Ejemplo controlado | OK — `docs/scanner/fase0_baseline_synthetic.json` |
| Tests subset alpha/F111 | OK — 27 passed |
| Auditoría | OK — `docs/scanner/current-alpha-scanner-audit.md` |

## FASE 1 — hecho

| Ítem | Estado |
|------|--------|
| `AlphaScanRequest` / `AlphaScanResult` / `RankedCandidate` | OK — `research/alpha/models.py` |
| Adapter `run_legacy_v1_scan` | OK — `research/alpha/legacy.py` |
| Breakdown componentes + summary | OK |
| Nota “score ≠ rentabilidad” | OK |
| Golden baseline F0 sigue igual | OK — test |
| Tests F1 | OK — 3 nuevos + alpha suite PASS |
| mypy strict alpha | OK |
| Cambio de fórmula default | **No** |

### Archivos FASE 1

- Creados: `src/quantlab/research/alpha/models.py`, `legacy.py`, `tests/unit/research/test_alpha_models_f1.py`
- Modificados: `research/alpha/__init__.py` (`__all__`)

---

## Fases pendientes

| Fase | Título | Estado |
|------|--------|--------|
| 0 | Discovery & baseline | **DONE** |
| 1 | Modelos / contratos | **DONE** |
| 2 | Universo + calidad datos | PENDING |
| 3–10 | Features → auditoría final | PENDING |
