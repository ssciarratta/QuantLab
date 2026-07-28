"""Genera docs/manuales/*.md — uso único / regenerable."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs" / "manuales"
ROOT.mkdir(parents=True, exist_ok=True)

INVARIANTES = """## Invariantes

- `LIVE_BLOCKED=True` por defecto: sin unlock no hay routing LIVE a venue.
- Modo **REAL** del producto = **PAPER** (fills simulados), no órdenes en exchange de producción.
- Este panel **no** garantiza rentabilidad ni es asesoramiento financiero.
"""

COMMON_OPEN = """## Cómo abrir

1. Menú **QL** (barra inferior) → elegir el panel.
2. **Ctrl+K** (Command Palette) → escribir el nombre.
3. Presets: QL → Research / Trading Paper / Ops (abren conjuntos de paneles).
"""


def write(name: str, body: str) -> None:
    path = ROOT / name
    path.write_text(body.strip() + "\n", encoding="utf-8")
    print("wrote", path.relative_to(ROOT.parent.parent))


def main() -> None:
    write(
        "00-INDICE.md",
        """# Manuales de uso — QuantLab Workbench

**Versión tip:** 1.01.0 · **Actualizado:** 2026-07-27
**UI:** http://127.0.0.1:8765 · Help: QL → Help / Docs → carpeta `manuales/`

Este índice lista **todas las funciones de panel** del Workbench. Cada archivo es un manual operativo (cómo usar, límites, invariantes).

## Arranque rápido

Ver también: [`../GUIA_COMPLETA_QUANTLAB.md`](../GUIA_COMPLETA_QUANTLAB.md) · [`../ops/WORKBENCH_1CLICK.md`](../ops/WORKBENCH_1CLICK.md)

```bash
uv sync --extra dev
uv run quantlab-workbench
# browser → http://127.0.0.1:8765
```

## Invariantes globales

- `LIVE_BLOCKED` · `REAL = PAPER` · secrets nunca en git/logs/chat
- Chat IA: safe-mode (no envía órdenes)
- Alpha Scanner / Monte Carlo / Backtest: investigación; no predicen el futuro

## Manuales por panel

### Laboratorio / investigación

| Manual | Panel |
|--------|-------|
| [01-guided-lab.md](01-guided-lab.md) | Guided Lab |
| [02-backtest.md](02-backtest.md) | Backtest |
| [03-alpha-scanner.md](03-alpha-scanner.md) | Alpha Scanner |
| [04-montecarlo.md](04-montecarlo.md) | Monte Carlo |
| [05-validation.md](05-validation.md) | Validation Splits |
| [06-optimizer.md](06-optimizer.md) | Optimizer |
| [07-features.md](07-features.md) | Features |
| [08-export-hb.md](08-export-hb.md) | Hummingbot Export |
| [09-metrics.md](09-metrics.md) | Metrics / Último |
| [10-reports.md](10-reports.md) | Reports |
| [11-experiments.md](11-experiments.md) | Experiments |

### Datos / mercado

| Manual | Panel |
|--------|-------|
| [12-health.md](12-health.md) | Salud / Modo |
| [13-market.md](13-market.md) | Market Data |
| [14-universe.md](14-universe.md) | Universe |
| [15-catalog.md](15-catalog.md) | Data Catalog |

### Paper trading

| Manual | Panel |
|--------|-------|
| [16-blotter.md](16-blotter.md) | Paper Blotter |
| [17-journal.md](17-journal.md) | Journal |
| [18-paper-session.md](18-paper-session.md) | Sesión Paper |
| [19-positions.md](19-positions.md) | Posiciones |
| [20-risk.md](20-risk.md) | Riesgo |
| [21-reconciliation.md](21-reconciliation.md) | Reconciliación |

### Ops / soporte

| Manual | Panel |
|--------|-------|
| [22-venues.md](22-venues.md) | Venues |
| [23-api-explorer.md](23-api-explorer.md) | API Explorer |
| [24-diagnostics.md](24-diagnostics.md) | Diagnostics |
| [25-docs.md](25-docs.md) | Help / Docs |
| [26-chat.md](26-chat.md) | Chat IA |
| [27-settings.md](27-settings.md) | Settings |
| [28-sessions.md](28-sessions.md) | Sessions |
| [29-activity.md](29-activity.md) | Activity |
| [30-access-log.md](30-access-log.md) | Access Log |
| [31-backups.md](31-backups.md) | Backups |
| [32-ops-metrics.md](32-ops-metrics.md) | Ops Metrics |

