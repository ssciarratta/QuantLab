# Fase 60 — i18n Scaffold (es default)

**Estado:** ✅ **APROBADO_INTERNO** (v0.52.0) — certificado externo `FASE_60_APPROVED.md` **NO** emitido  
**Base:** v0.51.0 · F59 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-104  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F60.md` · noche `INTERNAL_AUDIT_F19_F60_NIGHT.md`

## Objetivo

Scaffold de internacionalización UI del workbench:

- Diccionario **es** (default) + stub **en** para strings clave (menú inicio, paneles, botones comunes, aria)
- `QLi18n.t()` / `applyDom()` en shell al load (settings.locale)
- API opcional `GET /api/i18n/{locale}` sirviendo JSON desde `static/i18n/`

## DoD

- [x] `static/js/i18n.js` — diccionario es + stub en · `t()` · `applyDom`
- [x] `static/i18n/es.json` + `en.json` (fuente API)
- [x] Settings locale `es|en` (default `es`) · shell aplica locale al boot
- [x] `GET /api/i18n/{locale}` · OpenAPI catalog
- [x] Suite `tests/unit/workbench/test_i18n_f60.py`
- [x] Spec + IMPLEMENTATION_REPORT
- [x] Smoke F60 + bundle default F19–F60
- [x] DEC-104 · bump **0.52.0**
- [x] Sin `FASE_60_APPROVED.md` · sin LIVE

## Diseño

| Artefacto | Rol |
|-----------|-----|
| `static/js/i18n.js` | `QLi18n` — mensajes embebidos + `t` / `setLocale` / `applyDom` |
| `static/i18n/{locale}.json` | Fuente JSON para API |
| `workbench/i18n.py` | `load_messages` / `build_i18n_payload` |
| `shell.js` | `applyLocale(settings.locale)` al load + títulos pane vía `tr()` |
| `index.html` | `data-i18n` / `data-i18n-aria` en chrome y menú |
| `settings.py` | `ALLOWED_LOCALES = {es, en}` · default `es` |

### Uso

```bash
export PATH="$HOME/.local/bin:$PATH"
uv run pytest -q tests/unit/workbench/test_i18n_f60.py
# GET /api/i18n/es  → messages ES
# GET /api/i18n/en  → stub EN
```

## Fuera de alcance

LIVE · auth WAN · traducción completa de paneles lab · i18n backend mensajes · certificado externo `FASE_60_APPROVED.md` · flip LIVE
