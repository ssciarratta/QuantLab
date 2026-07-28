# Interpretación de resultados Monte Carlo

- **Media de los escenarios simulados** ≠ predicción ni “resultado esperado” de mercado.
- Pocos escenarios (N&lt;100): solo exploración cualitativa.
- N tip de lab: default ~1000; rango **2…1_000_000** (batching). Confirmá runs ≥100k.
- CI de la media se estrecha con √N; no implica que un escenario futuro caiga ahí.
- Mejor/peor escenario: extremos de la muestra simulada, no VaR regulatorio.
- Trayectorias persistidas (~16) son muestra visual; **no** son el tamaño N.
- Guía: [`montecarlo-guide.md`](montecarlo-guide.md) · manual: [`../manuales/04-montecarlo.md`](../manuales/04-montecarlo.md)