### Shell / navegación

| Manual | Tema |
|--------|------|
| [33-shell-navegacion.md](33-shell-navegacion.md) | Menú QL, presets, ventanas, deep-links |
| [34-about.md](34-about.md) | About / versión |

## Guías técnicas (subdirs Help)

- `docs/montecarlo/*.md` — Monte Carlo (métodos, interpretación, corrección)
- `docs/scanner/*.md` — Alpha Scanner
- `docs/ops/*.md` — Runbooks ops
""",
    )

    specs: list[tuple[str, str, str, str]] = [
        (
            "01-guided-lab.md",
            "Guided Lab",
            "Wizard paso a paso para escanear, backtestear y (opcional) paper/LIVE gated.",
            """## Para qué sirve

Flujo guiado recomendado para principiantes y demos:

1. Elegir venue / fuente de datos (sintético, Binance MD público, A3, etc.).
2. Correr **Alpha Scanner** (ranking).
3. Correr **Backtest** sobre candidatos.
4. Ver capital inicial/final, fees (VIP0 Spot tip: 10 bps/lado) y métricas.
5. Opcional: deep-link a **Monte Carlo** con `scan_id` / `backtest_id`.
6. Opcional: unlock LIVE + demo Binance (sim local o testnet opt-in).

## Cómo usar (flujo típico)

1. Abrí **Guided Lab**.
2. Revisá el banner: modo PAPER / LIVE_BLOCKED.
3. Sección datos: símbolo(s), intervalo, límite de velas.
4. Perfil de scanner (default `legacy_v1`) + walk-forward ON (Binance).
5. **Ejecutar** scan → anotá `scan_id`.
6. **Backtest** → anotá `backtest_id` / report.
7. Botón **→ Monte Carlo** (si está visible) para estrés con el mismo id.

## LIVE / demo (gated)

- Unlock solo con `QUANTLAB_LIVE_USER` + `QUANTLAB_LIVE_PASSWORD` en `.env` local.
- Testnet: `QUANTLAB_DEMO_USE_TESTNET=1` + `BINANCE_DEMO_*`.
- Sin unlock: el camino LIVE no rutea a venue de producción.

## Límites

- No es bot autónomo: cada paso requiere acción del operador.
- Walk-forward reduce sesgo in-sample; **no** garantiza OOS.
- Detalle técnico: `docs/scanner/alpha-scanner-guide.md` · fases F99–F111.
""",
        ),
        (
            "02-backtest.md",
            "Backtest",
            "Correr un backtest de laboratorio sobre dataset sintético o referenciado.",
            """## Para qué sirve

Evaluar una estrategia en histórico lab (métricas, equity, fills, fees).

## Cómo usar

1. Abrí **Backtest**.
2. Completá parámetros (estrategia, barras, capital inicial, fee por lado si aplica).
3. Ejecutá y esperá el resultado.
4. Revisá Metrics / Reports para el historial de la sesión.
5. Botón **→ Monte Carlo** (cuando hay `report_id`) para estrés.

## Lectura de resultados

- Capital inicial / final y fees totales ayudan a validar el modelo de costos.
- Un backtest bueno en lab **no** implica edge en vivo.

## Relacionado

- Guided Lab (flujo guiado)
- Reports / Metrics
- Monte Carlo (mode `normal` exige `backtest_id`)
""",
        ),
        (
            "03-alpha-scanner.md",
            "Alpha Scanner",
            "Ranking de mercados según perfil de scoring (investigación).",
            """## Para qué sirve

Ordenar candidatos (sintéticos WB:A/B/C o universo Binance MD) por score compuesto.

## Cómo usar

1. Abrí **Alpha Scanner**.
2. Elegí perfil (`legacy_v1` default, momentum, mean_reversion, …).
3. Ejecutá **Escanear**.
4. Revisá ranking, exclusiones y `scan_id`.
5. Continuá en Guided Lab / Backtest / Monte Carlo.

