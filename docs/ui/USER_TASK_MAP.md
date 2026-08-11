# Mapa de tareas de usuario — QuantLab Workbench

Objetivo: reorganizar la UI por **qué quiere hacer el usuario**, no por módulo técnico.

## Tareas principales

| # | Tarea (ES) | Pregunta del usuario | Paneles actuales | Pasos hoy (aprox.) | Propuesta |
|---|------------|----------------------|------------------|--------------------|-----------|
| T1 | **Empezar / orientarme** | ¿Qué puedo hacer? ¿Está todo OK? | health, about, chat, guided_lab | 3–5 ventanas al boot | **Inicio** único: estado + continuar + 6 acciones |
| T2 | **Buscar oportunidades** | ¿Qué moneda/par conviene mirar? | scanner, universe, market, features, catalog | 2–4 | Grupo **Investigar**; Scanner como hub |
| T3 | **Probar estrategia en histórico** | ¿Cómo rinde en el pasado? | backtest, simulator, optimize, validation | 3–6 | Grupo **Probar**; wizard Sim → BT |
| T4 | **Estresar escenarios** | ¿Qué pasa con ruido/volatilidad? | montecarlo, reports | 2–4 | Acción desde Sim/BT: "Simular escenarios" |
| T5 | **Ejecutar en prueba** | ¿Funciona con precios reales sin riesgo? | strategy_live_test, paper_session, binance_* | 4–8 | **Un solo flujo** "Ejecutar en prueba" (paper/testnet) |
| T6 | **Monitorear corrida** | ¿Qué está haciendo ahora? ¿PnL? | strategy_live_test, blotter, journal, positions, risk | 3–5 | Grupo **Monitorear**; una vista "Operación activa" |
| T7 | **Revisar resultados** | ¿Qué salió? ¿Comparo runs? | metrics, reports, experiments, sim_registry | 2–4 | Grupo **Resultados** |
| T8 | **Exportar / llevar afuera** | ¿Cómo lo llevo a Hummingbot? | export_hb | 2–3 | Sub-acción en Resultados |
| T9 | **Configurar sistema** | ¿Keys, sesión, backups? | settings, sessions, backups, binance_* | 3–6 | Grupo **Sistema** |
| T10 | **Diagnosticar problemas** | ¿Por qué falla? | diagnostics, api_explorer, access_log, activity | 2–4 | "Diagnóstico" bajo Sistema |

## Flujos conectados (objetivo)

```text
Buscar oportunidades (Scanner)
    → Probar en histórico (Simulador / Backtest)
    → Simular escenarios (Monte Carlo)
    → Ejecutar en prueba (Corrida en vivo)
    → Monitorear (Operación activa)
    → Revisar resultados (Informes / Mis simulaciones)
```

Cada salto debe transportar **IDs y parámetros** (scan_id, sim_context, strategy_id, symbol) — ya parcialmente en `nav.js`; unificar en botones "Siguiente paso".

## Anti-patrones actuales

1. Usuario debe elegir entre **paper_session**, **Corrida en vivo** y **Blotter** para "correr algo".
2. **Guided Lab** duplica Scanner + Backtest + Testnet en un monolito.
3. **Boot** abre health + market + blotter sin contexto de tarea.
4. **39 paneles** en menú con 4 secciones técnicas — no mapean a T1–T10.

## Nueva navegación propuesta (7 grupos)

| Grupo | Tareas | Paneles visibles (inicial) |
|-------|--------|---------------------------|
| **Inicio** | T1 | Home (nuevo) |
| **Investigar** | T2 | Scanner, Universe, Datos |
| **Probar** | T3, T4 | Simulador, Backtest, Monte Carlo |
| **Ejecutar en prueba** | T5 | Corrida en vivo (unificado) |
| **Monitorear** | T6 | Operación activa, Posiciones, Riesgo |
| **Resultados** | T7, T8 | Informes, Mis simulaciones, Experimentos |
| **Sistema** | T9, T10 | Ajustes, Diagnóstico, Sesiones |

Paneles avanzados (Optimizer, Validation, API Explorer, Ops Metrics…) → **Configuración avanzada** o búsqueda (Command Palette).

## Personas

| Persona | Tareas frecuentes | Necesita ver |
|---------|-------------------|--------------|
| Investigador | T2, T3, T4, T7 | Rankings, métricas, comparar |
| Operador paper/testnet | T5, T6 | Estado corrida, fills, riesgo |
| Admin local | T9, T10 | Sesión, backups, diagnóstico |

## Métricas de éxito UX

- Abrir Scanner → Corrida en vivo: **≤ 3 clics** con handoff visible.
- Primera visita: **≤ 1 ventana** (Inicio) antes de acción consciente.
- Ningún panel sin **nombre ES + descripción 1 línea + acción primaria única**.
