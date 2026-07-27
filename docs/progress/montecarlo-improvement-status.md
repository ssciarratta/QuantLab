# Monte Carlo improvement — status

**Actualizado:** 2026-07-27  
**Branch:** `cursor/modo-real-workbench-aafd`  
**LIVE_BLOCKED:** True  
**Cierre formal:** no generar `FASE_*_APPROVED.md`

---

## Resumen de fases

| Fase | Tema | Estado |
|------|------|--------|
| 0 | Auditoría obligatoria | **DONE** |
| 1 | Modelos contexto/config/result | pending |
| 2 | Persistencia + trazabilidad | pending |
| 3 | Compat schema v1 | pending |
| 4 | Métricas backend | pending |
| 5 | Cabecera UI | pending |
| 6 | Panel qué simulamos | pending |
| 7 | Resultados UI | pending |
| 8 | Gráficos | pending |
| 9 | Historial | pending |
| 10 | Navegación Scan/BT/MC | pending |
| 11 | Tests | pending |
| 12 | Docs finales | pending |

---

## FASE 0 — DONE

**Entregable:** `docs/montecarlo/current-montecarlo-audit.md`

**Hallazgos clave (código):**
- Método único: shock gaussiano OHLC × re-run `BarBacktester` + `BuyOnceStrategy`
- `n_bars` = # velas sintéticas 1m (`make_synthetic_bars`), no BT previo
- `noise_bps` = σ gauss en bps (÷10000); 10 bps = 0.10%
- CI95 = Wald IC de la **media** (`μ ± 1.96·σ/√N`, `pstdev` poblacional)
- Sin contexto estrategia/venue/dataset en payload; sin trayectorias en JSON
- Baseline: 11 tests PASS · ruff OK · mypy OK · repro seed=42 True

**Gates FASE 0:**
```
ruff check src/quantlab/montecarlo + montecarlo_runs.py → OK
mypy --strict src/quantlab/montecarlo → OK
pytest MC-related → 11 passed
```

**Próximo:** FASE 1 — modelos tipados evolucionando `quantlab.montecarlo` existente.
