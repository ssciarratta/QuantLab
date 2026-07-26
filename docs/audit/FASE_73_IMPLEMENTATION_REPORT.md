# FASE 73 — Implementation Report (Optional Sound Alerts)

**Fecha:** 2026-07-26  
**Versión:** 0.65.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F72 Desktop Notifications · F70 Paper Kill · F41 Toasts  
**Impl SHA:** `e3257b7`  
**Alcance:** settings opt-in + WebAudio beep en toast errors / kill engage — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| D1 | Settings field `sound_alerts` default false | `workbench/settings.py` · `api.py` PUT merge |
| D2 | Settings checkbox UI | `static/js/panes/settings.js` |
| D3 | WebAudio beep hook (graceful) | `static/js/toasts.js` · `shell.js` |
| D4 | Spec + DEC-117 + bump | `docs/FASE_73_SOUND.md` · **0.65.0** |
| D5 | Suite roundtrip | `tests/unit/workbench/test_sound_alerts_f73.py` |
| D6 | Smoke F73 | `scripts/internal_audit_smoke.py` |
| D7 | Implementation report | este doc |
| D8 | Bundle default F19–F73 | `scripts/build_internal_review_bundle.py` |

## Invariantes

- `LIVE_BLOCKED is True`
- Sin `FASE_73_APPROVED.md`
- Sin flip LIVE / place_order venue
- DEC-117
- `phases_summary == "F19–F73 INTERNAL"`
- About `version` ≡ `__version__` · **0.65.0**
- Default `sound_alerts is False` (opt-in)
- Sin assets de audio externos

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
- Certificado externo `FASE_73_APPROVED.md`
- WAV/MP3 / Service Worker audio