## Perfiles (resumen)

- `legacy_v1`: 0.35 vol + 0.35 volume + 0.30 liquidity (min-max)
- Otros: ver `docs/scanner/alpha-scanner-guide.md`

## Walk-forward (pipeline Binance)

En Guided Lab / API pipeline: rank en tramo inicial, BT en tramo posterior (`rank_fraction` default 0.70).

## Límites

- No afirma rentabilidad.
- Funding/OI ausentes → `None` (nunca 0 fingido).
""",
        ),
        (
            "04-montecarlo.md",
            "Monte Carlo",
            "Estrés de equity bajo shocks de precio (dispersión, no predicción).",
            """## Para qué sirve

Medir dispersión de equities finales bajo ruido OHLC en un dataset (sintético o ligado a BT/scan).

## Parámetros clave

| UI | Código | Notas |
|----|--------|-------|
| Escenarios | `n_scenarios` | **2 … 1_000_000** (default tip: 1000) |
| Velas por escenario | `n_bars` | Velas 1m sintéticas (`WB:SYN`) usadas **por** escenario |
| Ruido bps | `noise_bps` | 10 bps = 0.10% |
| Seed | `seed` | Reproducibilidad |
| Confirmación | `confirm_large` | Requerida si N ≥ 100k |

**Importante:** el tope visual de trayectorias persistidas (~16) **no** limita N; solo cuántas paths se guardan.

## Modos

- `technical_lab`: dataset sintético demo.
- `normal`: exige `backtest_id` (ligazón a un BT real de sesión).

## Cómo usar

1. Abrí **Monte Carlo** (o deep-link desde Reports / Backtest / Guided Lab).
2. Revisá prefill (`backtest_id` / `scan_id`) si vino de otro panel.
3. Elegí N (presets: 100 / 1k / 10k / 100k / 1M).
4. Ejecutá; jobs grandes corren async (cancelable).
5. Leé media, desvío, histograma, IC de la **media** (no banda de un solo path).
6. Botones para abrir Reports / Guided Lab enfocando el id.

## Capital y fees

Mostrá capital inicial/final y fee por lado (lab tip VIP0 Spot 10 bps) para validar costos.

## Relacionado

- Guía: `docs/montecarlo/montecarlo-guide.md`
- Corrección: `docs/progress/montecarlo-correction-status.md`
""",
        ),
        (
            "05-validation.md",
            "Validation Splits",
            "Particiones train/validation/test (o walk-forward splits) para experimentos de research.",
            """## Para qué sirve

Definir y revisar cortes temporales de datos para evitar evaluar siempre in-sample.

## Cómo usar

1. Abrí **Validation Splits**.
2. Refrescá / generá splits según el flujo del panel.
3. Usá los ids/rangos al configurar backtests o experimentos.

## Límites

- Es herramienta de laboratorio; no sustituye validación out-of-sample real de producción.
""",
        ),
        (
            "06-optimizer.md",
            "Optimizer",
            "Búsqueda de parámetros de estrategia en el lab (grid/search acotado).",
            """## Para qué sirve

Explorar combinaciones de hiperparámetros y comparar métricas en sesión.

## Cómo usar

1. Abrí **Optimizer**.
2. Definí rango/grid y métrica objetivo.
3. Ejecutá y revisá ranking de candidatos.
4. Exportá / llevá el mejor set a Backtest o Experiments.

## Riesgos

- Overfitting: optimizar demasiado sobre el mismo sample.
- Preferí Validation Splits / walk-forward antes de confiar en un óptimo.
""",
        ),
        (
            "07-features.md",
            "Features",
            "Exploración / cómputo de features de research en el Workbench.",
            """## Para qué sirve

Inspeccionar transformaciones y series derivadas usadas por estrategias o scanners.

## Cómo usar

1. Abrí **Features**.
2. Elegí dataset / símbolo / ventana.
3. Generá o listá features y revisá salida.

## Límites

- Features lab no implican señal operable en vivo.
""",
        ),
        (
            "08-export-hb.md",
            "Hummingbot Export",
            "Exportar configuración / artefactos compatibles con flujo Hummingbot (lab).",
            """## Para qué sirve

