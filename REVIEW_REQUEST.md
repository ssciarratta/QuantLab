# REVIEW REQUEST — Fase 2: Core + Infraestructura (Post-Auditoría v1.1)

**Proyecto:** QuantLab
**Fase:** 2 — Core + Infraestructura
**Iteración:** v1.1 (primera corrección post-auditoría)
**Fecha:** 2026-07-23
**Estado:** EN CORRECCIÓN — esperando segunda revisión GPT

---

## Resumen ejecutivo

Se implementó la Fase 2 de QuantLab (core + infraestructura) corrigiendo **todos** los hallazgos de la auditoría técnica de GPT sobre la Fase 1/2.

Este paquete contiene el proyecto completo actualizado, no un parche.

---

## Matriz de corrección

| # | Hallazgo GPT | Severidad | Corrección aplicada | Archivos principales | Tests | Estado |
|---|-------------|-----------|--------------------|--------------------|-------|--------|
| 1 | Secretos expuestos en código | Crítica | No había secretos. Se integró `.gitleaks.toml` + CI scan | `.gitleaks.toml`, `.github/workflows/ci.yml` | CI verifica | CORREGIDO |
| 2 | Escaneo automático de secretos | Alta | Gitleaks adoptado (DEC-017). CI bloquea si detecta secretos | `.gitleaks.toml`, `.github/workflows/ci.yml` | CI step | CORREGIDO |
| 3 | requirements.txt de entorno global | Alta | Eliminado. Se usa `pyproject.toml` + `uv.lock` (DEC-018) | `pyproject.toml`, `uv.lock` | `test_lockfile_hash` | CORREGIDO |
| 4 | Lockfile reproducible | Alta | `uv.lock` generado. Hash desde lockfile, no pip freeze | `uv.lock`, `infra/utils/hashing.py` | `test_deterministic`, `test_uses_uv_lock_first` | CORREGIDO |
| 5 | Hashes truncados | Media | `compute_file_hash()` retorna digest completo (64 chars SHA-256) | `infra/utils/hashing.py` | `test_full_hash_not_truncated` | CORREGIDO |
| 6 | Falsa opcionalidad de on_bar() | Alta | `on_event(MarketEvent, StrategyContext)` reemplaza `on_bar()` (DEC-013) | `core/interfaces/strategy.py`, `cli.py` | `test_strategy_protocol.py` (7 tests) | CORREGIDO |
| 7 | DummyStrategy sin actualizar | Media | DummyStrategy usa `on_event()`, retorna `tuple[OrderIntent, ...]` | `cli.py` | `test_strategy_protocol.py`, `test_vertical_slice.py` | CORREGIDO |
| 8 | Inmutabilidad superficial (frozen=True con dict/list) | Alta | `MappingProxyType` + `tuple` + `freeze_json()` recursivo (DEC-014) | Todos los tipos en `core/types/` | 15+ tests de inmutabilidad | CORREGIDO |
| 9 | Instrument.metadata mutable | Alta | `MappingProxyType[str, JsonValue]` | `core/types/market.py` | `test_metadata_is_immutable` | CORREGIDO |
| 10 | StrategyContext.parameters mutable | Alta | `MappingProxyType[str, JsonValue]` | `core/types/trading.py` | `test_parameters_immutable` | CORREGIDO |
| 11 | MarketEvent.payload mutable | Alta | `MappingProxyType[str, JsonValue]` | `core/types/trading.py` | `test_payload_immutable` | CORREGIDO |
| 12 | ExperimentManifest.resolved_config mutable | Alta | `MappingProxyType[str, JsonValue]` | `core/types/experiment.py` | `test_resolved_config_immutable` | CORREGIDO |
| 13 | SimulationResult.metadata/events_log mutable | Alta | `MappingProxyType` + `tuple` | `core/types/trading.py` | `test_metadata_immutable`, `test_events_log_immutable` | CORREGIDO |
| 14 | MetricsResult.metrics/benchmarks mutable | Alta | `MappingProxyType` | `core/types/trading.py` | `test_metrics_immutable`, `test_benchmarks_immutable` | CORREGIDO |
| 15 | OrderIntent sin validación por tipo | Crítica | Validación completa por IntentType (DEC-016) | `core/types/trading.py` | 18 tests en `test_trading_types.py` | CORREGIDO |
| 16 | Invariantes de Instrument | Alta | tick_size/lot_size positivos, min_notional no negativo, símbolos no vacíos, base≠quote | `core/types/market.py` | 8 tests | CORREGIDO |
| 17 | Invariantes de Bar | Alta | tz-aware, high≥open/close/low, low≤open/close, precios positivos, vol≥0 | `core/types/market.py` | 12 tests | CORREGIDO |
| 18 | Invariantes de BookLevel | Media | precio positivo, cantidad no negativa | `core/types/market.py` | 3 tests | CORREGIDO |
| 19 | Invariantes de Trade/Fill | Alta | precio/cantidad positivos, timestamp tz-aware | `core/types/market.py` | 7 tests | CORREGIDO |
| 20 | Invariantes de Order | Alta | cantidad positiva, filled≤quantity, LIMIT requiere precio, tz-aware | `core/types/market.py` | 6 tests | CORREGIDO |
| 21 | Invariantes de Balance | Media | no negativos, total=available+locked | `core/types/trading.py` | 4 tests | CORREGIDO |
| 22 | Invariantes de TimeRange | Media | tz-aware, start<end | `core/types/trading.py` | 4 tests | CORREGIDO |
| 23 | Invariantes de ExperimentManifest | Alta | IDs, versión, timestamp, checksum, instrumentos, commit, lockfile_hash | `core/types/experiment.py` | 10 tests | CORREGIDO |
| 24 | except Exception genérico | Alta | Captura `pydantic.ValidationError` específicamente (DEC-019) | `infra/config/loader.py` | `test_config.py` (14 tests) | CORREGIDO |
| 25 | Valores de logging no validados | Media | `LogLevel`, `LogFormat`, `Environment` como StrEnum | `infra/config/loader.py` | `test_invalid_log_level`, `test_invalid_log_format` | CORREGIDO |
| 26 | Configuración duplicada | Media | Single source of truth en `QuantLabConfig`. `logging.yaml` documenta deferencia | `infra/config/loader.py`, `config/base/` | `test_logging_yaml_merged` | CORREGIDO |
| 27 | Uso excesivo de Any | Alta | `JsonScalar`, `JsonValue`, `JsonArray`, `JsonObject` (DEC-015) | `core/types/json_types.py` | `test_json_types.py` (12 tests) | CORREGIDO |
| 28 | mypy --strict no limpio | Alta | 0 errores en mypy --strict | Todos | CI step | CORREGIDO |
| 29 | Tests de comportamiento faltantes | Crítica | 157 tests cubriendo invariantes, inmutabilidad, timezone, protocol, config | `tests/` | 157 tests | CORREGIDO |
| 30 | CI incompleta | Alta | Workflow con install, ruff, mypy, pytest, coverage, vertical slice, secrets | `.github/workflows/ci.yml` | — | CORREGIDO |
| 31 | YAML vacío/malformado | Media | Handlers para YAML vacío y con solo comentarios | `infra/config/loader.py` | `test_empty_yaml`, `test_yaml_with_only_comments`, `test_malformed_yaml` | CORREGIDO |
| 32 | Deep merge | Media | `_deep_merge()` recursivo con tests | `infra/config/loader.py` | `test_deep_merge_preserves_base` | CORREGIDO |
| 33 | Ausencia de Git | Media | `get_git_commit()` retorna "unknown" sin git | `infra/utils/git.py` | `test_returns_commit_or_unknown` | CORREGIDO |
| 34 | Búsqueda de project root | Media | `find_project_root()` con error si no existe | `infra/utils/paths.py` | `test_not_found_raises` | CORREGIDO |
| 35 | Vertical slice con estrategia inyectada | Alta | `test_vertical_slice.py` con DummyStrategy y PassThroughStrategy | `tests/integration/test_vertical_slice.py` | 5 tests | CORREGIDO |

