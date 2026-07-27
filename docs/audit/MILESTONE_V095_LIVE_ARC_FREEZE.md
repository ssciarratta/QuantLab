# Milestone Freeze — Arco LIVE Guided Path v0.95 (F99–F102)

**Fecha:** 2026-07-26  
**Versión tip:** 0.95.0 · **Fase:** F103  
**Branch:** `cursor/modo-real-workbench-aafd`  
**LIVE_BLOCKED:** True (sin unlock)  
**Estado:** freeze documental · sin `FASE_103_APPROVED.md`

---

## 1. Alcance congelado

Camino producto **Guided Lab → Binance demo** (corte humano user/pass):

| Fase | Tema | Ver | Notas |
|------|------|-----|-------|
| F99 | Guided Lab MVP wizard | 0.91.0 | venue → scan → estrategia → paper |
| F100 | LIVE credential gate + MD público | 0.92.0 | unlock/lock/status; scan Binance |
| F101 | Demo routing local post-unlock | 0.93.0 | `/api/live/demo/submit` sim |
| F102 | Spot Testnet opt-in | 0.94.0 | doble gate flag+keys; no prod |

Congelado junto con tip F103 (esta fase documental) en **0.95.0**.

## 2. Invariantes Zero-Trust (no negociar)

1. Sin unlock: routing LIVE bloqueado
2. Password / API keys: solo env local; nunca git ni activity log
3. Default transport: `local_demo_sim`
4. Testnet remoto: `QUANTLAB_DEMO_USE_TESTNET=1` + `BINANCE_DEMO_*`
5. Rechazo explícito de hosts de producción (`api.binance.com`)
6. `live_routing=False` en APIs demo (no place_order producción)
7. Sin emitir `FASE_99`…`FASE_103_APPROVED.md` desde INTERNAL

## 3. Operación

1. Set `QUANTLAB_LIVE_USER` / `QUANTLAB_LIVE_PASSWORD`
2. Guided Lab → Unlock
3. Scan Binance MD / paper sim
4. Demo order (sim local) o, si flag+keys, testnet
5. Lock para cerrar sesión

Docs: `docs/ops/LIVE_CREDENTIAL_GATE.md`

## 4. Fuera de alcance (siguiente)

- A3 live / MD cert en Guided Lab
- Producción Binance
- Certificados externos Meta-Auditor