Generar un paquete de exportación para llevar parámetros del lab a un entorno HB externo.

## Cómo usar

1. Abrí **Hummingbot Export**.
2. Completá los campos requeridos.
3. Generá / descargá el artefacto.
4. Revisá el contenido antes de usarlo fuera de QuantLab.

## Límites

- QuantLab **no** rutea órdenes HB automáticamente.
- LIVE sigue bloqueado salvo unlock explícito en el producto.
""",
        ),
        (
            "09-metrics.md",
            "Metrics / Último",
            "Vista del último resultado de lab (métricas agregadas de la sesión).",
            """## Para qué sirve

Consultar rápido el último backtest / run sin abrir el report completo.

## Cómo usar

1. Abrí **Metrics / Último**.
2. Pulsá refresh tras un Backtest / Guided Lab.
3. Contrastá con **Reports** para el historial.
""",
        ),
        (
            "10-reports.md",
            "Reports",
            "Historial de reportes de backtest / lab de la sesión.",
            """## Para qué sirve

Listar, abrir y enfocar reportes por `report_id`.

## Cómo usar

1. Abrí **Reports** y refrescá.
2. Seleccioná un reporte para detalle.
3. **→ Monte Carlo** abre MC en modo normal con ese `report_id` / backtest ligado.
4. Deep-link inverso: desde MC podés volver a Reports enfocando el id.

## Tips

- Tras F5, la sesión puede reiniciar; persistencia depende del store de sesión.
""",
        ),
        (
            "11-experiments.md",
            "Experiments",
            "Registro liviano de experimentos de research en la sesión.",
            """## Para qué sirve

Agrupar corridas (scan/BT/opt) con notas para comparación.

## Cómo usar

1. Abrí **Experiments**.
2. Creá / listá experimentos.
3. Vinculá ids de runs cuando el panel lo permita.
""",
        ),
        (
            "12-health.md",
            "Salud / Modo",
            "Estado del Workbench: versión, modo (tester/paper), LIVE_BLOCKED.",
            """## Para qué sirve

Verificar que el laboratorio está sano antes de operar paneles.

## Cómo usar

1. Abrí **Salud / Modo**.
2. Confirmá `LIVE_BLOCKED` y el modo (PAPER = REAL del producto).
3. Si el banner superior no coincide, refrescá este panel.
""",
        ),
        (
            "13-market.md",
            "Market Data",
            "Snapshot de market data del broker / fuente activa (read-oriented).",
            """## Para qué sirve

Inspeccionar precio/book o snapshot lab del símbolo actual.

## Cómo usar

1. Abrí **Market Data**.
2. Elegí símbolo / refrescá.
3. Usá la info para paper blotter o diagnóstico; no es terminal de trading LIVE.
""",
        ),
        (
            "14-universe.md",
            "Universe",
            "Universo de símbolos / watchlist del lab.",
            """## Para qué sirve

Ver y gestionar el conjunto de mercados disponibles para scan/MD.

## Cómo usar

1. Abrí **Universe**.
2. Revisá lista / import-export si está habilitado (JSON watchlist).
3. Alineá el universo con Scanner o Guided Lab.
""",
        ),
        (
            "15-catalog.md",
            "Data Catalog",
            "Catálogo de datasets / artefactos de datos del lab.",
            """## Para qué sirve

Descubrir qué datasets están registrados y metadatos básicos.

## Cómo usar

1. Abrí **Data Catalog**.
2. Refrescá y explorá entradas.
3. Usá referencias al configurar BT / features.
""",
        ),
        (
            "16-blotter.md",
            "Paper Blotter",
            "Enviar órdenes **paper** manuales (fills simulados).",
            """## Para qué sirve

Probar ticket de orden sin venue real.

## Cómo usar

1. Abrí **Paper Blotter**.
2. Completá símbolo, lado, qty, tipo.
3. Enviá → el fill aparece en **Journal**.
4. Revisá **Posiciones** / **Riesgo**.

## Límites

- No es ejecución en Binance prod.
- Con LIVE unlock, otros paneles pueden usar demo; el blotter paper sigue siendo simulación local salvo flujos demo documentados.
""",
        ),
        (
            "17-journal.md",
            "Journal",
            "Libro de fills paper (autoritativo en sesión).",
            """## Para qué sirve

