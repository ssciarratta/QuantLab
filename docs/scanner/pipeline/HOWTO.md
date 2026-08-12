# Cómo escanear y validar (Pipeline Alpha v3)

**Regla de oro:** el ranking del scanner (**A**) no es el ranking de estrategias validadas (**B**).

## 1. Escanear candidatas (Ranking A)

- Modo **Individual** o **Pares** — por separado, sin fusionar scores.
- Tomá un **top-N fijo** (5–10). No mandes todo el universo a validar.

## 2. Validar (una estrategia por corrida)

- En el detalle de una moneda: botón **Validar** (usa la 1ª estrategia sugerida).
- O API: `POST /api/lab/validate-candidate` con `signal` + `strategy_id`.
- Cada corrida se registra **siempre** (gane o pierda) en `experiments/alpha_trials/`.

## 3. Decidir con Ranking B

- Botón **Ranking B** en Scanner, o `GET /api/lab/validated-strategies`.
- Solo entran configs con Deflated Sharpe OK.
- El ranking por PnL de ~37 estrategias en Simulador es **exploración**, no Ranking B.

## No hacer

- Probar 5 estrategias a la vez “a ver cuál pega” en la misma pasada mental.
- Operar directamente el top del scanner.
- Mezclar Sharpe dentro del score de selección.
