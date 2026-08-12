"""Docs / Help browser — lista y lee markdown bajo ``docs/`` (F38).

Paths relativos safe: ``*.md`` en raíz ``docs/`` y subdirs allowlist
(``ops``, ``manuales``, ``montecarlo``, ``scanner``).
Path traversal y escapes fuera de ``docs/`` → fail-closed.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_DOCS_ROOT = _REPO_ROOT / "docs"

# Subdirs relativas permitidas ("" = raíz docs/).
_ALLOWED_SUBDIRS: frozenset[str] = frozenset(
    {"", "ops", "manuales", "montecarlo", "scanner"}
)

_MAX_CONTENT_BYTES = 512_000


def default_docs_root() -> Path:
    """Raíz canónica ``docs/`` del repo."""
    return _DEFAULT_DOCS_ROOT


def resolve_docs_root(docs_root: Path | None = None) -> Path:
    root = docs_root if docs_root is not None else _DEFAULT_DOCS_ROOT
    return root.expanduser().resolve()


def normalize_docs_relpath(raw: str) -> str:
    """Normaliza path relativo pedido por el cliente (sin traversal)."""
    if not isinstance(raw, str):
        raise ValidationError("path de docs debe ser string")
    text = raw.strip().replace("\\", "/")
    if not text:
        raise ValidationError("path de docs vacío")
    if text.startswith("/") or text.startswith("~") or ":" in text.split("/")[0]:
        raise ValidationError(f"path absoluto rechazado: {raw!r}")
    parts = [p for p in text.split("/") if p not in ("", ".")]
    if not parts:
        raise ValidationError(f"path de docs vacío: {raw!r}")
    if any(p == ".." for p in parts):
        raise ValidationError(f"path traversal rechazado: {raw!r}")
    if any(p.startswith(".") for p in parts):
        raise ValidationError(f"path oculto/rechazado: {raw!r}")
    name = parts[-1]
    if not name.endswith(".md") or name == ".md":
        raise ValidationError(f"solo archivos .md permitidos: {raw!r}")
    if len(parts) == 1:
        return name
    if len(parts) == 2 and parts[0] in _ALLOWED_SUBDIRS - {""}:
        return f"{parts[0]}/{name}"
    allowed = ", ".join(sorted(s for s in _ALLOWED_SUBDIRS if s))
    raise ValidationError(
        f"path fuera de docs/*.md o docs/{{{allowed}}}/*.md: {raw!r}"
    )


def resolve_docs_file(relpath: str, *, docs_root: Path | None = None) -> Path:
    """Resuelve path relativo → absoluto bajo docs/; fail-closed ante escape."""
    safe_rel = normalize_docs_relpath(relpath)
    root = resolve_docs_root(docs_root)
    if not root.is_dir():
        raise ValidationError(f"docs_root inexistente: {root}")
    candidate = (root / safe_rel).resolve()
    if not candidate.is_relative_to(root):
        raise ValidationError(f"path fuera de docs/ (path traversal): {relpath!r}")
    try:
        rel = candidate.relative_to(root)
    except ValueError as exc:
        raise ValidationError(f"path fuera de docs/: {relpath!r}") from exc
    parts = rel.parts
    if len(parts) == 1 or len(parts) == 2 and parts[0] in _ALLOWED_SUBDIRS - {""}:
        pass
    else:
        allowed = ", ".join(sorted(s for s in _ALLOWED_SUBDIRS if s))
        raise ValidationError(
            f"path fuera de docs/*.md o docs/{{{allowed}}}/*.md: {relpath!r}"
        )
    if not candidate.is_file():
        raise ValidationError(f"doc no encontrado: {safe_rel}")
    if candidate.suffix.lower() != ".md":
        raise ValidationError(f"solo archivos .md permitidos: {safe_rel}")
    return candidate


def list_docs(*, docs_root: Path | None = None) -> dict[str, Any]:
    """Lista ``docs/*.md`` y subdirs allowlist (paths relativos safe)."""
    root = resolve_docs_root(docs_root)
    items: list[dict[str, Any]] = []
    if root.is_dir():
        for path in sorted(root.glob("*.md")):
            if path.is_file():
                items.append(_doc_meta(path, root, subdir=""))
        for sub in sorted(s for s in _ALLOWED_SUBDIRS if s):
            folder = root / sub
            if folder.is_dir():
                for path in sorted(folder.glob("*.md")):
                    if path.is_file():
                        items.append(_doc_meta(path, root, subdir=sub))
    return {
        "ok": True,
        "kind": "docs",
        "docs_root": str(root),
        "count": len(items),
        "docs": items,
        "allowed_subdirs": sorted(s for s in _ALLOWED_SUBDIRS if s),
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }


def read_docs_content(relpath: str, *, docs_root: Path | None = None) -> dict[str, Any]:
    """Lee markdown solo bajo docs/ (path traversal fail-closed)."""
    path = resolve_docs_file(relpath, docs_root=docs_root)
    root = resolve_docs_root(docs_root)
    size = path.stat().st_size
    if size > _MAX_CONTENT_BYTES:
        raise ValidationError(f"doc demasiado grande ({size} bytes > {_MAX_CONTENT_BYTES})")
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise ValidationError(f"no se pudo leer doc: {exc}") from exc
    safe_rel = str(path.relative_to(root)).replace("\\", "/")
    subdir = safe_rel.split("/", 1)[0] if "/" in safe_rel else ""
    return {
        "ok": True,
        "kind": "docs_content",
        "path": safe_rel,
        "name": path.name,
        "subdir": subdir,
        "size": size,
        "content": text,
        "html": markdown_to_simple_html(text),
        "docs_root": str(root),
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }


def search_docs_files(
    query: str, *, docs_root: Path | None = None, limit: int = 8
) -> dict[str, Any]:
    """Busca keywords en docs allowlist (chat search_docs)."""
    if not isinstance(query, str):
        raise ValidationError("search_docs: query debe ser string")
    keywords = [k for k in re.split(r"\s+", query.strip().lower()) if k]
    root = resolve_docs_root(docs_root)
    if not keywords:
        return {
            "query": "",
            "matches": [],
            "docs_root": str(root),
            "live_blocked": LIVE_BLOCKED is True,
        }
    listed = list_docs(docs_root=root)
    matches: list[dict[str, Any]] = []
    for item in listed["docs"]:
        rel = str(item["path"])
        try:
            path = resolve_docs_file(rel, docs_root=root)
            text = path.read_text(encoding="utf-8", errors="replace")
        except (OSError, ValidationError):
            continue
        lower = text.lower()
        hits = [kw for kw in keywords if kw in lower]
        if not hits:
            continue
        matches.append(
            {
                "file": rel,
                "path": rel,
                "hits": hits,
                "snippet": _snippet_for(text, hits[0]),
            }
        )
        if len(matches) >= max(1, limit):
            break
    return {
        "query": " ".join(keywords),
        "matches": matches,
        "docs_root": str(root),
        "live_blocked": LIVE_BLOCKED is True,
    }


def markdown_to_simple_html(text: str) -> str:
    """Markdown→HTML mínimo: escape HTML + headings/listas/código/énfasis."""
    escaped = html.escape(text, quote=True)
    lines = escaped.splitlines()
    out: list[str] = []
    in_ul = False
    in_code = False
    code_buf: list[str] = []

    def close_ul() -> None:
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    for line in lines:
        if line.strip().startswith("```"):
            if in_code:
                out.append('<pre class="docs-code mono">' + "\n".join(code_buf) + "</pre>")
                code_buf = []
                in_code = False
            else:
                close_ul()
                in_code = True
            continue
        if in_code:
            code_buf.append(line)
            continue

        stripped = line.lstrip()
        if stripped.startswith("#"):
            close_ul()
            hashes = 0
            while hashes < len(stripped) and stripped[hashes] == "#":
                hashes += 1
            level = min(max(hashes, 1), 4)
            title = stripped[hashes:].strip()
            out.append(f"<h{level}>{_inline_md(title)}</h{level}>")
            continue
        if stripped.startswith("- ") or stripped.startswith("* "):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{_inline_md(stripped[2:].strip())}</li>")
            continue
        close_ul()
        if not stripped:
            out.append("<br/>")
        else:
            out.append(f"<p>{_inline_md(stripped)}</p>")

    if in_code:
        out.append('<pre class="docs-code mono">' + "\n".join(code_buf) + "</pre>")
    close_ul()
    return "\n".join(out)


def _inline_md(text: str) -> str:
    """Énfasis/código inline sobre texto ya escapado (sin HTML crudo)."""
    text = re.sub(
        r"`([^`]+)`",
        r'<code class="mono">\1</code>',
        text,
    )
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    return text


def _doc_meta(path: Path, root: Path, *, subdir: str) -> dict[str, Any]:
    rel = path.relative_to(root)
    rel_s = str(rel).replace("\\", "/")
    title = path.stem.replace("_", " ")
    try:
        first = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in first[:12]:
            s = line.strip()
            if s.startswith("#"):
                title = s.lstrip("#").strip() or title
                break
    except OSError:
        pass
    return {
        "path": rel_s,
        "name": path.name,
        "subdir": subdir,
        "title": title,
        "size": path.stat().st_size,
    }


def _snippet_for(text: str, keyword: str, radius: int = 80) -> str:
    lower = text.lower()
    idx = lower.find(keyword.lower())
    if idx < 0:
        return text[:160].replace("\n", " ").strip()
    start = max(0, idx - radius)
    end = min(len(text), idx + len(keyword) + radius)
    chunk = text[start:end].replace("\n", " ").strip()
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{chunk}{suffix}"
