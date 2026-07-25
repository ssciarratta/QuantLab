# IMPROVEMENTS — Research-prod post-hardening

**Fecha:** 2026-07-25

## Qué funcionó
- Plan A0–A7 ejecutable de punta a punta sin habilitar LIVE.
- Fail-closed universal (`NullRouter` + live_gate) con tests red-team.
- Separar `order_router` de imports runtime de `a3` eliminó el ciclo de import.
- Checklist + SELF_AUDIT como DoD verificable.

## Qué no funcionó / fricciones
- Push de `.github/workflows/ci.yml` rechazado por OAuth sin scope `workflow`.
  Mitigación: fuente en `docs/ci/ci.yml.example` + `.gitignore` del workflow local.
- Checksum A3 hasheaba `str(rows)` en vez del JSONL → verify_dataset fallaba hasta alinear hash al archivo.

## Riesgos
- LIVE sigue bloqueado; no confundir research-prod con trading-prod.
- Ops metrics son in-process (sin Prometheus/exporter); suficiente para lab, no HA.
- TD-03 ledger distribuido sigue fuera de alcance.

## Mejoras futuras
- Cuando haya PAT con scope `workflow`, pushear CI desde el example.
- Subir cobertura DuckDB/batch/sizing sin abrir Fase 18.
- TD-04 Decimal puro en LogReturn si aparece sesgo numérico en research.
