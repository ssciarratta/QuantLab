# Autauditoría exhaustiva QuantLab — 2026-07-25

**Versión:** 0.9.0  
**QA snapshot:** 191 passed · mypy strict · ruff · coverage **86.5%** (mín. 80%)  
**Canvas:** `quantlab-self-audit.canvas.tsx`  
**Agentes/acciones:** `docs/ops/HARDENING_AGENTS.md`

---

## Veredicto

| Modo | ¿Listo? |
|------|---------|
| **Research-prod** (lab reproducible, CI, sin secretos, LIVE fail-closed) | **NO aún** — gaps críticos de seguridad/LIVE |
| **Trading-prod** (routing real, reconciliación, HA) | **NO** — bloqueado por diseño + TD-03 |

QuantLab es un laboratorio de investigación certificado F0–F17. “Poner en producción” debe interpretarse como **research-prod seguro**, no como trading live.

---

## CRITICAL

| ID | Hallazgo | Acción |
|----|----------|--------|
| C1 | PAT `ghp_*` embebido en `git remote` | **CERRADO:** remote limpio + token revocado (`POST /credentials/revoke`, verify 401) + GCM erase + `gh auth setup-git` |
| C2 | `live_gate` no cablea `A3Adapter.place_order` / `PyRofexBackend.send_order` | Fail-closed universal |
| C3 | Capa `data/exchanges/a3` puede enviar órdenes reales | Separar NullRouter / ExecutionBackend |

## HIGH

| ID | Hallazgo | Acción |
|----|----------|--------|
| H1 | `ParallelBatchRunner` traga excepciones | Modo `strict` |
| H2 | `verify_dataset` no hashea storage (TD-14) | Checksum real |
| H3 | CI Actions ausente (solo example) | Activar workflow |
| H4 | Storage sin WAL / Parquet no atómico | Endurecer I/O |
| H5 | Accounting omite fills huérfanos | Fail/issue |
| H6 | Docs `Roadmap.md` contradictorio | Alinear |
| H7 | Observabilidad = solo structlog | Métricas mínimas ops |

## MEDIUM / LOW

- TD-15 `profit_factor=999` · TD-16 Sortino/Sharpe · TD-04 LogReturn float  
- TD-05 latencia wall-clock · zip-slip en `backup.restore`  
- Cobertura baja: `duckdb_backend` 59%, `sizing` 60%, `batch` 70%, Avellaneda 73%

---

## Optimizaciones prioritarias

1. Unificar **RoutingPolicy** fail-closed en todo path de órdenes.  
2. Batch strict + monitor con `Lock`.  
3. Parquet/raw/kill_switch atómicos; SQLite WAL.  
4. Eliminar sentinels de métricas.  
5. CI en `main` + docs alineadas.  
6. Tests de cableado LIVE↔A3 (red team).

---

## Definición de Done — Research-prod

- [x] Token GitHub revocado + remote limpio  

- [ ] Ningún `send_order` alcanzable sin `assert_live_routing_blocked`  
- [ ] `execution.enabled: false` default  
- [ ] CI workflow activo  
- [ ] `verify_dataset` real + accounting fail-closed  
- [ ] Batch strict + suite E2E research sin LIVE  
- [ ] Docs únicas (`ROADMAP_ALIGNED` como verdad)
