# QuantLab — Lessons Learned

**Actualizado:** 2026-07-26  
**Alcance:** arco nocturno F19–F22 (+ reglas permanentes)

---

## F19–F22 — aprendizajes duros

### 1. REAL ≠ LIVE (F19)

- El alias de producto **REAL** significa **PAPER** (`REAL_ALIAS = OperatingMode.PAPER`).
- Market data / cuenta pueden ser “reales”; **fills y órdenes al venue no**.
- Confundir REAL con LIVE es el error de producto más caro: ModeGuard + docs + health deben decirlo explícito.
- `OperatingMode.LIVE` existe en el enum para fail-closed (rechazo), no para habilitar routing.

### 2. Workbench = stdlib (F20–F21)

- Stack elegido: `ThreadingHTTPServer` + SPA estática + window-manager MDI (**sin** Electron / deps UI nuevas).
- Bind default **loopback** (`127.0.0.1`); `--host` no-loopback es riesgo consciente (MEDIUM abierto).
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
- Smoke barato: `scripts/internal_audit_smoke.py` (LIVE + imports brokers/workbench/chat).
- Contar tests workbench por fase (F20 shell → F21 lab → F22 chat) ayuda a no regresar cobertura.

---

## Permanentes (pre-F19, siguen vigentes)

- Order routing LIVE A3 bloqueado (`live_gate.py`) — TD-10.
- Strategy produce `OrderIntent`; el simulador decide fills.
- Raw inmutable; anticorrupción A3 (dominio no importa pyRofex).
- Certificados formales solo con APROBADO explícito del Meta-Auditor externo.
