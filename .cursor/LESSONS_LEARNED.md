# QuantLab — Lessons Learned

**Actualizado:** 2026-07-26  
**Alcance:** noche F19–F25 (+ reglas permanentes)

---

## F19–F22 — aprendizajes duros

### 1. REAL ≠ LIVE (F19)

- El alias de producto **REAL** significa **PAPER** (`REAL_ALIAS = OperatingMode.PAPER`).
- Market data / cuenta pueden ser “reales”; **fills y órdenes al venue no**.
- Confundir REAL con LIVE es el error de producto más caro: ModeGuard + docs + health deben decirlo explícito.
- `OperatingMode.LIVE` existe en el enum para fail-closed (rechazo), no para habilitar routing.

### 2. Workbench = stdlib (F20–F21)

- Stack elegido: `ThreadingHTTPServer` + SPA estática + window-manager MDI (**sin** Electron / deps UI nuevas).
- Bind default **loopback** (`127.0.0.1`); non-loopback exige `--allow-non-loopback` (F25).
- Connect de broker en UI siempre envuelve **PaperBroker**; paneles lab usan adapters thin sobre research existente.
- Una fase = un job: F20 shell → F21 lab → F22 chat (no mezclar en el mismo DoD).

### 3. Chat safe-by-default (F22)

- Tool calling libre es incompatible con Zero-Trust: **allowlist** + **FORBIDDEN** explícito.
- Default CI = **FakeProvider** (determinista). LLM opt-in solo si `QUANTLAB_LLM_API_KEY` ≠ `DISABLED`.
- El chat **no** puede flippear `LIVE_BLOCKED` ni `place_order` / `submit_order` — tests fail-hard.
- Audit JSONL append-only por turno (`chat_audit.jsonl`) es evidencia, no telemetría opcional.
- Orchestrator aborta si `LIVE_BLOCKED` no es True (defensa en profundidad).

### 4. Auditoría INTERNAL vs externa

- INTERNAL puede cerrar fases/arcos con `APROBADO_INTERNO` + Review Package INTERNAL.
- **Nunca** emitir `FASE_*_APPROVED.md` desde el rol INTERNAL (reserva Meta-Auditor externo).
- Autauditoría ejecutable (`AUTO_AUDIT_*`) + Lista A/B + QA verde = base del veredicto.

### 5. QA del arco

- Canónica: `mypy --strict` + `ruff` + `pytest -q` + `quantlab-health`.
- Smoke barato: `scripts/internal_audit_smoke.py` (LIVE + imports brokers/workbench/chat + F23–F25).
- Contar tests workbench por fase ayuda a no regresar cobertura.

---

## F23–F25 — aprendizajes duros

### 6. PaperBook + path segments (F23)

- `session_id` es segmento de path: charset + anti-traversal + `is_relative_to` parent.
- Cash/shorts fail-closed en load; short default rechazado.
- Risk paper (`max_qty` / notional / symbols) en submit workbench — no en el MD venue.

### 7. Plugins no sombrean builtins (F24)

- Entry points `quantlab.brokers` deben ser **fail-soft** (warning + continue).
- Plugin **no** puede registrar sobre `a3`/`paper`/… ya presentes (`has_venue` + refuse).
- MD env opt-in (`QUANTLAB_A3_MD_READONLY=1`) **nunca** habilita submit venue.

### 8. Ops desk ≠ bind abierto (F25)

- 1-click launcher / `.desktop` no implica exposer WAN: default loopback; flag explícito + WARNING.
- Residuales MEDIUM del arco temprano (charset `experiment_id`, `--host`) se cierran en Ops Desk, no en el shell inicial.
- Slippage paper es **adverso** (BUY peor / SELL peor); default `0` = identidad.
- Panel Riesgo es read-only de límites + sesión; no sustituye el gate LIVE.

### 9. Monte Carlo «ligado» debe ser motor, no solo memo (2026-07-31)

- Pasar `sim_context` solo al banner/memo engaña: el POST seguía BuyOnce + WB:SYN.
- Regla: handoff Sim → POST `sim_context` + `strategy_id` + confirmación explícita moneda/estrategia/params; runner carga velas del par y la estrategia del Sim (`mode=sim_linked`).
- Limpiar `backtest_id` residual de Guided Lab al abrir MC desde Simulador.

### 10. Corridas concurrentes = UX + AbortSignal (2026-07-31)

- Sin coordinador, Comparar/Ranking/MC/Scanner se pisan en silencio.
- `QLRunGate`: una activa; si hay otra → Esperar / Cortar / Cancelar; Stop en panel y status bar.
- `QLApi.request` debe aceptar `signal` (AbortController); jobs MC async se cancelan vía `onCancel` + API cancel.

---

## Permanentes (pre-F19, siguen vigentes)

- Order routing LIVE A3 bloqueado (`live_gate.py`) — TD-10.
- Strategy produce `OrderIntent`; el simulador decide fills.
- Raw inmutable; anticorrupción A3 (dominio no importa pyRofex).
- Certificados formales solo con APROBADO explícito del Meta-Auditor externo.
