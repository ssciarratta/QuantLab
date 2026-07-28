# Manual — Guided Lab

Wizard paso a paso para escanear, backtestear y (opcional) paper/LIVE gated.

## Cómo abrir

1. Menú **QL** (barra inferior) → elegir el panel.
2. **Ctrl+K** (Command Palette) → escribir el nombre.
3. Presets: QL → Research / Trading Paper / Ops (abren conjuntos de paneles).

## Invariantes

- `LIVE_BLOCKED=True` por defecto: sin unlock no hay routing LIVE a venue.
- Modo **REAL** del producto = **PAPER** (fills simulados), no órdenes en exchange de producción.
- Este panel **no** garantiza rentabilidad ni es asesoramiento financiero.

## Para qué sirve

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
