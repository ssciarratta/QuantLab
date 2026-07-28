# Monte Carlo — Auditoría de corrección (FASE 0)

**Fecha:** 2026-07-27  
**Baseline tests:** `tests/unit/montecarlo` + `test_mc_export_f34` + `test_sim_capital_fees` → **29 passed** (16.88s)  
**Cierre formal auditoría:** no aplica (corrección de módulo; sin FASE_*_APPROVED)

---

## 1. Componentes localizados

| Rol | Path |
|-----|------|
| UI | `src/quantlab/workbench/static/js/panes/montecarlo.js` |
| Shell / open | `src/quantlab/workbench/static/js/shell.js` |
| API client | `src/quantlab/workbench/static/js/api.js` |
| Servicio lab | `src/quantlab/workbench/lab_services.py` → `run_lab_montecarlo` |
| API HTTP | `src/quantlab/workbench/api.py` → `handle_post_lab_montecarlo` |
| Persistencia | `src/quantlab/workbench/montecarlo_runs.py` |
| Motor | `src/quantlab/montecarlo/simulator.py` |
| Modelos | `src/quantlab/montecarlo/models.py` |
| Trazabilidad | `src/quantlab/montecarlo/traceability.py` |
| Barras sintéticas | `lab_services.make_synthetic_bars` |

---

## 2. Por qué el usuario solo puede ejecutar 20 escenarios

| Capa | Límite real | Origen |
|------|-------------|--------|
| **UI HTML** | `min=2` `max=20` value=5 | `montecarlo.js` input `#mc-n` |
| **Servicio lab** | `2 ≤ n_scenarios ≤ 20` | `lab_services.py` ValidationError *"(mini)"* |
| **API** | solo tipo `int` | no valida rango; delega al lab |
| **Motor** | `n_scenarios ≥ 2`, **sin tope superior** | `MonteCarloConfig` / `MonteCarloSimulator` |

**Causa raíz:** el path HTTP/lab se diseñó como *mini lab demo* (cap 20). El motor ya admite N arbitrario. El checkbox “máx 16” es **solo trayectorias** (`max_paths_stored=16`), **no** confunde el límite de escenarios en backend — pero la UX lo mezcla visualmente.

---

## 3. Significado exacto de `n_bars`

**Definición canónica** (`models.py`): cantidad de velas del **dataset de entrada** (alias `dataset_bar_count`).

En el lab actual:

1. `make_synthetic_bars(n_bars)` genera exactamente N barras `timeframe="1m"`, instrumento `WB:SYN`.
2. Timestamps desde `2024-06-01` UTC, 1 minuto por vela.
3. Precio base 100 + drift +1/barra; OHLC = close±1.
4. Cada escenario: `_perturb` clona esas N velas con shock gaussiano OHLC y **re-ejecuta** `BarBacktester` + estrategia sobre la secuencia completa.
5. **No es:** nº de escenarios, tamaño de bootstrap block, ni “pasos MC” abstractos.
6. Hoy **siempre sintético**; `scan_id`/`backtest_id` **no cargan** dataset real.

**Etiqueta correcta propuesta:** *“Velas utilizadas por escenario”*  
**Tooltip:** *“Cada escenario vuelve a ejecutar la estrategia sobre estas N velas perturbadas.”*

---

## 4. Origen del dataset

| Campo | Valor lab |
|-------|-----------|
| `dataset_source` | `synthetic` |
| `dataset_id` | `wb-synthetic` |
| `dataset_hash` | `hash_bars(bars)` |
| `symbols` | `("WB:SYN",)` |
| `timeframe` | `1m` |
| `venue` / `network` | `lab` / `local` |
| `initial_equity` | `50000` Decimal |
| Estrategia runtime | **siempre** `BuyOnceStrategy` (aunque `strategy_id` vaya al context) |
| Fees | Binance Spot VIP0 |

La UI muestra “No disponible” cuando:

- corrida **schema v1** legacy sin `context`; o
- el render usa `na()` sobre campos None; o
- el usuario mira capital en cards (`capital_summary`) pero la fila de contexto falló / orphan sin propagar bien `strategy_name`.

El capital final **sí** sale de `initial_cash=50000` + PnL simulado; el bug es de **trazabilidad/UX**, no de magia monetaria.

---

## 5. Botones de navegación — causas

### Abrir backtest / Abrir scan

- Se **deshabilitan** si `context.backtest_id` / `scan_id` son null (corrida orphan default).
- Si el usuario tipeó IDs en inputs, se guardan en context **sin validar existencia**.
- Al click: `QLShell.open("reports"|"backtest"|"scanner"|"guided_lab")` — **abre el panel vacío**, **sin deep-link** al `run_id`.
- No hay lookup de existencia del artefacto.

### Abrir dataset

