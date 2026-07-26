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

---

## Fase 87 — Broker Plugin Contract v1 (2026-07-26)

1. Capturar `TypeError` alrededor de una factory y reintentar con otra firma
   oculta bugs internos y puede duplicar efectos. Validar con
   `inspect.signature().bind()` antes de una única invocación.
2. Una política read-only documentada no es una frontera. El registry debe
   retornar siempre un wrapper que no delegue submit/cancel.
3. Un test kit de plugins puede validar contrato y fixtures offline, pero no
   convierte código Python de terceros en seguro: no reemplaza sandbox ni
   revisión de confianza.
4. La metadata versionada y un allowlist de capabilities hacen explícita la
   compatibilidad y rechazan ejecución por default.

---

## Fase 88 — Paper Journal authoritative + reconciliation (2026-07-26)

1. Persistir primero una proyección mutable crea un estado durable que el log no
   puede explicar. El único commit seguro es append+fsync del journal antes del
   book.
2. Una copia de preview evita descubrir cash/short inválido después de haber
   escrito el fill autoritativo.
3. Atomic replace protege la integridad física del book, pero no su integridad
   lógica; el checkpoint y el replay exacto cubren esa segunda dimensión.
4. La recuperación automática oculta incidentes. Para PAPER se prefirió
   fail-closed + backup + rebuild CLI offline, aun en journal-ahead demostrable.
5. Un reader “tolerante” de JSONL convierte corrupción en pérdida silenciosa:
   línea, tipos, timezone, finitud, source y duplicados deben validarse.

---

## Fase 89 — A3 MD read-only certification (2026-07-26)

1. Una lane opt-in omitida debe reportar skip explícito; llamarla PASS crea una
   certificación ficticia.
2. Un fallback útil para UX normal es inseguro en certificación: la lane strict
   debe fallar antes que sustituir pyRofex por fake.
3. La seguridad read-only se prueba con write-bomb y contador, no sólo por
   ausencia aparente de llamadas en el happy path.
4. El reporte de integración debe usar códigos y agregados allowlisted; propagar
   excepciones o payloads del proveedor puede filtrar identidad/secretos.
5. Production se rechaza antes de connect y sandbox se aísla en subprocess con
   timeout y entorno mínimo.

---

## Portabilidad Windows post-F88 (2026-07-26)

La rama se desarrolló en Linux (cloud); al correr en Windows aparecieron 4
fallos que la suite Linux no podía detectar:

1. `with sqlite3.Connection` delimita transacción pero **no cierra** la
   conexión; en Windows el archivo queda bloqueado (WinError 32) y rompe el
   cleanup de `TemporaryDirectory`. Usar `contextlib.closing()` siempre.
2. Validar path traversal con prefijo string `"/"` es POSIX-only. Comparar
   `Path.parent == root` (o `Path.is_relative_to`) es portable.
3. `os.fsync` sobre un handle abierto `"rb"` falla en Windows (exige acceso
   de escritura). Abrir `"rb+"`.
4. `/tmp` hardcodeado no existe en Windows; usar `tempfile.gettempdir()` o
   el fixture `tmp_path`.

Regla futura: todo smoke/test nuevo usa paths temporales portables y toda
conexión sqlite se cierra explícitamente.
