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

Workflow versionado: `.github/workflows/ci.yml`  
Espejo documental: `docs/ci/ci.yml.example`  
Si el push falla por scope OAuth `workflow`: `SKIP_WORKFLOWS=1 bash scripts/sync_phase_github.sh ...`

## Paper ledger

```python
from pathlib import Path
from quantlab.ledger import LocalPaperLedger

ledger = LocalPaperLedger(Path("data/runtime/paper.sqlite"), node_id="lab-1")
ledger.append_simulation(simulation_result)  # append-once por experiment_id

# Federación research (TD-03 mitigado): merge de shards
other = LocalPaperLedger(Path("data/runtime/paper-node2.sqlite"), node_id="lab-2")
report = ledger.reconcile_with(other)
if report.ok:
    ledger.merge_from(other)
```

## Autauditoría

Ver `docs/audit/AUTO_AUDIT_2026-07-25_F18.md` y checklist `docs/ops/RESEARCH_PROD_CHECKLIST.md`.

## Incidentes

| Síntoma | Acción |
|---------|--------|
| Remote con token | `git remote set-url` limpio + revocar token + `check_git_remote_clean` |
| Health `ok=false` | Revisar `LIVE_BLOCKED` y imports NullRouter/ledger |
| Paper ledger conflict | Mismo `experiment_id` con payload distinto → nuevo id |