- **No existe** en la UI actual (ni botón ni handler).
- `dataset_id` se muestra como texto en contexto.

---

## 6. Ejecuciones huérfanas

`orphan = (scan_id is None and backtest_id is None)` → warning técnico.  
El lab **permite** orphan y igual corre BuyOnce sintético → equity ~50k.  
Modo normal pedido: **bloquear** sin contexto completo; modo lab técnico: auto-rellenar contexto completo y etiquetarlo (nunca “No disponible” para datos que el sistema conoce).

---

## 7. Riesgos de permitir hasta 1.000.000

| Riesgo | Severidad | Mitigación planificada |
|--------|-----------|------------------------|
| Memoria: lista de N `SimulationResult` | Crítica | No guardar results enteros; stats incrementales |
| Memoria: N `final_equities` | Alta | Umbral 10k full; luego histograma + reservoir |
| CPU sync HTTP timeout | Alta | Jobs async + poll + cancel para N grandes |
| Persistencia JSON gigante | Alta | `storage_mode=summary_and_sample` |
| UI DOM | Alta | No renderizar millón de puntos |
| Confirmación accidental 1e6 | Media | Confirm + cost estimate |
| Confundir 16 paths con N | Media | Renombrar checkbox + docs |

---

## 8. Architecture Review — corrección MC

### Estado actual
- Mini-lab sync: N≤20, dataset sintético fijo, BuyOnce hardcodeado.
- Schema v2 de contexto ya existe; v1 legible.
- Motor sin tope; lab con tope 20.
- Navegación cosméticas (abrir panel).

### Archivos afectados (plan)

| Archivo | Cambio | Impacto |
|---------|--------|---------|
| `montecarlo/simulator.py` | batching, stats inc., cancel, memory modes | alto |
| `montecarlo/models.py` | DatasetReference, límites, storage_mode, schema | alto |
| `montecarlo/traceability.py` | normalizar v2.1 / dataset | medio |
| `montecarlo/jobs.py` *(nuevo)* | job store async + cancel | alto |
| `lab_services.py` | límites 1e6, anti-huérfano, contexto completo | alto |
| `api.py` + `server.py` | jobs endpoints, validación | alto |
| `montecarlo.js` | presets, n_bars label, nav, progress, cost | alto |
| `shell.js` | deep-link opcional / dataset pane | medio |
| tests + docs | cobertura FASE 12 | alto |

### Alternativas

**A — Extender motor + jobs en session (recomendada)**  
Pros: un solo módulo; memoria acotada; UI poll. Contras: threading en stdlib server.

**B — Solo subir cap a 1e6 sync**  
Pros: simple. Contras: OOM, timeout, incumple requisitos.

**C — Módulo MC paralelo**  
Prohibido por el usuario.

### Recomendación
**A.** Extender `MonteCarloSimulator` + capa `jobs` en workbench; lab con modos `normal` / `technical_lab`; UI con presets y progress. Schema persistencia **2** enriquecido (campos nuevos opcionales; lectura v1 intacta).

### Plan por fases
Ver secciones 19 del prompt usuario → status en `docs/progress/montecarlo-correction-status.md`.

### Criterio de verificación
Acceptance criteria 1–30 del prompt; tests nuevos + baseline 29 verdes; N=1e6 no materializa trayectorias completas.

---

## 9. Plan correctivo resumido

1. Subir límite técnico a 1e6; default 1000; presets; confirm ≥100k.
2. Separar N vs max_persisted_trajectories (16).
3. Batching + Welford + histograma + reservoir; no guardar N SimulationResult.
4. Jobs async + progreso + cancel.
5. Renombrar n_bars + periodo/duración/timeframe.
6. `DatasetReference` obligatoria en toda corrida.
7. Botones Abrir dataset/scan/BT con enable/disable + deep-link o detalle inline.
8. Anti-huérfano en modo normal; lab técnico auto-contexto completo.
9. Resultados `summary_and_sample` para N grandes.
10. Compat schema v1; tests + benchmarks slow opcionales.

---

## 10. Respuestas a las 9 preguntas de arranque

1. **Límite 20:** validación lab + HTML `max=20`.  
2. **16 trayectorias:** NO limita N en backend; confusión UX del checkbox.  
3. **n_bars:** velas del dataset sintético 1m por escenario.  
4. **Dataset:** `make_synthetic_bars` → `WB:SYN`.  
5. **Abrir dataset:** no implementado.  
6. **Abrir scan:** abre panel genérico; disabled sin scan_id; sin deep-link.  
7. **Abrir backtest:** igual.  
8. **Capital final sin inicial visible:** capital sí es 50k; fallo de presentación/contexto/orphan/v1.  
9. **Estrategia/símbolo/venue faltantes:** hardcode + context a veces no reflejado / UI `na()` / legacy.
