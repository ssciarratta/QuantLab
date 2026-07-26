# INTERNAL AUDIT — F96 Diagnostics Download (support snapshot)

**Veredicto:** `# APROBADO_INTERNO`
**Fecha:** 2026-07-26
**Código tip auditado:** `d2239cc` · **v0.88.0**
**Branch:** `cursor/modo-real-workbench-aafd`
**LIVE_BLOCKED:** True (verificado en smoke)
**Auditor:** interno Zero-Trust (no sustituye Meta-Auditor externo)

---

## 1. Alcance auditado

- `GET /api/diagnostics.json` (`handle_get_diagnostics_download`): reutiliza el
  snapshot read-only de F95, lo serializa a JSON indentado y lo entrega como
  descarga adjunta (`Content-Disposition`), con nombre saneado por `session_id`.
- Ruta en `server.py` vía `_send_download`; declarada en `api_catalog.py`.
- Botón "Descargar" en `panes/diagnostics.js` + helper `diagnosticsDownloadUrl`.
- Tests `test_diagnostics_download_f96.py` + smoke `check_f96_diagnostics_download`.

## 2. QA verificado (Windows, 2026-07-26)

| Gate | Resultado |
|---|---|
| mypy --strict src/quantlab | Success (200 files) |
| ruff check src/quantlab tests scripts | All checks passed |
| pytest -q | 1194 passed, 2 skipped (ver nota) |
| internal_audit_smoke.py | PASS (incluye F96) |

**Nota QA:** una corrida del suite marcó `test_perf_baseline_key_endpoints_p95`
como fallo por presión de disco/I/O (C: al 100%); re-ejecutado en aislamiento
pasa. Es un umbral de latencia p95 sensible a carga del sistema, no un defecto
de F96. Se liberó espacio limpiando temporales regenerables (VS Code/pytest).

## 3. Hallazgos

Sin hallazgos bloqueantes. Descarga estrictamente read-only; sin nuevas fuentes
de datos. El catálogo mantiene el guard F55 contra rutas LIVE.

## 4. Invariantes

- `LIVE_BLOCKED is True`; descarga sin acciones ni mutaciones.
- No existe `docs/audit/FASE_96_APPROVED.md` (reserva Meta-Auditor externo).

**Cierre formal pendiente de auditoría externa.**
