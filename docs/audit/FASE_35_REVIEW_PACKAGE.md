# FASE 35 — Review Package INTERNAL (Command Palette + Shortcuts)

**Fecha:** 2026-07-26  
**Versión código (impl F35):** 0.27.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**LIVE:** BLOQUEADO · flip **NO**

## Decisión de diseño

**Opción elegida:** registry server-side `commands.py` expuesto por `GET /api/commands`; palette SPA carga lista y ejecuta client-side (abrir pane / health refresh / close focused). Atajos Ctrl+K / Ctrl+Shift+P / Ctrl+1..9 / Esc / Ctrl+W (DEC-079).

## Artefactos A

| ID | Artefacto | Path |
|----|-----------|------|
| A1 | Registry | `workbench/commands.py` |
| A2 | API + server | `api.py` · `server.py` |
| A3 | Palette JS | `static/js/command_palette.js` |
| A4 | Shell shortcuts | `static/js/shell.js` |
| A5 | WM closeFocused | `static/js/wm.js` |
| A6 | Spec | `docs/FASE_35_COMMAND_PALETTE.md` |
| A7 | Implementation report | `docs/audit/FASE_35_IMPLEMENTATION_REPORT.md` |
| A8 | DEC-079 | `learning/decisiones.txt` |
| A9 | Suite F35 | `tests/unit/workbench/test_commands_f35.py` |
| A10 | Version 0.27.0 | `pyproject.toml` |

## QA esperado

```text
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health                → ok=true, live_blocked=true, version=0.27.0
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance

LIVE flip · auth WAN · browser E2E · certificado externo `FASE_35_APPROVED.md`
