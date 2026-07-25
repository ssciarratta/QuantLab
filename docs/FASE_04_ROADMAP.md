# Fase 4 — Roadmap inicial

**Estado:** En desarrollo (MVP de los 3 pilares implementado)  
**Fecha:** 2026-07-24  
**Prerrequisito:** [`docs/audit/FASE_03_APPROVED.md`](audit/FASE_03_APPROVED.md)  
**Versión proyecto:** 0.4.0

---

## Objetivo

Cerrar el loop investigación: datos certificados (F3) → selección de universo → simulación reproducible → métricas inmutables, sin order routing real.

---

## Pilares

### 1. Motor de Simulación Bar-Based / Event-Driven

Motor de ejecución de experimentos que:

- Ingiere `DatasetManifest` (y datasets processed asociados).
- Ejecuta `Strategy.on_event()` / adaptadores bar-based según contrato DEC-014.
- Produce `SimulationResult` (equity, fills, orders, snapshots, metadata congelada).

**Entregables esperados:** runner de backtest, clock de simulación, políticas mínimas de fill (baseline), integración con manifests versionados.

### 2. Alpha Scanner / Selector de Activos

Módulo de filtrado y ranking de activos basado en:

- Volatilidad
- Volumen
- Liquidez

**Entregables esperados:** scoring determinista, ranking reproducible, salida tipada consumible por el motor de simulación (universo filtrado).

### 3. Engine de Métricas de Rendimiento

Cálculo inmutable de:

- Sharpe
- Max Drawdown
- Win Rate
- Profit Factor
- Curva de Equity

**Entregables esperados:** `MetricsResult` poblado desde `SimulationResult`, versionado de fórmulas (`metrics_version`), sin mutación post-cómputo.

---

## Fuera de alcance (sigue bloqueado)

- Order routing real / LIVE A3 (ver `docs/A3_PRODUCTION_READINESS.md`).
- Microestructura 5B completa (puede planificarse, no es el baseline F4).
- Optimización de parámetros a gran escala (post-validación científica).

---

## Orden de trabajo sugerido

1. Motor de simulación mínimo viable (bar-based) + tests.
2. Engine de métricas sobre `SimulationResult`.
3. Alpha Scanner alimentando el universo del motor.

---

## Progreso MVP (2026-07-24)

| Pilar | Módulo | Estado |
|-------|--------|--------|
| Simulación | `quantlab.simulation` | ✅ MVP |
| Métricas | `quantlab.metrics` | ✅ MVP |
| Alpha Scanner | `quantlab.research.alpha` | ✅ MVP |
| Slice | `quantlab-fase4-slice` | ✅ |

Pendiente para cierre formal F4: Review Package + auditoría GPT.
