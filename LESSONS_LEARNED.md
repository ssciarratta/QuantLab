# QuantLab — Lessons Learned

**Fase:** 3 — Data Layer + A3  
**Fecha:** 2026-07-24  
**Estado:** Pendiente de auditoría v1.0

---

## Qué salió bien

1. **Arquitectura v1.1 como guía estricta.**
2. **Dataclasses frozen + invariantes.**
3. **Vertical slice obligatorio.**
4. **CI desde día uno.**
5. **Política única de exclusiones** (Review Package).
6. **Métricas autoritativas JUnit/coverage** (v1.3).
7. **Anticorrupción A3** — Fake backend permite CI sin credenciales.
8. **Gates de producción apilados** — imposible “olvidar” un flag.

---

## Qué salió mal / fricciones

1. **Review Package v1.1 incluyó `__pycache__/`.**
2. **Review Package v1.2: test_count=0** — corregido en v1.3 (DEC-039).
3. **Token en `requirements.txt` legacy** — eliminado; rotar si estuvo en remoto.
4. **pyRofex sin OHLCV nativo** — hay que construir barras desde trades (DEC-043).
5. **Cobertura inicial cayó al agregar CLI/client live** — omitidos del gate (frontera).

---

## Qué aprendimos

1. El conteo de tests debe salir de un reporte estructurado de la misma corrida PASS.
2. No se puede meter el SHA del ZIP dentro del ZIP.
3. Separar Data Plane / Execution Plane desde el día 1 evita acoplar market data a órdenes.
4. Docs de discovery antes de código reducen sorpresas de API externa.

---

## Deuda técnica registrada

- Processed JSONL (Parquet/DuckDB)
- Simulation tests reMarkets opt-in
- Observabilidad / reconciliación ampliada
- Schemas YAML / from_dict completo

---

*Actualizado PROMPT 007 — esperando auditoría GPT Fase 3.*
