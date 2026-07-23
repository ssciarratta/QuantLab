# QuantLab — Lessons Learned

**Fase:** 1 — Diseño de arquitectura  
**Fecha de cierre:** 2026-07-23  
**Estado:** Pendiente de revisión externa

---

## Qué salió bien

1. **Metodología por fases funcionó.** Separar fundación (Fase 0) de diseño (Fase 1) permitió construir sobre bases sólidas sin deuda técnica prematura.

2. **Reglas permanentes clarificaron el rol.** Asumir múltiples roles (CTO, Quant Researcher, Data Engineer) y el filtro de 6 preguntas orientó cada decisión hacia modularidad, reproducibilidad y escalabilidad.

3. **Interface-first desde el día uno.** Definir 10 interfaces conceptuales antes de escribir código evita el acoplamiento que suele aparecer en proyectos cuantitativos ad-hoc.

4. **Separación investigación/ejecución.** La frontera QuantLab → ExecutionEngine → Hummingbot reduce riesgo operacional y permite investigar sin infraestructura live.

5. **Roadmap incremental de 14 fases.** Cada fase tiene objetivo, dependencias, entregables y criterio de cierre. Esto hace el proyecto gestionable y revisable.

6. **Documentación dual.** Arquitectura.md (técnica) + Arquitectura_Explicada.txt (accesible) permite revisión tanto por arquitectos como por el director del proyecto.

7. **Future Improvements registradas.** 15 mejoras identificadas y documentadas sin implementarlas, cumpliendo la regla de no avanzar sin autorización.

---

## Qué salió mal

1. **Autenticación GitHub tomó varios intentos.** Los códigos de device login expiraron por timeout. Lección: este paso requiere acción inmediata del usuario; no puede ser 100% automatizado.

2. **Complejidad del árbol de proyecto puede intimidar.** 9 módulos bajo `src/quantlab/` con múltiples subcarpetas es correcto arquitectónicamente pero puede generar fricción al implementar Fase 2 si no se crean módulos progresivamente.

3. **Algunas decisiones quedaron con recomendación pero sin resolución.** 8 dudas abiertas en `learning/dudas.txt` — algunas deberían resolverse antes de Fase 5 (backtester).

---

## Qué aprendimos

1. **Un laboratorio cuantitativo no es un bot.** El 80% del valor está en la infraestructura de datos, simulación y reproducibilidad, no en la estrategia en sí.

2. **La reproducibilidad científica requiere diseño, no disciplina.** Snapshots inmutables, versionado de config, seeds y registro de experimentos deben ser parte de la arquitectura, no convenciones opcionales.

3. **Progressive complexity es clave.** Diseñar interfaces para escala futura (simulaciones distribuidas, cloud storage) sin implementarlas ahora evita over-engineering y reescrituras.

4. **El catálogo de datos es infraestructura crítica.** Sin un catálogo robusto (DuckDB), los datasets se vuelven inmanejables rápidamente con 100+ activos.

5. **Las interfaces son el activo más valioso del proyecto.** Invertir tiempo en definirlas bien en Fase 1 ahorra semanas de refactoring en Fases 5-11.

---

## Qué deberíamos hacer diferente

1. **Resolver dudas bloqueantes antes de Fase 5.** DUD-002 (slippage model), DUD-004 (OHLCV vs order book) y DUD-005 (granularidad temporal) deben cerrarse con input del revisor cuantitativo.

2. **No crear carpetas vacías en Fase 2.** Implementar solo lo necesario por fase; el árbol completo es un mapa, no un mandato de crear todo de una vez.

3. **Definir "golden runs" para el backtester desde Fase 5.** Tests con resultados conocidos que validen correctness del simulador, no solo que "corre sin error".

4. **Establecer CI temprano (Fase 2-3).** Aunque sea GitHub Actions básico con pytest, evita regresiones desde el inicio.

---

## Riesgos futuros

| Riesgo | Fase de materialización | Severidad |
|--------|-------------------------|-----------|
| Backtester con bugs silenciosos | Fase 5 | Crítica |
| RAM insuficiente para Monte Carlo masivo | Fase 8 | Alta |
| Scope creep en Alpha Scanner | Fase 10 | Media |
| API de Hummingbot cambia | Fase 13 | Media |
| Schema de datos evoluciona sin migración | Fase 3+ | Media |
| Deuda de tests acumulada | Fase 2+ | Alta |
| Pérdida de datos locales | Continuo | Alta |
| Over-engineering por ambición arquitectónica | Fase 2-4 | Media |

---

*Generado al cierre de Fase 1. Se actualizará al cierre de cada fase subsiguiente.*
