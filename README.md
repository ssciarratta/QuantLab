# QuantLab

Plataforma profesional de investigación cuantitativa.

QuantLab es un **laboratorio de investigación cuantitativa**, no un bot de trading. Está diseñado para descubrir, validar, optimizar y comparar estrategias antes de delegar la ejecución a motores especializados como Hummingbot.

---

## Estado del proyecto

| Fase | Nombre | Estado |
|------|--------|--------|
| 0 | Fundación | Completada |
| 1 | Diseño de arquitectura | Completada |
| 2 | Core + Infraestructura | **EN CORRECCIÓN** |
| 3+ | Implementación por capas | Pendiente |

---

## Instalación

```bash
# Requiere Python 3.11+ y uv
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Verificar instalación

```bash
quantlab-vertical-slice
```

---

## Desarrollo

```bash
# Lint
ruff check .
ruff format --check .

# Type checking
mypy src tests

# Tests
pytest tests/ -v

# Coverage
pytest --cov=quantlab --cov-report=term-missing

# Vertical slice
quantlab-vertical-slice
```

---

## Estructura del proyecto

```
QuantLab/
├── src/quantlab/
│   ├── core/               Interfaces, tipos de dominio, excepciones
│   │   ├── types/           Instrument, Bar, Order, OrderIntent, etc.
│   │   ├── interfaces/      Strategy Protocol (on_event)
│   │   └── exceptions/      Jerarquía de errores
│   └── infra/               Config, logging, utils
│       ├── config/           Pydantic + YAML deep merge
│       ├── logging/          structlog (consola/JSON)
│       └── utils/            Hashing, git, paths
├── tests/                   157 tests de comportamiento
├── config/                  YAML por entorno
├── .github/workflows/       CI (ruff, mypy, pytest, gitleaks)
├── docs/                    Arquitectura y diagramas
├── learning/                Decisiones, dudas, diario
└── reports/                 Reportes generados
```

---

## Principios de diseño

1. **Diseño antes de código** — Sin implementación sin arquitectura aprobada.
2. **Modularidad extrema** — Interfaces claras e intercambiables.
3. **Reproducibilidad científica** — Todo experimento es repetible.
4. **Inmutabilidad profunda** — MappingProxyType + tuples, no solo frozen=True.
5. **Separación investigación / ejecución** — QuantLab investiga; Hummingbot ejecuta.
6. **Fail fast** — Validación en construcción, no en consumo.

---

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [docs/Arquitectura.md](docs/Arquitectura.md) | Arquitectura completa del sistema |
| [docs/Diagrama.md](docs/Diagrama.md) | Diagramas de módulos y flujos |
| [REVIEW_REQUEST.md](REVIEW_REQUEST.md) | Solicitud de revisión + matriz de corrección |
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | Estado actual del proyecto |
| [LESSONS_LEARNED.md](LESSONS_LEARNED.md) | Lecciones por fase |
| [CHANGELOG.md](CHANGELOG.md) | Historial de cambios |

---

## Licencia

MIT — ver [LICENSE](LICENSE).
