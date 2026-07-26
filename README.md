# QuantLab

Plataforma profesional de investigación cuantitativa.

QuantLab es un **laboratorio de investigación cuantitativa**, no un bot de trading. Está diseñado para descubrir, validar, optimizar y comparar estrategias antes de delegar la ejecución a motores especializados como Hummingbot.

---

## Estado del proyecto

| Fase | Nombre | Estado |
|------|--------|--------|
| 0 | Fundación | Completada |
| 1 | Diseño de arquitectura | Completada (v1.1 aprobada) |
| 2 | Fundación del dominio | Completada (v1.3) |
| 3 | Data Layer + A3 | Completada y Aprobada v1.0 |
| 4 | Motor de Simulación / Backtesting & Alpha Scanner | Completada y Aprobada v1.0 |
| 5 | Ejecución avanzada (slippage/latencia/fees/artifacts) | En Desarrollo — M1–M3 listos (v0.5.0) |

> Certificados: [F3](docs/audit/FASE_03_APPROVED.md) · [F4](docs/audit/FASE_04_APPROVED.md)  
> Roadmaps: [F4](docs/FASE_04_ROADMAP.md) · [F5](docs/FASE_05_ROADMAP.md)  
> **ORDER ROUTING REAL — BLOQUEADO** (independiente del gating de fases de investigación).

---

## Inicio rápido

```bash
uv sync --frozen --extra dev
uv run pytest
uv run quantlab-health
uv run quantlab-vertical-slice
uv run quantlab-a3 health
```

### Workbench local (F20–F22)

UI loopback (stdlib) con paneles Health / MD / Blotter, Laboratorio y **Chat IA** safe-mode:

```bash
uv run quantlab-workbench --no-browser
# http://127.0.0.1:8765  ·  --mode tester|paper|real  ·  live rechazado
uv run python scripts/internal_audit_smoke.py   # invariantes LIVE + imports
```

- Bind default `127.0.0.1` · `LIVE_BLOCKED=True` · REAL = PAPER (≠ LIVE)
- Chat: FakeProvider por defecto; tools allowlist read-only (sin órdenes)
- Specs: [F20](docs/FASE_20_WORKBENCH.md) · [F21](docs/FASE_21_LAB_PANELS.md) · [F22](docs/FASE_22_CHAT_IA.md)

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
