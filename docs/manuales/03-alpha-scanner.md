# Manual — Alpha Scanner

Ranking de **candidatas** (monedas o pares) para investigación.  
**No** es rentabilidad. `LIVE_BLOCKED=True`. No hay órdenes reales.

**Guía larga:** [`../scanner/alpha-scanner-guide.md`](../scanner/alpha-scanner-guide.md)  
**Pipeline validación:** [`../scanner/pipeline/HOWTO.md`](../scanner/pipeline/HOWTO.md)  
**ML:** [`../scanner/ml/HOWTO.md`](../scanner/ml/HOWTO.md)

## Cómo abrir

1. Menú **QL** → **Alpha Scanner**.
2. **Ctrl+K** → `scanner`.
3. URL: `http://127.0.0.1:8765`

## Flujo de trabajo (el que importa)

```
1. Escanear  →  Ranking A (candidatas)
2. Validar   →  1 estrategia por corrida (alimenta el ML)
3. Ranking B →  todas las evaluaciones (aprobadas, rechazadas, fallidas)
```

El ranking del scanner **no** se opera. Se usa para elegir qué validar.

---

## 1. Modo Individual (monedas)

1. **Modo:** Individual.
2. Mercado: Spot o Futures. Venue: Binance (u otros).
3. Perfil (trend / momentum / …) y velas.
4. **ML ranking** queda **marcado** (default): el GBM puntúa las mismas candidatas.
5. **Escanear**.
6. Clic en una fila → **Validar** (1 estrategia sugerida).

Cada **Validar** se guarda en `experiments/alpha_trials/` (gane o pierda). El ML entrena un **candidato**; solo promociona si el AUC no empeora (el sintético de arranque se reemplaza con datos reales).

---

## 2. Modo Pares (pairwise)

1. **Modo:** Pares.
2. Mercado: Spot **o** Futures (mismo venue, no mezclar).
3. Detectores: correlación, lag, cointegración, spread z.
4. Velas: mínimo **120** (mejor 720+).
5. Opcional: **Validación OOS** (valida el top con DSR).
6. **Escanear** → tabla de pares + estrategia sugerida → **Sim** o **Validar**.

---

## 3. ML (automático)

| Qué | Comportamiento |
|-----|----------------|
| Primer escaneo | Si no hay modelo, se crea uno **sintético** de arranque |
| Cada Validar / pipeline / OOS pares | El trial entra al ledger |
| Cada 5 trials (con ≥30 filas y ≥8 positivas) | Entrena un **candidato**; promociona solo si AUC ≥ activo |
| Checkbox **ML ranking** | Default ON. Badge «ML sintético» si aún no hay datos reales |

El score ML es **una señal más** (`ml_ranking`), no reemplaza el scanner ni el Ranking B.

Entrenar a mano (opcional):

```bash
uv run python scripts/alpha_ml_bootstrap.py --synthetic --activate
uv run python scripts/alpha_ml_bootstrap.py --trials data/runtime/workbench/<sesión>/experiments --activate
```

---

## 4. Ranking A vs Ranking B

| Ranking | Qué es | Para qué |
|---------|--------|----------|
| **A** | Scanner (features / pares / ML) | Elegir qué validar (top 5–10) |
| **B** | Todas las validaciones (DSR) | Ver aprobadas **y** rechazadas |

Botón **Ranking B** en el Scanner.

---

## Kronos (opcional)

Forecast de horizonte **dentro** del ranking individual. Extra `kronos`.  
Detalle: `docs/scanner/kronos-inside-scanner.md`

## Perfiles

- `legacy_v1`: 0.35 vol + 0.35 volume + 0.30 liquidity
- Otros: `docs/scanner/alpha-scanner-guide.md`

## Límites

- Score ≠ PnL. LIVE bloqueado.
- Una candidata × una estrategia por validación (no “probar 5 a la vez”).
- No fusionar scores individual + pares en un único número.
