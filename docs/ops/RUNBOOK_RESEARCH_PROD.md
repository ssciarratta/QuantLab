# Runbook Research-Prod QuantLab

**LIVE order routing: BLOQUEADO.** No habilitar.

## Gate diario (local)

```bash
uv run python scripts/check_git_remote_clean.py
uv run quantlab-health
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab
uv run pytest -q
```

## CI

Fuente: `docs/ci/ci.yml.example`  
Activar en Actions: `mkdir -p .github/workflows && cp docs/ci/ci.yml.example .github/workflows/ci.yml`  
(Push requiere OAuth/PAT con scope `workflow`.)

## Paper ledger

```python
from pathlib import Path
from quantlab.ledger import LocalPaperLedger
ledger = LocalPaperLedger(Path("data/runtime/paper.sqlite"))
ledger.append_simulation(simulation_result)  # append-once por experiment_id
```

## Autauditoría

Ver `docs/audit/AUTO_AUDIT_2026-07-25_F18.md` y checklist `docs/ops/RESEARCH_PROD_CHECKLIST.md`.

## Incidentes

| Síntoma | Acción |
|---------|--------|
| Remote con token | `git remote set-url` limpio + revocar token + `check_git_remote_clean` |
| Health `ok=false` | Revisar `LIVE_BLOCKED` y imports NullRouter/ledger |
| Paper ledger conflict | Mismo `experiment_id` con payload distinto → nuevo id |
