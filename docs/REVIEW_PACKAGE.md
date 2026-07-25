# Review Package — Guía operativa

## Comando oficial (auditable)

```bash
uv sync --frozen --extra dev
uv run python scripts/build_review_package.py --phase 2 --version 1.3
```

**No usar `--skip-tests` para entregas auditables.** Ese flag produce únicamente:

`QuantLab_Review_Fase_XX_vY.Y.NON_AUTHORITATIVE.zip`

con métricas marcadas `authoritative=false`.

## Fuente única de métricas

`QualitySummary` (`scripts/review_package_quality.py`) se materializa en:

- `reports/quality_summary.json`
- `reports/pytest_junit.xml` (conteo de tests)
- `reports/coverage.xml` (cobertura)

`PROJECT_STATUS.md`, `REVIEW_REQUEST.md` y `REVIEW_PACKAGE_MANIFEST.json`
se generan/actualizan **desde** esa fuente. No se recalcula el conteo con
`pytest --collect-only`.

## Pipeline (dos pasadas)

1. Calidad (ruff, format, mypy, pytest+JUnit+coverage, vertical slice)
2. Secret scan
3. ZIP **provisional** (temp) → validación estructural
4. Escribir `reports/review_package_validation.txt` con evidencia completa
5. Regenerar manifiesto
6. ZIP **final**
7. Revalidar miembros idénticos a la pasada provisional
8. Sidecar `.sha256` + reporte externo `.validation.txt`

## Qué va dentro vs fuera del ZIP

| Artefacto | Ubicación | Contenido |
|-----------|-----------|-----------|
| ZIP | raíz | proyecto + reportes + validación **estructural** |
| `*.zip.sha256` | fuera | SHA-256 de los bytes finales del ZIP |
| `*.validation.txt` | fuera | validación del byte stream + SHA-256 |

**No es posible** incluir el hash final del ZIP dentro del propio ZIP: al
añadirlo cambiarían los bytes y el hash quedaría inválido (dependencia circular).

El reporte incluido demuestra `validation=PASS` estructural (miembros, exclusiones,
secretos, extracción). El SHA-256 autoritativo vive solo en el sidecar.
