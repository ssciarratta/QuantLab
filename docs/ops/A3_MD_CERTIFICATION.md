# Runbook — A3 MD Certification

## Lane fake (CI obligatoria)

```bash
uv run python scripts/a3_md_certify.py \
  --lane fake \
  --output reports/certification/a3-md-cert.json
```

Debe terminar con código 0 y `status=PASS`, `write_calls=0`,
`live_blocked=true`. No requiere `.env`, credenciales ni red.

## Lane sandbox (opt-in manual)

Configurar las variables en el entorno del proceso, sin escribir secretos en
argumentos, logs ni reportes:

```text
QUANTLAB_RUN_A3_SANDBOX_CERT=1
QUANTLAB_A3_MD_READONLY=1
QUANTLAB_A3_ENVIRONMENT=simulation
QUANTLAB_A3_USER=<secret>
QUANTLAB_A3_PASSWORD=<secret>
QUANTLAB_A3_ACCOUNT=<secret>
QUANTLAB_A3_TOKEN=<optional-secret>
```

Ejecutar:

```bash
uv run python scripts/a3_md_certify.py \
  --lane sandbox \
  --timeout 30 \
  --output reports/certification/a3-md-sandbox-cert.json
```

Sandbox corre en un worker subprocess con entorno allowlisted. No hay fallback:
una configuración incompleta, environment distinto de `simulation`, error de
backend o timeout produce `FAIL`. Sin `QUANTLAB_RUN_A3_SANDBOX_CERT=1`, produce
`SKIPPED_NOT_REQUESTED` y exit 2.

`--lane all` permite que fake PASS + sandbox SKIPPED termine 0, pero conserva el
skip explícito en el JSON. Nunca interpretar ese resultado como sandbox PASS.

## Seguridad y diagnóstico

- No usar `production`; se rechaza antes de connect.
- No pegar el entorno ni stderr del proveedor en tickets.
- El JSON permitido no contiene account IDs, secretos ni payloads raw.
- Todo resultado con `write_calls!=0` es FAIL.
- `LIVE_BLOCKED=True` es requisito; este runbook no autoriza su modificación.
