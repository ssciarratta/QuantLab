# Fase 59 — A11y Basics (focus + aria)

**Estado:** ✅ **APROBADO_INTERNO** (v0.51.0) — certificado externo `FASE_59_APPROVED.md` **NO** emitido  
**Base:** v0.50.0 · F58 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-103  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F59.md` · noche `INTERNAL_AUDIT_F19_F59_NIGHT.md`

## Objetivo

Mejoras de accesibilidad mínimas en el SPA estático del workbench:

- `role="dialog"` + `aria-modal` + `aria-label` en Command Palette, About y Onboarding
- `aria-label` en botones de la taskbar (inicio + ventanas)
- Focus trap básico (Tab ciclo) en Command Palette
- Skip link opcional «Ir al contenido» → `#workspace`

## DoD

- [x] Dialog roles en palette / about / onboarding (shells en `index.html` + JS)
- [x] `aria-label` en taskbar buttons
- [x] Focus trap básico en palette
- [x] Skip link «Ir al contenido»
- [x] Suite `tests/unit/workbench/test_a11y_f59.py` (`index.html` contiene aria / `role=dialog`)
- [x] Spec + IMPLEMENTATION_REPORT
- [x] Smoke F59 + bundle default F19–F59
- [x] DEC-103 · bump **0.51.0**
- [x] Sin `FASE_59_APPROVED.md` · sin LIVE

## Diseño

| Artefacto | Rol |
|-----------|-----|
| `static/index.html` | Skip link · shells `role="dialog"` · aria taskbar |
| `command_palette.js` | Focus trap Tab · `aria-modal` · restore focus |
| `about.js` / `onboarding.js` | Reusan shells HTML; refuerzan aria |
| `wm.js` | `aria-label="Ventana {title}"` en task buttons |
| `workbench.css` | `.skip-link` visible al focus |

### Skip link

```html
<a class="skip-link" href="#workspace">Ir al contenido</a>
```

Visible solo al recibir foco (teclado).

### Focus trap (palette)

Al abrir: guarda `document.activeElement`, enfoca el input, escucha `Tab`/`Shift+Tab` en captura y cicla focusables dentro del dialog. Al cerrar: restaura foco previo.

## Uso / tests

```bash
export PATH="$HOME/.local/bin:$PATH"
uv run pytest -q tests/unit/workbench/test_a11y_f59.py
```

## Fuera de alcance

LIVE · auth WAN · axe-core completo · screen-reader E2E · certificado externo `FASE_59_APPROVED.md` · flip LIVE
