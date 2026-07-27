# Strategy Expander — QuantLab

Generá o promové estrategias del espectro QuantLab (familias F115).

## Cuándo usar
- Usuario pide nueva estrategia, promover stub → runnable, o ampliar una familia.
- Tras Architecture Review si el cambio toca >5 archivos / contratos.

## Invariantes (no negociables)
1. `LIVE_BLOCKED=True` — sin order routing a producción Binance.
2. **binance-ready** = ejecutable en backtest + paper + **demo/testnet post-unlock** con el mismo `strategy_id`.
3. Stubs (`runnable=false`) listan en catálogo pero `build_strategy` / lab / paper fallan con `ValidationError` clara.
4. UI Guided Lab / Paper / Backtest cargan desde `GET /api/lab/strategies` (no hardcode).

## Archivos canónicos
- Catálogo: `src/quantlab/workbench/strategy_catalog.py`
- Señales bar: `src/quantlab/research/strategies/classic_bar.py`
- MM variantes: `src/quantlab/research/strategies/mm_spectrum.py`
- Tests: `tests/unit/workbench/test_strategy_catalog_f27.py` (+ unit propio si lógica nueva)

## Checklist por estrategia nueva **runnable**
1. Definir `StrategyMeta` (family, tags, default_params, `runnable=True`).
2. Implementar señal en `ClassicBarStrategy` **o** clase MM/event dedicada.
3. Cablear `factory` en `build_strategy`.
4. Alias opcionales en `_ALIASES`.
5. Test: `build_strategy` + `run_lab_backtest` smoke (≥24–40 bars).
6. Verificar que aparece en API con `binance_ready: true`.

## Checklist por **stub**
1. `StrategyMeta(..., runnable=False, factory="stub")`.
2. Test: `build_strategy` raises match `stub`.
3. No agregar a Guided Lab runnable filter (ya filtra `runnable !== false`).

## Promoción stub → runnable
1. Preferí proxy bar-honest (documentar límites) antes que mentir L2/opciones/multi-venue.
2. Implementar señal en `classic_bar.py` + `signal_kind`.
3. `runnable=True`, `factory="classic"` (o mm), tags `proxy` si aplica.
4. Test smoke `run_lab_backtest`.
5. Actualizar `RESUMEN_PROYECTO.txt`.

## Stubs que deben quedarse (hasta datos reales)
- multi-venue arb · funding · basis
- opciones con greeks (delta/gamma/covered) excepto `volatility_trading` proxy
- `queue_position` (L2)
- `sector_rotation` / `risk_parity` / `asset_allocation` (universo)

## Familias
`demo` · `trend` · `momentum` · `mean_reversion` · `market_making` · `stats` · `ml` · `multi_asset` · `microstructure` · `arbitrage` · `options`
