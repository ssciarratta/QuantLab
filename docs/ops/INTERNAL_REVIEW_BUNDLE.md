# Internal Review Bundle — evidencia F19–F29 (Meta-Auditor)

Tooling **ligero** para empaquetar evidencia INTERNAL de fases 19–29.
**No** emite `FASE_*_APPROVED.md`. **No** sustituye el Review Package oficial
(`scripts/build_review_package.py`), que es más pesado (tests/coverage/calidad).

`LIVE_BLOCKED` permanece intacto.

## Comando

```bash
uv run python scripts/build_internal_review_bundle.py
# equivalente:
uv run python scripts/build_internal_review_bundle.py --from-phase 19 --to-phase 29
```

Salida (fuera de `src/`, en `reports/`):

| Artefacto | Descripción |
|-----------|-------------|
| `reports/QuantLab_Internal_Review_F19_F29_v{version}.zip` | Bundle documental |
| `reports/QuantLab_Internal_Review_F19_F29_v{version}.zip.sha256` | Sidecar SHA-256 |
| `reports/QuantLab_Internal_Review_F19_F29_v{version}_MANIFEST.json` | Manifest JSON |

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

- Cualquier `FASE_*_APPROVED.md`
- `.env`, secretos, `data/`, caches, `__pycache__`
- Artefactos de build pesados

## Defaults

- `--from-phase 19`
- `--to-phase 29` (`DEFAULT_TO_PHASE`)

## Notas

`reports/*` ya está en `.gitignore` (salvo `.gitkeep`). **No** commitear el ZIP
si supera ~5 MB. El sidecar `.sha256` también queda bajo `reports/` (ignorado);
el digest se documenta en `INTERNAL_AUDIT_F19_F29_NIGHT.md`.
