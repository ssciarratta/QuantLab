# Fase 25 — Ops desk (1-click + hardening)

**Estado:** APROBADO_INTERNO (v0.17.0) — externo pendiente  
**Prerrequisito:** F23–F24  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F25.md` · arco `INTERNAL_AUDIT_F23_F25_ARC.md`

## Objetivo
- `scripts/launch_workbench.sh` + `.desktop` 1-click
- `--allow-non-loopback` (cierra M2 non-loopback)
- Charset `experiment_id` (cierra M1)
- Paper slip bps opcional
- Panel Risk + banner session

## DoD
- [x] `scripts/launch_workbench.sh` — uv/venv, sync opcional, browser
- [x] `packaging/quantlab-workbench.desktop` — Exec→script; Comment ES; Categories=Finance
- [x] `docs/ops/WORKBENCH_1CLICK.md`
- [x] launch: host no-loopback exige `--allow-non-loopback` (exit 2) + warning stderr
- [x] `experiment_id` charset `^[A-Za-z0-9_-]+$` en lab_services / export → ValidationError/400
- [x] PaperBroker `slippage_bps` adverso; CLI `--slippage-bps` + connect API + WorkbenchState
- [x] UI panel Riesgo (límites + session path) + menú Inicio; banner `session_id`
- [x] Smoke: F23 book import, F24 plugins, F25 allow-non-loopback
- [x] Tests: non-loopback, experiment_id charset, paper slippage
- [x] Bump **0.17.0**; `LIVE_BLOCKED is True`

## Fuera de alcance
LIVE · Electron · auth WAN
