# Manual — Monte Carlo

Estrés de equity bajo shocks (dispersión, **no** predicción).

## Cómo abrir

1. Menú **QL** → **Monte Carlo**
2. Desde **Simulador**: botón **Monte Carlo** (único; lleva `sim_context`)
3. Desde **Backtest** / Reports / Guided Lab (deep-link)
4. **Mis simulaciones** → Reabrir / Memo

## Invariantes

- `LIVE_BLOCKED=True` · REAL = PAPER
- No garantiza rentabilidad ni es asesoramiento

## Ligado al Simulador (`sim_linked`)

Cuando abrís desde el Simulador:

- Confirmá moneda / estrategia / params
- El motor usa **velas históricas** del par + la estrategia del Sim
- `n_bars` = velas **por escenario** (tope MC; no replica todo el período Comparar)

## Modos

| Mode | Uso |
|------|-----|
| `sim_linked` | Con `sim_context` del Sim (preferido) |
| `normal` | Exige `backtest_id` |
| `technical_lab` | Demo sintético |

## Parámetros

| UI | Notas |
|----|--------|
| Escenarios N | 2 … 1e6 (async si grande; **Stop**/Cancel) |
| Velas/escenario | No confundir con N escenarios |
| Ruido bps / seed | Reproducibilidad |
| Trayectorias | Tope visual ~16 paths; **no** limita N |

## Stop

Corridas concurrentes: coordinador global (Esperar / Cortar / Stop en barra).

## Relacionado

- `docs/montecarlo/montecarlo-guide.md`
- Manual Simulador: `35-simulador.md`
- Mis simulaciones (registro + memo)
