# Fase 19 — Operating Modes (TESTER / PAPER·REAL / LIVE)

**Estado:** ✅ **APROBADO_INTERNO** (Meta-Auditor INTERNO Zero-Trust, 2026-07-26)  
**Certificado externo:** pendiente — **no** existe `FASE_19_APPROVED.md`  
**Fecha diseño / auditoría INTERNAL:** 2026-07-26  
**Código:** **v0.11.0** · commit implementación `a5b12d3`  
**Evidencia INTERNAL:** `docs/audit/INTERNAL_AUDIT_F19.md` · `AUTO_AUDIT_2026-07-26_F19.md` · `FASE_19_REVIEW_PACKAGE.md`  
**Pedido dueño (2026-07-26):** modo TESTER + modo REAL multiplataforma; workbench; chat IA; fases + auditor interno.  
**Alcance F19:** modos operativos + `BrokerPort` multiplataforma + paper broker. **Sin UI** (F20). **Sin chat IA** (F21/F22). **Sin LIVE orders por default.**

---

## 0. Hechos verificados (invariantes de partida)

| Hecho | Estado |
|-------|--------|
| F0–F18 certificados | Sí |
| `LIVE_BLOCKED` | `True` (inmutable sin decisión explícita + Meta-Auditor) |
| UI | Ausente hasta F20 |
| DEC-008 | research ≠ execution (AMEND F19: PAPER permitido) |
| A3 Fake / `--live-api` | Solo market data (órdenes gated) |
| `LocalPaperLedger` | Auditoría de sims ≠ paper broker de fills |

---

## 1. Objetivo de producto

| Modo | Alias operador | Qué hace | Órdenes al venue |
|------|----------------|----------|------------------|
| **TESTER** | tester / offline | Fake backends, datasets locales, sims deterministas | Nunca |
| **PAPER** | **REAL** (producto) | MD/cuenta reales (o sandbox) + **fills simulados** | Nunca |
| **LIVE** | live | MD + envío real de órdenes | Solo tras flip explícito + checklist |

> **REAL = PAPER con conectividad real de MD/cuenta. REAL ≠ LIVE.**

---

## 2. DoD

- [x] `OperatingMode` + `ModeGuard` fail-closed
- [x] Paquete `src/quantlab/brokers/` con `BrokerPort`, registry, PaperBroker, journal
- [x] Adapter A3 vía port (MD + account read; órdenes venue bloqueadas)
- [x] Segundo venue skeleton + Fake (`binance`)
- [x] Docs + DEC-054…060
- [x] `docs/ops/LIVE_FLIP_CHECKLIST.md` (flip **no** ejecutado)
- [x] Health reporta `operating_mode`
- [x] Invariante: `LIVE_BLOCKED is True`

## 3. Fuera de alcance

- UI / workbench (F20)
- Chat IA (F22)
- Flip real de `LIVE_BLOCKED`
- SDKs Binance/IBKR production-ready

## 4. QA

```bash
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab
uv run pytest -q
uv run quantlab-health
```