Auditar qué se operó en paper (incl. mirrors demo cuando aplica).

## Cómo usar

1. Abrí **Journal**.
2. Refrescá tras blotter / paper session / Guided Lab paper.
3. Contrastá con **Reconciliación** si hay divergencias.
""",
        ),
        (
            "18-paper-session.md",
            "Sesión Paper",
            "Runner de estrategia automática en paper (lab).",
            """## Para qué sirve

Dejar una estrategia corriendo contra fills simulados en la sesión.

## Cómo usar

1. Abrí **Sesión Paper**.
2. Elegí estrategia / parámetros.
3. Start / stop según controles del panel.
4. Monitoreá Journal, Posiciones y Riesgo.

## Límites

- No arranca routing LIVE por sí solo.
""",
        ),
        (
            "19-positions.md",
            "Posiciones",
            "Posiciones paper abiertas / agregadas.",
            """## Para qué sirve

Ver exposición actual del book paper.

## Cómo usar

1. Abrí **Posiciones**.
2. Refrescá tras fills.
3. Si no cuadra con Journal → **Reconciliación**.
""",
        ),
        (
            "20-risk.md",
            "Riesgo",
            "Límites y métricas de riesgo del book paper / sesión.",
            """## Para qué sirve

Vigilar notional, drawdown lab, kill/limits cuando estén activos.

## Cómo usar

1. Abrí **Riesgo**.
2. Revisá umbrales y estado.
3. Ante alertas, pausá Sesión Paper y revisá Journal.
""",
        ),
        (
            "21-reconciliation.md",
            "Reconciliación",
            "Estado de reconciliación paper (journal vs book).",
            """## Para qué sirve

Detectar inconsistencias post-rebuild o tras muchos fills.

## Cómo usar

1. Abrí **Reconciliación**.
2. Refrescá status.
3. Si hay mismatch, no asumas venue real: corregí paper / rehydrate según docs F88–F91.
""",
        ),
        (
            "22-venues.md",
            "Venues",
            "Registry read-only de brokers / venues conocidos.",
            """## Para qué sirve

Ver qué plugins/venues están registrados y su estado (paper, demo, MD).

## Cómo usar

1. Abrí **Venues**.
2. Refrescá la tabla.
3. No edita credenciales secretas aquí.
""",
        ),
        (
            "23-api-explorer.md",
            "API Explorer",
            "Explorador OpenAPI read-only del Workbench.",
            """## Para qué sirve

Descubrir endpoints documentados sin Postman.

## Cómo usar

1. Abrí **API Explorer**.
2. Navegá paths / schemas.
3. Las llamadas destructivas / LIVE siguen fail-closed en el servidor.
""",
        ),
        (
            "24-diagnostics.md",
            "Diagnostics",
            "Snapshot de diagnóstico + descarga de support bundle.",
            """## Para qué sirve

Empaquetar estado del sistema para soporte (F95–F97).

## Cómo usar

1. Abrí **Diagnostics**.
2. Generá snapshot.
3. Descargá support ZIP si necesitás compartir (sin pegar secrets).
""",
        ),
        (
            "25-docs.md",
            "Help / Docs",
            "Navegador de markdown allowlist bajo `docs/`.",
            """## Para qué sirve

Leer guías e instructivos **dentro** del Workbench.

## Carpetas visibles

- `docs/*.md` (raíz)
- `docs/ops/*.md`
- `docs/manuales/*.md` ← estos manuales
- `docs/montecarlo/*.md`
- `docs/scanner/*.md`

## Cómo usar

1. Abrí **Help / Docs**.
2. Filtrá / elegí un archivo.
3. Empezá por `manuales/00-INDICE.md` o `GUIA_COMPLETA_QUANTLAB.md`.

## Seguridad

- Path traversal fail-closed.
- No lista `docs/audit/` ni otros subdirs no allowlist.
""",
        ),
        (
            "26-chat.md",
            "Chat IA",
            "Asistente en safe-mode (guía / lectura; **no** envía órdenes).",
            """## Para qué sirve

Explicar paneles, interpretar métricas, buscar docs (`search_docs`).

## Cómo usar

