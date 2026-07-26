#!/usr/bin/env python3
"""Empaqueta evidencia INTERNAL F19–F88 para Meta-Auditor externo.

NO emite ni incluye certificados ``FASE_*_APPROVED.md``.
NO corre el Review Package oficial (pesado). Solo evidencia documental.

Uso:
  uv run python scripts/build_internal_review_bundle.py
  uv run python scripts/build_internal_review_bundle.py --from-phase 19 --to-phase 48
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

GENERATOR_VERSION = "1.0.0"
DEFAULT_FROM_PHASE = 19
DEFAULT_TO_PHASE = 88

# Nunca empaquetar certificados externos (ni aunque existan por error).
EXCLUDE_APPROVED_RE = re.compile(r"(?i)FASE_.*_APPROVED\.md$")

EXCLUDE_DIR_NAMES = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "data",
        "node_modules",
    }
)

EXCLUDE_FILE_NAMES = frozenset(
    {
        ".env",
        ".DS_Store",
        "Thumbs.db",
        "sync_token.txt",
        "sync_approved.txt",
    }
)

EXCLUDE_SUFFIXES = frozenset({".pyc", ".pyo", ".pyd", ".secret", ".env"})


@dataclass(frozen=True, slots=True)
class BundleResult:
    zip_path: Path
    sha256_path: Path
    manifest_path: Path
    version: str
    git_sha: str
    member_count: int
    files: tuple[str, ...]


class InternalBundleError(RuntimeError):
    """Error fatal al construir el bundle INTERNAL."""


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def utc_now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_quantlab_version(root: Path) -> str:
    init_py = root / "src" / "quantlab" / "__init__.py"
    text = init_py.read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
    if not match:
        raise InternalBundleError(f"No se pudo leer __version__ desde {init_py}")
    return match.group(1)


def git_tip_sha(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return f"unavailable:{exc}"
    if result.returncode != 0:
        return "unavailable"
    return (result.stdout or "").strip() or "unavailable"


def phase_token(phase: int) -> str:
    return f"F{phase:02d}" if phase < 100 else f"F{phase}"


def phase_doc_prefix(phase: int) -> str:
    return f"FASE_{phase:02d}_"


def _is_excluded_path(path: Path, root: Path) -> bool:
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        return True
    parts = rel.parts
    if any(part in EXCLUDE_DIR_NAMES for part in parts[:-1]):
        return True
    if path.name in EXCLUDE_FILE_NAMES:
        return True
    if any(path.name.endswith(suf) for suf in EXCLUDE_SUFFIXES):
        return True
    if EXCLUDE_APPROVED_RE.search(path.name):
        return True
    # Nunca incluir data/ ni .env en cualquier profundidad.
    return bool(parts and parts[0] == "data")


def _safe_add(candidates: set[Path], path: Path, root: Path) -> None:
    if not path.is_file():
        return
    if _is_excluded_path(path, root):
        return
    candidates.add(path.resolve())


def _matches_phase_token(name: str, from_phase: int, to_phase: int) -> bool:
    """True si el nombre menciona alguna fase en el rango (F19 / FASE_19 / etc.)."""
    upper = name.upper()
    for phase in range(from_phase, to_phase + 1):
        tok = phase_token(phase)
        doc = phase_doc_prefix(phase)
        if tok in upper or doc in upper:
            return True
        # AUTO_AUDIT_*_F19.md style already covered by tok
    return False


def _arc_or_night_relevant(name: str, from_phase: int, to_phase: int) -> bool:
    """INTERNAL_AUDIT_*ARC* / *NIGHT* overlapping the phase window."""
    upper = name.upper()
    if "INTERNAL_AUDIT" not in upper:
        return False
    if "ARC" not in upper and "NIGHT" not in upper:
        return False
    # Prefer explicit phase tokens in the filename.
    if _matches_phase_token(name, from_phase, to_phase):
        return True
    # Range forms like F19_F26 / F19_F25 — include if any endpoint overlaps.
    range_hits = re.findall(r"F(\d{2})", upper)
    if not range_hits:
        return False
    nums = [int(x) for x in range_hits]
    return any(from_phase <= n <= to_phase for n in nums)


def collect_bundle_files(
    root: Path,
    *,
    from_phase: int,
    to_phase: int,
) -> list[Path]:
    if from_phase > to_phase:
        raise InternalBundleError("--from-phase must be <= --to-phase")
    if from_phase < 1 or to_phase > 99:
        raise InternalBundleError("phase range must be within 1..99")

    candidates: set[Path] = set()

    # docs/FASE_XX_*.md (fase docs en docs/)
    docs_dir = root / "docs"
    if docs_dir.is_dir():
        for phase in range(from_phase, to_phase + 1):
            prefix = phase_doc_prefix(phase)
            for path in docs_dir.glob(f"{prefix}*.md"):
                _safe_add(candidates, path, root)

    audit_dir = root / "docs" / "audit"
    if audit_dir.is_dir():
        for path in audit_dir.iterdir():
            if not path.is_file():
                continue
            name = path.name
            # Explicitly never pick APPROVED certificates.
            if EXCLUDE_APPROVED_RE.search(name):
                continue

            upper = name.upper()
            include = False

            # AUTO_AUDIT_*FXX*
            if "AUTO_AUDIT" in upper and _matches_phase_token(name, from_phase, to_phase):
                include = True

            # INTERNAL_AUDIT_FXX* (per-phase) and range ARC/NIGHT
            if "INTERNAL_AUDIT" in upper:
                if _matches_phase_token(name, from_phase, to_phase):
                    include = True
                if _arc_or_night_relevant(name, from_phase, to_phase):
                    include = True

            # FASE_XX_REVIEW_PACKAGE* / IMPLEMENTATION_REPORT*
            if (
                upper.startswith("FASE_")
                and ("REVIEW_PACKAGE" in upper or "IMPLEMENTATION_REPORT" in upper)
                and _matches_phase_token(name, from_phase, to_phase)
            ):
                include = True

            if include:
                _safe_add(candidates, path, root)

    # Context docs (full)
    for rel in (
        "RESUMEN_PROYECTO.txt",
        "PROJECT_MEMORY.md",
        "docs/audit/MAPA_FASES_PARA_AUDITOR.md",
        "docs/ROADMAP_ALIGNED.md",
        "docs/ops/LIVE_FLIP_CHECKLIST.md",
    ):
        _safe_add(candidates, root / rel, root)

    # Stable ordering by relative path
    ordered = sorted(candidates, key=lambda p: str(p.relative_to(root)).replace("\\", "/"))
    return ordered


def relative_arcname(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def write_manifest(
    path: Path,
    *,
    version: str,
    git_sha: str,
    from_phase: int,
    to_phase: int,
    files: Iterable[str],
    zip_name: str,
) -> dict[str, object]:
    file_list = list(files)
    payload: dict[str, object] = {
        "bundle_kind": "INTERNAL_REVIEW",
        "generator": "scripts/build_internal_review_bundle.py",
        "generator_version": GENERATOR_VERSION,
        "quantlab_version": version,
        "git_tip_sha": git_sha,
        "from_phase": from_phase,
        "to_phase": to_phase,
        "created_at_utc": utc_now_iso(),
        "zip_name": zip_name,
        "notes": [
            "Evidencia INTERNAL only — NO sustituye Review Package oficial.",
            "NO incluye ni emite FASE_*_APPROVED.md.",
            "LIVE_BLOCKED permanece intacto.",
        ],
        "file_count": len(file_list),
        "files": file_list,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def build_bundle(
    root: Path,
    *,
    from_phase: int = DEFAULT_FROM_PHASE,
    to_phase: int = DEFAULT_TO_PHASE,
    output_dir: Path | None = None,
) -> BundleResult:
    version = read_quantlab_version(root)
    git_sha = git_tip_sha(root)
    files = collect_bundle_files(root, from_phase=from_phase, to_phase=to_phase)
    if not files:
        raise InternalBundleError("No se encontraron archivos para el bundle")

    out_dir = output_dir or (root / "reports")
    out_dir.mkdir(parents=True, exist_ok=True)

    zip_name = f"QuantLab_Internal_Review_F{from_phase:02d}_F{to_phase:02d}_v{version}.zip"
    zip_path = out_dir / zip_name
    sha_path = Path(str(zip_path) + ".sha256")
    manifest_name = (
        f"QuantLab_Internal_Review_F{from_phase:02d}_F{to_phase:02d}_v{version}_MANIFEST.json"
    )
    manifest_path = out_dir / manifest_name

    rel_files = [relative_arcname(p, root) for p in files]
    # Guard: never ship APPROVED certificates
    bad = [r for r in rel_files if EXCLUDE_APPROVED_RE.search(Path(r).name)]
    if bad:
        raise InternalBundleError(f"APPROVED files leaked into bundle: {bad}")

    write_manifest(
        manifest_path,
        version=version,
        git_sha=git_sha,
        from_phase=from_phase,
        to_phase=to_phase,
        files=rel_files,
        zip_name=zip_name,
    )

    # Include manifest inside the ZIP as well.
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path, arc in zip(files, rel_files, strict=True):
            zf.write(path, arcname=arc)
        zf.write(manifest_path, arcname=f"reports/{manifest_name}")

    digest = sha256_file(zip_path)
    sha_path.write_text(f"{digest}  {zip_name}\n", encoding="utf-8")

    members = tuple(rel_files) + (f"reports/{manifest_name}",)
    return BundleResult(
        zip_path=zip_path,
        sha256_path=sha_path,
        manifest_path=manifest_path,
        version=version,
        git_sha=git_sha,
        member_count=len(members),
        files=members,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Empaqueta evidencia INTERNAL (docs/audit) F19–F37 para Meta-Auditor. "
            "No emite FASE_*_APPROVED.md ni corre el Review Package oficial."
        )
    )
    parser.add_argument(
        "--from-phase",
        type=int,
        default=DEFAULT_FROM_PHASE,
        help=f"Fase inicial inclusive (default {DEFAULT_FROM_PHASE})",
    )
    parser.add_argument(
        "--to-phase",
        type=int,
        default=DEFAULT_TO_PHASE,
        help=f"Fase final inclusive (default {DEFAULT_TO_PHASE})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directorio de salida (default: <root>/reports)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = project_root()
    try:
        result = build_bundle(
            root,
            from_phase=args.from_phase,
            to_phase=args.to_phase,
            output_dir=args.output_dir,
        )
    except InternalBundleError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"zip:      {result.zip_path}")
    print(f"sha256:   {result.sha256_path}")
    print(f"manifest: {result.manifest_path}")
    print(f"version:  {result.version}")
    print(f"git:      {result.git_sha}")
    print(f"members:  {result.member_count}")
    print("note:     INTERNAL evidence only — FASE_*_APPROVED.md NOT emitted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
