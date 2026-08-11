# Terminología UI — Español visible / técnico secundario

**Regla:** nombre amigable en UI; ID técnico en subtítulo, tooltip o "Detalles".

| ID interno | Nombre visible (ES) | Subtítulo / detalle técnico |
|------------|---------------------|------------------------------|
| `scanner` | Buscar oportunidades | Alpha Scanner |
| `simulator` | Comparar mercados | Simulador multi-venue |
| `backtest` | Probar en histórico | Backtest |
| `montecarlo` | Simular escenarios | Monte Carlo |
| `strategy_live_test` | Ejecutar en prueba | Corrida en vivo · paper / testnet |
| `paper_session` | Motor paper (avanzado) | Sesión paper · step manual |
| `binance_spot` | Prueba Spot Testnet | Binance Spot Testnet |
| `binance_futures` | Prueba Futures Testnet | Binance Futures Testnet |
| `guided_lab` | Asistente paso a paso | Guided Lab |
| `strategies` | Catálogo de estrategias | IDs y guías |
| `sim_registry` | Mis simulaciones | Historial local Comparar / MC |
| `blotter` | Órdenes simuladas | Paper Blotter |
| `journal` | Registro de fills | Journal |
| `positions` | Posiciones y PnL | Posiciones |
| `paper_session` | Sesión paper | Step / kill switch |
| `risk` | Límites y kill switch | Riesgo |
| `reconciliation` | Verificar consistencia | Reconciliación book vs journal |
| `health` | Estado del sistema | Salud / modo |
| `market` | Cotizaciones en vivo | Market Data |
| `universe` | Lista de seguimiento | Universe / watchlist |
| `catalog` | Datos disponibles | Data Catalog |
| `metrics` | Última corrida (JSON) | Metrics |
| `reports` | Informes | Reports |
| `experiments` | Experimentos guardados | Experiments |
| `optimize` | Optimizar parámetros | Optimizer |
| `features` | Variables calculadas | Features |
| `export_hb` | Exportar a Hummingbot | Hummingbot Export |
| `validation` | Validación train/test | Validation Splits |
| `venues` | Mercados conectados | Venues |
| `api_explorer` | Explorar API | API Explorer |
| `diagnostics` | Diagnóstico completo | Diagnostics bundle |
| `sessions` | Sesiones locales | Sessions |
| `activity` | Actividad reciente | Activity log |
| `access_log` | Registro HTTP | Access Log |
| `backups` | Copias de seguridad | Backups |
| `ops_metrics` | Métricas del servidor | Ops Metrics |
| `settings` | Ajustes | Settings |
| `docs` | Ayuda | Help / Docs |
| `chat` | Asistente | Chat IA |
| `about` | Acerca de QuantLab | Versión y fases |

## Términos de estado (unificados)

| Estado | Cuándo |
|--------|--------|
| Preparando | Antes del primer step |
| Ejecutando | Motor / scan activo |
| Completado | Steps alcanzados o informe listo |
| Detenido | Usuario pulsó Detener |
| Advertencia | Espejo omitido, stub, sin keys |
| Error | Fallo con detalle técnico colapsable |
| Bloqueado | LIVE / kill switch |

## Banner de seguridad (único, compacto)

```text
PAPER · DATOS BINANCE · PRODUCCIÓN BLOQUEADA
```

No repetir párrafos LIVE_BLOCKED en cada panel.

## Campos de formulario (ejemplos)

| Técnico | Visible |
|---------|---------|
| `noise_bps` | Variación al precio (bps) |
| `scan_id` | ID de escaneo (avanzado) |
| `max_steps` | Pasos del motor |
| `interval_ms` | Cadencia entre pasos (ms) |