1. Abrí **Chat IA**.
2. Preguntá en lenguaje natural.
3. Si el modelo sugiere una acción LIVE/orden: **ignorala** — el backend no debe ejecutar órdenes vía chat.

## Límites

- Requiere provider/API key según Settings / env.
- Memoria / instructor: ver fases F47 / F112.
- Nunca pegues secrets en el chat.
""",
        ),
        (
            "27-settings.md",
            "Settings",
            "Preferencias de UI: tema, locale, timezone, notificaciones, escala de fuente.",
            """## Para qué sirve

Personalizar el escritorio sin tocar código.

## Cómo usar

1. Abrí **Settings**.
2. Cambiá tema / idioma / notificaciones desktop / sonido.
3. Guardá; el status bar y toasts se actualizan.
""",
        ),
        (
            "28-sessions.md",
            "Sessions",
            "Gestión de sesiones Workbench (switch / listado).",
            """## Para qué sirve

Cambiar de sesión de trabajo y ver `session_id` activo (banner).

## Cómo usar

1. Abrí **Sessions**.
2. Seleccioná / creá según controles.
3. Tras switch, refrescá Journal / Reports (datos de sesión).
""",
        ),
        (
            "29-activity.md",
            "Activity",
            "Log de actividad de la sesión (acciones UI / lab).",
            """## Para qué sirve

Auditar qué se hizo en la sesión actual.

## Cómo usar

1. Abrí **Activity**.
2. Refrescá y filtrá si el panel lo permite.
""",
        ),
        (
            "30-access-log.md",
            "Access Log",
            "Registro de accesos HTTP / auditoría de acceso al Workbench.",
            """## Para qué sirve

Revisar quién/qué tocó el loopback (ops / seguridad).

## Cómo usar

1. Abrí **Access Log**.
2. Refrescá entradas recientes.
""",
        ),
        (
            "31-backups.md",
            "Backups",
            "Listado / disparo de backups de sesión o store (ops).",
            """## Para qué sirve

Respaldar estado antes de cambios estructurales.

## Cómo usar

1. Abrí **Backups**.
2. Listá backups existentes.
3. Creá uno nuevo si el panel lo permite; verificá ruta en disco.
""",
        ),
        (
            "32-ops-metrics.md",
            "Ops Metrics",
            "Métricas operativas del proceso Workbench.",
            """## Para qué sirve

Observabilidad liviana (latencias, contadores) para ops.

## Cómo usar

1. Abrí **Ops Metrics**.
2. Refrescá y anotá anomalías.
3. Complementá con Diagnostics si necesitás bundle.
""",
        ),
        (
            "33-shell-navegacion.md",
            "Shell, menú QL y navegación",
            "Escritorio flotante del Workbench.",
            """## Layout

- Banner superior: modo, LIVE_BLOCKED, session, avisos
- Escritorio: ventanas (paneles)
- Barra inferior: status + **QL**

## Abrir paneles

- Menú **QL**
- **Ctrl+K** Command Palette
- Atajos numéricos (orden del shell) cuando estén documentados en About/Settings
- Presets Research / Trading Paper / Ops

## Ventanas

- Snap a bordes, minimize/restore all, cascade/tile, bring to front/back, maximize (F82–F86)
- Resize por bordes; tooltips en controles

## Deep-links (QLNav)

Flujos conectados:

- Reports / Backtest / Guided Lab → **Monte Carlo** (prefill ids)
- Monte Carlo → Reports / Guided Lab enfocando id

Implementación: `static/js/nav.js` + `QLShell.open(pane, opts)`.
""",
        ),
        (
            "34-about.md",
            "About",
            "Diálogo de versión / build / invariantes.",
            """## Para qué sirve

Confirmar versión tip (`pyproject` / about API) y recordatorios de seguridad.

## Cómo usar

1. QL → **About** (o Command Palette).
2. Verificá versión vs `RESUMEN_PROYECTO.txt`.
""",
        ),
    ]

    for filename, title, blurb, extra in specs:
        body = f"# Manual — {title}\n\n{blurb}\n\n{COMMON_OPEN}\n{INVARIANTES}\n{extra}"
        write(filename, body)

    print("total", len(list(ROOT.glob("*.md"))))


if __name__ == "__main__":
    main()
