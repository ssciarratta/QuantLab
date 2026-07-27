# Milestone Freeze — Arco Guided Lab v1.00 (F99–F109)

**Fecha:** 2026-07-27  
**Versión tip:** 1.00.0 · **Fase:** F110  
**Branch:** `cursor/modo-real-workbench-aafd`  
**LIVE_BLOCKED:** True (sin unlock)  
**Estado:** freeze documental · sin `FASE_110_APPROVED.md`

---

## 1. Alcance congelado

Camino producto **Guided Lab** completo (paper + LIVE gated + A3):

| Fase | Tema | Ver | Notas |
|------|------|-----|-------|
| F99 | Guided Lab MVP wizard | 0.91.0 | venue → scan → estrategia → paper |
| F100 | LIVE credential gate + MD público | 0.92.0 | unlock/lock/status |
| F101 | Demo routing local post-unlock | 0.93.0 | `/api/live/demo/submit` |
| F102 | Spot Testnet opt-in | 0.94.0 | flag+keys |
| F103 | Freeze arco LIVE F99–F102 | 0.95.0 | doc |
| F104 | Guided Lab A3 paper connect | 0.96.0 | connect + instrumentos |
| F105 | A3 MD env Guided Lab | 0.97.0 | md-status + md_source |
| F106 | A3 snapshot MD | 0.98.0 | broker snapshot |
| F107 | A3 paper submit | 1.00.0 | POST /api/paper/submit |
| F108 | i18n + venue-aware UX | 1.00.0 | es/en guided_lab.* |
| F109 | LIVE demo cancel/LIMIT/mirror | 1.00.0 | deuda LIVE cerrada |

Congelado junto con tip F110 en **1.00.0**.

## 2. Invariantes Zero-Trust (no negociar)

1. Sin unlock: routing LIVE bloqueado
2. Secrets solo env local; nunca git ni activity log con passwords
3. Default transport demo: `local_demo_sim`
4. Testnet: `QUANTLAB_DEMO_USE_TESTNET=1` + `BINANCE_DEMO_*`
5. Rechazo explícito de `api.binance.com`
6. `live_routing=False` en APIs demo
7. A3 / paper: PaperBroker; sin routing venue A3
8. Mirror demo→journal opt-in (`mirror_to_paper`); source `binance_demo`
9. Sin emitir `FASE_99`…`FASE_110_APPROVED.md` desde INTERNAL

## 3. Operación Guided Lab

1. Elegir venue (binance / paper / a3)
2. Opcional: unlock LIVE (env user/pass)
3. Binance: scan MD → demo order (MARKET/LIMIT) → cancel open → mirror journal
4. A3: connect paper → MD status → instrumentos → snapshot → paper submit
5. Lock LIVE al terminar

Docs: `docs/ops/LIVE_CREDENTIAL_GATE.md`

## 4. Fuera de alcance (post v1.00)

- Producción Binance (`api.binance.com`)
- Certificados externos Meta-Auditor F19+
- Flip LIVE producción (checklist + dueño)
