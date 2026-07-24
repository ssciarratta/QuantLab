# QuantLab — Lessons Learned

---

## Fase 2 — Core + Infraestructura (Post-Auditoría)

**Fecha de cierre:** 2026-07-23
**Estado:** EN CORRECCIÓN — esperando segunda revisión

### Qué salió bien

1. **Auditoría como fuente de verdad.** Aplicar los hallazgos de GPT de forma sistemática produjo una implementación más robusta que si se hubiera hecho sin revisión.

2. **Inmutabilidad profunda desde el día uno.** `MappingProxyType` + `freeze_json()` evitan una clase entera de bugs donde datos compartidos mutan inesperadamente.

3. **Strategy Protocol con on_event().** El contrato genérico basado en eventos es más extensible que `on_bar()`. Soportará trades, book updates sin cambios.

4. **Validación OrderIntent por tipo.** Impedir estados inválidos en construcción evita bugs downstream en el simulador.

5. **Tests de comportamiento vs cobertura.** 157 tests focalizados en invariantes, inmutabilidad y timezone son más valiosos que perseguir 100% de cobertura.

6. **uv.lock como lockfile.** Resolución determinista, más rápido que pip-tools, hash computado desde el lockfile no desde pip freeze.

### Qué salió mal

1. **Complejidad inicial de tipos.** La combinación de `MappingProxyType`, `freeze_json()`, `Union` con forward references y mypy strict requirió iteración.

2. **Ruff rules cambiaron entre versiones.** `TCH001` fue remapeado a `TC001`, `str+Enum` → `StrEnum` (UP042). Documentar versiones de herramientas es importante.

### Qué aprendimos

1. **frozen=True ≠ inmutable.** Si un campo es `dict` o `list`, el contenido puede mutarse. Siempre usar `MappingProxyType` + `tuple`.

2. **Validación en __post_init__ es el lugar correcto.** Impide crear instancias inválidas. No delegar al consumidor.

3. **Pydantic ValidationError es específico.** Nunca usar `except Exception` para validación de config. `except pydantic.ValidationError` es el patrón correcto.

4. **Tipos JSON explícitos eliminan Any.** `JsonScalar`, `JsonValue`, `JsonArray`, `JsonObject` son self-documenting y type-safe.

5. **Gitleaks es la opción correcta para secret scanning.** Lightweight, rápido, CI-friendly, buena cobertura de patrones.

### Riesgos futuros

| Riesgo | Fase | Severidad |
|--------|------|-----------|
| Gitleaks en GitHub Actions requiere licencia para repos privados | CI | Media |
| `freeze_json()` no soporta tipos custom (solo JSON primitivos) | Fase 3+ | Media |
| Performance de `MappingProxyType` en hot paths | Fase 8+ | Baja |
| Exceso de validación podría ralentizar construcción masiva de objetos | Fase 8+ | Baja |

---

## Fase 1 — Diseño de arquitectura

**Fecha de cierre:** 2026-07-23
**Estado:** Completada

### Qué salió bien

1. **Metodología por fases funcionó.** Separar fundación (Fase 0) de diseño (Fase 1) permitió construir sobre bases sólidas sin deuda técnica prematura.

2. **Interface-first desde el día uno.** Definir 10 interfaces conceptuales antes de escribir código evita el acoplamiento que suele aparecer en proyectos cuantitativos ad-hoc.

3. **Separación investigación/ejecución.** La frontera QuantLab → ExecutionEngine → Hummingbot reduce riesgo operacional.

4. **Roadmap incremental de 14 fases.** Cada fase tiene objetivo, dependencias, entregables y criterio de cierre.

### Qué salió mal

1. **Autenticación GitHub tomó varios intentos.**
2. **Complejidad del árbol de proyecto puede intimidar.**
3. **8 dudas abiertas sin resolución.**

### Qué aprendimos

1. **Un laboratorio cuantitativo no es un bot.** El 80% del valor está en la infraestructura.
2. **La reproducibilidad científica requiere diseño, no disciplina.**
3. **Progressive complexity es clave.**
4. **El catálogo de datos es infraestructura crítica.**
5. **Las interfaces son el activo más valioso del proyecto.**

---

*Se actualizará al cierre de cada fase.*
