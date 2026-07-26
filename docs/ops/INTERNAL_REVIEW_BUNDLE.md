# Internal Review Bundle — evidencia F19–F26 (Meta-Auditor)

Tooling **ligero** para empaquetar evidencia INTERNAL de fases 19–26.
**No** emite `FASE_*_APPROVED.md`. **No** sustituye el Review Package oficial
(`scripts/build_review_package.py`), que es más pesado (tests/coverage/calidad).

`LIVE_BLOCKED` permanece intacto.

## Comando

```bash
uv run python scripts/build_internal_review_bundle.py
# equivalente:
uv run python scripts/build_internal_review_bundle.py --from-phase 19 --to-phase 26
```

Salida (fuera de `src/`, en `reports/`):

| Artefacto | Descripción |
|-----------|-------------|
| `reports/QuantLab_Internal_Review_F19_F26_v{version}.zip` | Bundle documental |
| `reports/QuantLab_Internal_Review_F19_F26_v{version}.zip.sha256` | Sidecar SHA-256 |
| `reports/QuantLab_Internal_Review_F19_F26_v{version}_MANIFEST.json` | Manifest JSON |

`{version}` se lee de `quantlab.__version__` (`src/quantlab/__init__.py`).

## Contenido típico del ZIP

- `docs/FASE_XX_*.md` (XX en el rango)
- `docs/audit/AUTO_AUDIT_*FXX*`
- `docs/audit/INTERNAL_AUDIT_FXX*`
- `docs/audit/INTERNAL_AUDIT_*ARC*` / `*NIGHT*` que solapan el rango
- `docs/audit/FASE_XX_REVIEW_PACKAGE*` / `FASE_XX_IMPLEMENTATION_REPORT*`
- `RESUMEN_PROYECTO.txt`
- `docs/audit/MAPA_FASES_PARA_AUDITOR.md`
- `docs/ROADMAP_ALIGNED.md` (full)
- `docs/ops/LIVE_FLIP_CHECKLIST.md`
- Manifest JSON (también en `reports/` del ZIP)

## Exclusiones

- `FASE_*_APPROVED.md` (nunca; este bundle no certifica)
- `.env`, `*.secret`, tokens de sync
- `data/`
- `__pycache__` y caches de tooling

## Manifest

Campos relevantes:

- `bundle_kind`: `INTERNAL_REVIEW`
- `quantlab_version`
- `git_tip_sha`
- `from_phase` / `to_phase`
- `files`: lista de rutas relativas incluidas

## Git / tamaño

`reports/*` ya está en `.gitignore` (salvo `.gitkeep`). **No** commitear el ZIP
si supera ~5 MB. El sidecar `.sha256` también queda bajo `reports/` (ignorado);
regeneralo con el comando de arriba.

## Tests

```bash
uv run pytest tests/unit/scripts/test_internal_review_bundle.py -q
```

## Relación con el Review Package oficial

| | Internal Review Bundle | Review Package oficial |
|--|------------------------|------------------------|
| Propósito | Evidencia INTERNAL rápida | Entrega auditable completa |
| Tests/coverage | No | Sí (autoritativo) |
| Emite `FASE_*_APPROVED` | **No** | No (lo emite Meta-Auditor) |
| Tiempo | Segundos | Minutos |

Para Meta-Auditor externo: usar este ZIP como paquete de evidencia INTERNAL;
el certificado `FASE_*_APPROVED.md` lo emite solo el Meta-Auditor.
