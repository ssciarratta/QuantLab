# QuantLab — PROJECT MEMORY (Cursor)

**Actualizado:** 2026-07-26  
**Branch trabajo:** `cursor/modo-real-workbench-aafd`  
**Versión tip:** **0.14.0**  
**LIVE:** `LIVE_BLOCKED = True` (flip **NO** ejecutado)

---

## Identidad

QuantLab = laboratorio de investigación cuantitativa (no bot de trading).  
Ejecución live / order routing venue = **bloqueado por diseño**.

---

## Estado de fases (resumen)

| Rango | Estado |
|-------|--------|
| F0–F18 | Certificados **externos** (`FASE_*_APPROVED.md`) |
| F19–F22 | **APROBADO_INTERNO** Zero-Trust; externos **pendientes** |
| Arco F19–F22 | Cerrado INTERNAL → `docs/audit/INTERNAL_AUDIT_F19_F22_ARC.md` |

**Regla:** el auditor INTERNAL **no** emite `FASE_*_APPROVED.md` (reserva Meta-Auditor externo).

---

## Arco nocturno F19–F22 (SHAs impl)

| Fase | Tema | Ver | Impl |
|------|------|-----|------|
| 19 | OperatingMode + BrokerPort; REAL=PAPER | 0.11.0 | `a5b12d3` |
| 20 | Workbench stdlib loopback + SPA WM | 0.12.0 | `cacf8e6` |
| 21 | Lab panels `/api/lab/*` | 0.13.0 | `c397ffc` |
| 22 | Chat IA allowlist + FakeProvider | 0.14.0 | `5ef9866` |

---

## Invariantes Zero-Trust (no negociar)

1. `LIVE_BLOCKED is True` en `execution/live_gate.py`
2. **REAL ≠ LIVE** — alias producto `REAL = PAPER` (MD/cuenta pueden ser reales; fills simulados)
3. Workbench bind default `127.0.0.1`; LIVE mode → 400 / CLI exit 2
4. Chat: solo tools allowlist read-only; mutaciones → `ValidationError`
5. FakeProvider = default CI; LLM solo opt-in vía env (`DISABLED` por defecto)
6. Lab demos sintéticos; export HB path-safe; `live_routing: false`

---

## Paths clave

- Roadmap: `docs/ROADMAP_ALIGNED.md`
- Mapa auditor: `docs/audit/MAPA_FASES_PARA_AUDITOR.md`
- Resumen: `RESUMEN_PROYECTO.txt`
- DECs: `learning/decisiones.txt` (DEC-054…065)
- Workbench: `src/quantlab/workbench/`
- Chat: `src/quantlab/workbench/chat/`
- Smoke: `scripts/internal_audit_smoke.py`
- Flip checklist (no ejecutar): `docs/ops/LIVE_FLIP_CHECKLIST.md`

---

## QA canónica

```bash
export PATH="$HOME/.local/bin:$PATH"
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

---

## Entry points útiles

- `quantlab-health` — ops / LIVE gate
- `quantlab-workbench` — UI local F20–F22
- `quantlab-a3` — market data A3 (anticorrupción)
- `quantlab-vertical-slice` — slice mínimo
