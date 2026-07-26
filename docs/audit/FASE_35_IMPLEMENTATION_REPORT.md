# FASE 35 — Implementation Report (Command Palette + Keyboard Shortcuts)

**Fecha:** 2026-07-26  
**Versión:** 0.27.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F34 MC/Export · F20 Workbench WM  
**Alcance:** command palette + shortcuts — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| S1 | Registry comandos | `workbench/commands.py` |
| A1 | `GET /api/commands` | `api.py` + `server.py` |
| U1 | Command palette JS | `static/js/command_palette.js` |
| U2 | Shortcuts shell | `static/js/shell.js` |
| U3 | WM focused/close | `static/js/wm.js` |
| U4 | CSS overlay | `static/css/workbench.css` |
| U5 | Index script | `static/index.html` |
| C1 | `QLApi.commands` | `static/js/api.js` |
| T1 | Tests F35 | `tests/unit/workbench/test_commands_f35.py` |
| T2 | Smoke F35 | `scripts/internal_audit_smoke.py` |
| D1 | Spec + DEC-079 + bump | `docs/FASE_35_COMMAND_PALETTE.md` · `0.27.0` |

## Invariantes

- `LIVE_BLOCKED is True`
- Comandos `safe=true` · `live=false`
- Sin flip LIVE / place_order / set_live en registry
- DEC-079

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff format src/quantlab tests/unit/workbench
uv run ruff check src/quantlab tests/unit/workbench
uv run mypy --strict src/quantlab
uv run pytest tests/unit/workbench/test_commands_f35.py -q
uv run pytest tests/unit/workbench -q
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- Auth WAN / Electron
- Browser E2E
- Certificado externo `FASE_35_APPROVED.md`
