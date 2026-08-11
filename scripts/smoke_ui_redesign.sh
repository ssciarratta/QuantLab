#!/usr/bin/env bash
# Smoke test — UI radical simplification (worktree)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PORT="${SMOKE_PORT:-8766}"
BASE="http://127.0.0.1:${PORT}"
FAIL=0

pass() { echo "  OK  $1"; }
fail() { echo "  FAIL $1"; FAIL=1; }

echo "== Smoke UI redesign =="

echo "[1] Archivos estáticos clave"
for f in \
  src/quantlab/workbench/static/js/panel_registry.js \
  src/quantlab/workbench/static/js/ql_ui.js \
  src/quantlab/workbench/static/js/panes/home.js \
  src/quantlab/workbench/static/js/panes/monitor.js \
  src/quantlab/workbench/static/css/design_tokens.css; do
  if [[ -f "$f" ]]; then pass "$f"; else fail "missing $f"; fi
done

echo "[2] Gate Python (rápido)"
if uv run pytest tests/unit/execution/test_strategy_execution.py -q --tb=no 2>/dev/null; then
  pass "pytest strategy_execution"
else
  fail "pytest strategy_execution"
fi

echo "[3] Servidor workbench :${PORT}"
uv run quantlab-workbench --host 127.0.0.1 --port "$PORT" >/tmp/ql_smoke_ui.log 2>&1 &
PID=$!
cleanup() { kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true; }
trap cleanup EXIT
for i in $(seq 1 40); do
  if curl -sf "$BASE/api/health" >/dev/null 2>&1; then break; fi
  sleep 0.5
done
if curl -sf "$BASE/api/health" >/dev/null 2>&1; then
  pass "GET /api/health"
else
  fail "GET /api/health (server no respondió)"
fi

echo "[4] Static assets"
for path in \
  /static/js/panel_registry.js \
  /static/js/ql_ui.js \
  /static/js/panes/home.js \
  /static/js/panes/monitor.js \
  /static/index.html; do
  if curl -sf "$BASE${path}" | head -c 20 >/dev/null 2>&1; then
    pass "GET $path"
  else
    fail "GET $path"
  fi
done

echo "[5] index.html referencias"
HTML="$(curl -sf "$BASE/static/index.html" || true)"
echo "$HTML" | grep -q "panel_registry.js" && pass "index → panel_registry" || fail "index → panel_registry"
echo "$HTML" | grep -q "home.js" && pass "index → home.js" || fail "index → home.js"
echo "$HTML" | grep -q "monitor.js" && pass "index → monitor.js" || fail "index → monitor.js"

echo "[6] Klines API (best-effort red)"
KL="$(curl -sf --max-time 15 -X POST "$BASE/api/lab/binance/klines" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTCUSDT","interval":"1m","limit":5,"market_type":"spot"}' 2>/dev/null || true)"
if echo "$KL" | grep -q '"bars"'; then
  pass "POST klines bars"
else
  echo "  WARN klines omitido (red Binance o timeout) — UI no depende en runtime"
  pass "POST klines skipped (offline ok)"
fi

if [[ "$FAIL" -eq 0 ]]; then
  echo "== SMOKE OK =="
  exit 0
else
  echo "== SMOKE FAILED =="
  tail -20 /tmp/ql_smoke_ui.log 2>/dev/null || true
  exit 1
fi
