# IMPROVEMENTS — Research-prod post-hardening

**Fecha:** 2026-07-25

## Qué funcionó
- Plan A0–A7 ejecutable de punta a punta sin habilitar LIVE.
- Fail-closed universal (`NullRouter` + live_gate) con tests red-team.
- Separar `order_router` de imports runtime de `a3` eliminó el ciclo de import.
- Checklist + SELF_AUDIT como DoD verificable.
- TD-05 `min_delay` wall-clock con `bar_times` en el engine.
- TD-03 research: federación de shards (`reconcile_indexes` / `merge_from`).
- CI Actions versionado en `.github/workflows/ci.yml`.

## Qué no funcionó / fricciones
- Push histórico de workflows falló por OAuth sin scope `workflow` (mitigado: workflow versionado + `SKIP_WORKFLOWS=1` escape hatch).
- Checksum A3 hasheaba `str(rows)` en vez del JSONL → verify_dataset fallaba hasta alinear hash al archivo.

## Riesgos
- LIVE sigue bloqueado; no confundir research-prod con trading-prod.
- Ops metrics son in-process (sin Prometheus/exporter); suficiente para lab, no HA.
- TD-03 residual: ACID multi-nodo / HA cluster (solo trading-prod).

## Mejoras futuras
- Subir cobertura DuckDB/batch/sizing.
- Observabilidad exportable (Prometheus) si el lab escala.
- TD-09 FeatureStore remoto si hace falta multi-host storage.
