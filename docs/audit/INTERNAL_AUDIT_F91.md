# INTERNAL AUDIT — F91 Paper Session Rehydrate post-rebuild

**Veredicto:** `# APROBADO_INTERNO`  
**Fecha:** 2026-07-26  
**Código tip auditado:** `5c34995` · **v0.83.0**  
**Branch:** `cursor/modo-real-workbench-aafd`  
**LIVE_BLOCKED:** True

## Veredicto de riesgo

| Severidad | Abiertos |
|-----------|---------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW/INFO | 1 limitación documentada: sin auto-detección de rebuild externo |

## Checklist Zero-Trust

| Check | Resultado |
|-------|-----------|
| Rehydrate nunca reconstruye archivos (no llama rebuild) | **PASS** |
| Journal byte-idéntico pre/post rehydrate | **PASS** |
| Durable inválido queda `rebuild_required`/`book_corrupt` (sin auto-recovery) | **PASS** |
| Teardown reusa `switch_session` (path auditado F46/F88) | **PASS** |
| `persist_book` en teardown solo si reconcilia exacto (no pisa rebuild) | **PASS** |
| Broker desconectado post-rehydrate; reconexión explícita | **PASS** |
| Catálogo OpenAPI POST-only (sin GET mutable) | **PASS** |
| UI exige `confirm()`; único QLApi extra: `paperRehydrate` | **PASS** |
| Evento `rehydrate` allowlisted en activity (F41) | **PASS** |
| `LIVE_BLOCKED is True`; handler lo exige | **PASS** |
| Sin `FASE_91_APPROVED.md` | **PASS** |
| `phases_summary == "F19–F91 INTERNAL"` · bump 0.83.0 | **PASS** |

## Evidencia adversarial

1. `test_rehydrate_without_rebuild_stays_blocked`: journal ahead sin rebuild →
   rehydrate devuelve `rebuild_required`, journal y book intactos byte a byte.
2. `test_rehydrate_after_cli_rebuild_unblocks_without_restart`: loop completo
   drift → rebuild CLI (backup) → rehydrate → `ok`, cash == replay exacto,
   sin tocar los archivos que dejó el rebuild.
3. `test_rehydrate_disconnects_broker_and_reports_it`: broker=None y
   `broker_connected=false` en payload.
4. Smoke F91: rehydrate en sesión limpia (idempotente), POST-only y journal
   intacto.

## Análisis del riesgo clave

El riesgo de diseño era que el teardown persistiera el book en memoria por
encima del book reconstruido. `persist_book` solo escribe si el book en
memoria reconcilia exacto con el journal; en ese caso es idéntico al replay
(o sea, al resultado del rebuild). Si no reconcilia, lanza y el teardown lo
suprime sin escribir. En ningún caso puede pisar un rebuild válido con estado
divergente.

## QA

```text
mypy --strict src/quantlab             PASS (200 source files)
ruff check src/quantlab tests scripts  PASS
pytest -q                              1171 passed, 2 skipped
internal_audit_smoke.py                PASS (incluye F91)
```

---

Meta-Auditor INTERNO Zero-Trust · F91 · **APROBADO_INTERNO** · sin certificado
externo · `LIVE_BLOCKED=True`