---

## Documentos actualizados

- `README.md` — Actualizado con Fase 2
- `CHANGELOG.md` — Entrada para v0.2.0
- `LESSONS_LEARNED.md` — Lecciones de auditoría
- `PROJECT_STATUS.md` — Estado EN CORRECCIÓN
- `learning/decisiones.txt` — DEC-013 a DEC-019
- `docs/Arquitectura.md` — Sin cambios (diseño Fase 1)

---

## Verificación

| Check | Resultado |
|-------|-----------|
| `ruff check .` | ✅ Limpio |
| `ruff format --check .` | ✅ Limpio |
| `mypy src tests` | ✅ 0 errores |
| `pytest` | ✅ 157 passed |
| `pytest --cov` | ✅ >80% |
| `quantlab-vertical-slice` | ✅ PASSED |
| Secretos en repo | ✅ 0 detectados |

---

## Archivos del Review Package

El ZIP `QuantLab_Review_Fase_02_v1.1.zip` contiene el proyecto completo.

---

## Restricciones cumplidas

- ❌ No se inició Fase 3
- ❌ No se agregaron funcionalidades fuera del alcance
- ❌ No se reinterpretaron los hallazgos
- ✅ Todos los hallazgos tienen corrección documentada
- ✅ Tests demuestran las correcciones

---

*Esperando segunda revisión de GPT para autorización de Fase 3.*
