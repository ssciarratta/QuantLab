#!/usr/bin/env bash
# Sync de cierre de fase → GitHub (para ver el repo actualizado desde el celular / Cursor).
# Uso:
#   bash scripts/sync_phase_github.sh FASE_07 "Backtester 5B"
#   bash scripts/sync_phase_github.sh --status   # solo muestra estado
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ "${1:-}" == "--status" ]]; then
  git status -sb
  git log origin/main..HEAD --oneline 2>/dev/null || true
  exit 0
fi

PHASE_ID="${1:?Falta ID de fase (ej. FASE_07)}"
PHASE_TITLE="${2:-$PHASE_ID}"
STAMP="$(date '+%Y-%m-%d %H:%M')"

echo "==> QA gate ($PHASE_ID)"
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab
uv run pytest -q --tb=line

echo "==> Staging (sin secretos / basura)"
git add -A
# Nunca versionar ruido local
git reset HEAD -- .coverage .env 2>/dev/null || true
# Escape hatch: SKIP_WORKFLOWS=1 si el PAT/OAuth no tiene scope `workflow`
if [[ "${SKIP_WORKFLOWS:-0}" == "1" ]]; then
  echo "==> SKIP_WORKFLOWS=1 — excluyendo .github/workflows del commit"
  git reset HEAD -- .github/workflows 2>/dev/null || true
fi
git status -sb

if git diff --cached --quiet && git diff --quiet; then
  echo "==> Sin cambios locales; intento push de commits pendientes"
else
  git commit -m "$(cat <<EOF
fase: ${PHASE_ID} — ${PHASE_TITLE}

Cierre de fase con QA (mypy/ruff/pytest) en verde.
Sync GitHub para seguimiento remoto (${STAMP}).
EOF
)"
fi

echo "==> Push origin main"
git push origin main

echo "==> OK — remoto actualizado"
git status -sb
git log -1 --oneline
