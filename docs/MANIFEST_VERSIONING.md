# Política de versionado de Manifests

**Estado:** Norma Fase 2 (antes de persistencia de datasets en Fase 3)  
**Decisión relacionada:** DEC-036  
**Aplica a:** `DatasetManifest`, `ExperimentManifest` y futuros manifests

---

## Schema version

Cada manifest **debe** incluir explícitamente una versión de esquema:

```text
schema_version = "1.0"
```

No confundir:

| Concepto | Significado |
|----------|-------------|
| **schema_version** | Forma y semántica de los campos del manifest |
| **dataset version** | Versión del contenido de datos (`DatasetManifest.version`) |
| **experiment id / versión de estrategia** | Identidad de una corrida o de código de estrategia |
| **QuantLab version** | Versión del paquete Python (`pyproject.toml`) |

---

## Compatibilidad (SemVer del schema)

- **Patch** (`1.0` → `1.0.1` o documentación equivalente): correcciones compatibles (clarificaciones, validaciones más estrictas sobre datos ya inválidos).
- **Minor** (`1.0` → `1.1`): campos **opcionales** nuevos; lectores de `1.0` pueden ignorarlos.
- **Major** (`1.x` → `2.0`): cambios incompatibles (renombre/eliminación de campos, cambio de semántica).

---

## Lectura

| Situación | Comportamiento esperado |
|-----------|-------------------------|
| Versión conocida actual | Lectura normal |
| Versión anterior compatible (mismo major, minor/patch ≤ actual) | Lectura; opcionalmente normalizar a vista canónica en memoria **sin** reescribir el archivo |
| Versión futura desconocida | **Rechazar** con error explícito (no adivinar) |
| Major incompatible | **Rechazar** o exigir migración explícita |
| Manifest sin `schema_version` | **Rechazar** |

---

## Migraciones

Las migraciones futuras deben ser:

- **Explícitas** (comando o función nombrada, no “upgrade silencioso”)
- **Deterministas**
- **Testeadas**
- **Auditables** (log / manifiesto de migración)
- **No destructivas** sobre el archivo original (escribir nuevo artefacto o nueva versión)

No se implementa un framework complejo de migraciones en Fase 2.

---

## Serialización canónica

- Formato: JSON UTF-8 (o dict equivalente en memoria)
- Orden de claves: **determinista** (ordenado)
- Timestamps: ISO-8601 con timezone (aware); naive **prohibido**
- Decimales: representación textual fija (`format(value, "f")`)
- Opcionales ausentes: omitir o `null` de forma consistente por tipo (documentar por campo en cambios minor)
- Checksum: hexadecimal, longitud ≥ 16
- Encoding: UTF-8 sin BOM
- Rutas y símbolos: strings normalizados (sin alterar significado de negocio)

---

## Inmutabilidad histórica

Una vez que un manifest identifica un dataset o experimento usado:

- **No** modificar el archivo persistido en silencio
- Todo cambio material produce:
  - nueva versión de dataset/experimento, **o**
  - nuevo identificador, **o**
  - migración explícita documentada

El Review Package y la CI deben tratar los manifests de ejemplo/sintéticos de Fase 2 como contratos de forma, no como datasets productivos.
