# QuantLab

Plataforma profesional de investigación cuantitativa.

QuantLab es un **laboratorio de investigación cuantitativa**, no un bot de trading. Está diseñado para descubrir, validar, optimizar y comparar estrategias antes de delegar la ejecución a motores especializados como Hummingbot.

---

## Estado del proyecto

| Fase | Nombre | Estado |
|------|--------|--------|
| 0 | Fundación | Completada |
| 1 | Diseño de arquitectura | **En revisión** |
| 2+ | Implementación por capas | Pendiente |

---

## Visión

Construir un sistema central de investigación cuantitativa capaz de:

- Ingerir y almacenar datos de múltiples exchanges y fuentes.
- Ejecutar backtesting de alta fidelidad y simulaciones Monte Carlo masivas.
- Comparar más de 30 estrategias sobre más de 100 activos.
- Optimizar parámetros de forma reproducible.
- Seleccionar automáticamente oportunidades vía Alpha Scanner.
- Enviar estrategias aprobadas a un motor de ejecución (Hummingbot) sin acoplamiento directo.

---

## Principios de diseño

1. **Diseño antes de código** — Ninguna implementación sin arquitectura aprobada.
2. **Modularidad extrema** — Cada módulo tiene interfaces claras y es intercambiable.
3. **Reproducibilidad científica** — Todo experimento es repetible con la misma config, datos y seed.
4. **Escalabilidad horizontal** — Preparado para millones de simulaciones y cientos de activos.
5. **Separación investigación / ejecución** — QuantLab investiga; Hummingbot ejecuta.
6. **Trazabilidad total** — Decisiones, experimentos y resultados quedan registrados.

---

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [docs/Arquitectura.md](docs/Arquitectura.md) | Arquitectura completa del sistema |
| [docs/Arquitectura_Explicada.txt](docs/Arquitectura_Explicada.txt) | Explicación en lenguaje claro |
| [docs/Diagrama.md](docs/Diagrama.md) | Diagramas de módulos y flujos |
| [REVIEW_REQUEST.md](REVIEW_REQUEST.md) | Solicitud de revisión técnica |
| [LESSONS_LEARNED.md](LESSONS_LEARNED.md) | Lecciones de la Fase 1 |
| [CHANGELOG.md](CHANGELOG.md) | Historial de cambios |

---

## Estructura del repositorio (resumen)

```
QuantLab/
├── docs/           Documentación de arquitectura y protocolos
├── learning/       Diario, decisiones y dudas del proyecto
├── src/quantlab/  Código fuente (por implementar en Fase 2+)
├── tests/          Pruebas unitarias e integración
├── config/         Configuración versionada por entorno
├── experiments/    Definiciones y registros de experimentos
├── reports/        Reportes generados (no versionados)
├── scripts/        Utilidades operativas
└── data/           Datos locales (no versionados)
```

Ver el árbol completo en [docs/Arquitectura.md](docs/Arquitectura.md#2-árbol-completo-del-proyecto).

---

## Roles en el proyecto

| Rol | Responsable |
|-----|-------------|
| Director del proyecto | Usuario |
| Revisor técnico / cuantitativo | GPT (arquitecto principal) |
| CTO / Implementador | Cursor |

---

## Licencia

MIT — ver [LICENSE](LICENSE).
