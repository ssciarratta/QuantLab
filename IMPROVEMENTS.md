# IMPROVEMENTS — Fase 2 v1.2

**Fecha:** 2026-07-24

## Qué funcionó
- Política centralizada + validación post-ZIP eliminó caches del paquete.
- Invariantes en `__post_init__` suben la calidad de contrato sin Fase 3.
- `uv.lock` cierra la deuda de reproducibilidad de deps.

## Qué no funcionó / fricciones
- Incluir el SHA del ZIP dentro del propio ZIP es imposible sin invalidarlo; sidecar obligatorio.
- `requirements.txt` legacy contenía URL con token (eliminado); rotar credencial si llegó a remoto.

## Riesgos
- Secret scan por regex es necesario pero incompleto.
- Migraciones de manifests aún no implementadas (solo política).

## Mejoras futuras
- Acción CI que falle si `git ls-files` encuentra bytecode (ya añadido).
- En Fase 3: `from_dict` + persistencia con schema_version.
