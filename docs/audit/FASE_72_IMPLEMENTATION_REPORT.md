# FASE 72 — Implementation Report (Desktop Notifications Hook)

**Fecha:** 2026-07-26  
**Versión:** 0.64.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F71 Health Extended · F70 Paper Kill · F41 Toasts  
**Alcance:** settings opt-in + Notification API en toast errors / kill engage — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| D1 | Settings field `desktop_notifications` default false | `workbench/settings.py` · `api.py` PUT merge |
| D2 | Settings checkbox UI | `static/js/panes/settings.js` |
| D3 | Toast/kill Notification hook (graceful) | `static/js/toasts.js` · `api.js` · `shell.js` |
| D4 | Spec + DEC-116 + bump | `docs/FASE_72_NOTIFICATIONS.md` · **0.64.0** |
| D5 | Suite roundtrip | `tests/unit/workbench/test_desktop_notifications_f72.py` |
| D6 | Smoke F72 | `scripts/internal_audit_smoke.py` |
| D7 | Implementation report | este doc |
| D8 | Bundle default F19–F72 | `scripts/build_internal_review_bundle.py` |

## Invariantes

- `LIVE_BLOCKED is True`
- Sin `FASE_72_APPROVED.md`
- Sin flip LIVE / place_order venue
- DEC-116
- `phases_summary == "F19–F72 INTERNAL"`
- About `version` ≡ `__version__` · **0.64.0**
- Default `desktop_notifications is False` (opt-in)

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff check src/quantlab tests scripts
uv run mypy --strict src/quantlab
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- Auth WAN / Electron
- Certificado externo `FASE_72_APPROVED.md`
- Service Worker / Web Push
