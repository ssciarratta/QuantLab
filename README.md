# QuantLab

Plataforma profesional de investigación cuantitativa.

QuantLab es un **laboratorio de investigación cuantitativa**, no un bot de trading. Está diseñado para descubrir, validar, optimizar y comparar estrategias antes de delegar la ejecución a motores especializados como Hummingbot.

---

## Estado del proyecto

| Rango | Estado |
|-------|--------|
| F0–F18 | Certificados externos (`docs/audit/FASE_*_APPROVED.md`) · research-prod |
| F19–F22 | **APROBADO_INTERNO** (modos TESTER/REAL, workbench, lab panels, chat IA) · v0.14.0 |
| F23 | Paper Book + session durable + risk paper · **APROBADO_INTERNO** · v0.15.0 |
| F24 | Venue plugins + A3 MD read-only opt-in + generic CSV/REST · **APROBADO_INTERNO** · v0.16.0 |
| F25 | Ops Desk 1-click + hardening (non-loopback, experiment_id, slip, Risk) · **APROBADO_INTERNO** · v0.17.0 |
| F26 | Paper Session Runner (estrategia → risk → PaperBroker) · **APROBADO_INTERNO** · v0.18.0 |
| LIVE order routing | **BLOQUEADO** (`LIVE_BLOCKED=True`) |

> Mapa: [ROADMAP_ALIGNED](docs/ROADMAP_ALIGNED.md) · [MAPA auditor](docs/audit/MAPA_FASES_PARA_AUDITOR.md) · [Arco F19–F22](docs/audit/INTERNAL_AUDIT_F19_F22_ARC.md) · [Arco F23–F25](docs/audit/INTERNAL_AUDIT_F23_F25_ARC.md) · [Noche F19–F26](docs/audit/INTERNAL_AUDIT_F19_F26_NIGHT.md)  
> **REAL ≠ LIVE** — REAL = PAPER (MD/cuenta reales + fills simulados).

---

## Inicio rápido

```bash
uv sync --frozen --extra dev
uv run pytest
uv run quantlab-health
uv run quantlab-vertical-slice
uv run quantlab-a3 health
```

### Workbench local (F20–F26)

UI loopback (stdlib) con paneles Health / MD / Blotter / Riesgo / **Sesión Paper**, Laboratorio y **Chat IA** safe-mode:

```bash
./scripts/launch_workbench.sh --no-browser
# o: uv run quantlab-workbench --no-browser
# http://127.0.0.1:8765  ·  --mode tester|paper|real  ·  live rechazado
uv run python scripts/internal_audit_smoke.py   # invariantes LIVE + imports
```

- Bind default `127.0.0.1` · `LIVE_BLOCKED=True` · REAL = PAPER (≠ LIVE)
- Non-loopback requiere `--allow-non-loopback`; 1-click: [WORKBENCH_1CLICK](docs/ops/WORKBENCH_1CLICK.md)
- Chat: FakeProvider por defecto; tools allowlist read-only (sin órdenes)
- MD: venues `a3` / `generic_csv` / `generic_rest` + plugins entry-point; `md_source` fake|env
- Specs: [F20](docs/FASE_20_WORKBENCH.md) · [F21](docs/FASE_21_LAB_PANELS.md) · [F22](docs/FASE_22_CHAT_IA.md) · [F23](docs/FASE_23_PAPER_BOOK.md) · [F24](docs/FASE_24_VENUE_MD_PLUGINS.md) · [F25](docs/FASE_25_OPS_DESK.md) · [F26](docs/FASE_26_PAPER_SESSION.md) · [plugins](docs/ops/BROKER_PLUGINS.md)

Market data / órdenes simulation offline usan Fake backend por defecto. API real:

```bash
uv run quantlab-a3 --live-api health
```

Credenciales solo vía `.env` (ver `.env.example`). Docs: [docs/A3_RUNBOOK.md](docs/A3_RUNBOOK.md).

---

## Review Package (auditoría)

```bash
uv run python scripts/build_review_package.py --phase 3 --version 1.0
```

Entregables: `QuantLab_Review_Fase_03_v1.0.zip` + `.sha256` + `.validation.txt` + `REVIEW_REQUEST.md`.

---

## Visión

Construir un sistema central de investigación cuantitativa capaz de:

- Ingerir, validar calidad y almacenar datos de múltiples exchanges.
- Simular estrategias con dos niveles de fidelidad (bar-based y microestructura).
- Validar resultados con metodología científica (walk-forward, out-of-sample).
- Comparar 30+ estrategias sobre 100+ activos.
- Optimizar parámetros de forma reproducible (solo post-validación).
- Seleccionar oportunidades vía Alpha Scanner.
- Exportar estrategias aprobadas a Hummingbot sin acoplamiento directo.

---

## Principios de diseño

1. **Diseño antes de código** — Arquitectura v1.1 es fuente de verdad.
2. **Modularidad con disciplina** — Abstraer solo cuando hay necesidad demostrada (DEC-013).
3. **Reproducibilidad científica** — ExperimentManifest con commit, seed, deps, platform.
4. **Escalabilidad progresiva** — Contratos de dominio estables.
5. **Separación investigación / ejecución** — QuantLab investiga; Hummingbot ejecuta.
6. **Intenciones, no ejecución** — Strategy produce `OrderIntent`; el simulador decide fills.
7. **Raw inmutable** — Datos originales en `raw/`; normalización en `processed/`.
8. **Auditoría por fases** — Cada fase requiere revisión GPT antes de continuar.
9. **Schemas de manifests versionados** — DEC-036 / docs/MANIFEST_VERSIONING.md.
10. **Anticorrupción A3** — el dominio no importa pyRofex (DEC-040).
