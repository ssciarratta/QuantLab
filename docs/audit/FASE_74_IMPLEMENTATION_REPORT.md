# FASE 74 — Implementation Report (Status Bar Clock Timezone)

**Fecha:** 2026-07-26  
**Versión:** 0.66.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F73 Optional Sound Alerts · F36 Settings + Status Bar  
**Impl SHA:** `ce0d5d1`  
**Alcance:** settings `timezone` UTC|local + status bar clock — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| D1 | Settings field `timezone` default UTC | `workbench/settings.py` · `api.py` PUT merge |
| D2 | Settings select UI | `static/js/panes/settings.js` |
| D3 | Status bar clock TZ hook | `static/js/shell.js` (`setClockTimezone` / `tickClock`) |
| D4 | Spec + DEC-118 + bump | `docs/FASE_74_CLOCK_TZ.md` · **0.66.0** |
| D5 | Suite roundtrip | `tests/unit/workbench/test_clock_timezone_f74.py` |
| D6 | Smoke F74 | `scripts/internal_audit_smoke.py` |
| D7 | Implementation report | este doc |
| D8 | Bundle default F19–F74 | `scripts/build_internal_review_bundle.py` |

## Invariantes

- `LIVE_BLOCKED is True`
- Sin `FASE_74_APPROVED.md`
- Sin flip LIVE / place_order venue
- DEC-118
- `phases_summary == "F19–F74 INTERNAL"`
- About `version` ≡ `__version__` · **0.66.0**
- Default `timezone == "UTC"`
- Allowed: `UTC` \| `local` only

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
- Certificado externo `FASE_74_APPROVED.md`
- IANA TZ database / offsets arbitrarios
