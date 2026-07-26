#!/usr/bin/env bash
# QuantLab Workbench — launcher 1-click (Fase 25 Ops Desk).
# Portable: detecta uv o .venv; sync opcional; abre browser por defecto.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PATH="${HOME}/.local/bin:${PATH}"

# QUANTLAB_SYNC=1 → uv sync --extra dev antes de arrancar
SYNC="${QUANTLAB_SYNC:-0}"

run_workbench() {
  # Args extra se pasan a quantlab-workbench (p. ej. --no-browser, --mode paper).
  if command -v uv >/dev/null 2>&1; then
    if [[ "$SYNC" == "1" ]]; then
      echo "[launch] uv sync --extra dev…"
      uv sync --extra dev
    fi
    exec uv run quantlab-workbench "$@"
  fi

  if [[ -x "$ROOT/.venv/bin/quantlab-workbench" ]]; then
    exec "$ROOT/.venv/bin/quantlab-workbench" "$@"
  fi

  if [[ -x "$ROOT/.venv/bin/python" ]]; then
    export PYTHONPATH="${ROOT}/src${PYTHONPATH:+:$PYTHONPATH}"
    exec "$ROOT/.venv/bin/python" -m quantlab.workbench.launch "$@"
  fi

  echo "ERROR: no se encontró uv ni .venv usable." >&2
  echo "  Instalá uv (https://docs.astral.sh/uv/) o creá .venv con:" >&2
  echo "    python -m venv .venv && .venv/bin/pip install -e '.[dev]'" >&2
  exit 1
}

run_workbench "$@"
