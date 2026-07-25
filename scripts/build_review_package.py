#!/usr/bin/env python3
"""Generador oficial del Review Package QuantLab.

Comando (entrega auditable):
  uv run python scripts/build_review_package.py --phase 2 --version 1.3

`--skip-tests` solo produce artefactos NON_AUTHORITATIVE (no auditable).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from review_package_policy import (  # noqa: E402
    GENERATOR_VERSION,
    MAX_FILE_SIZE_BYTES,
    REQUIRED_DOC_FILES,
    REQUIRED_REPORT_FILES,
    REQUIRED_TOP_DIRS,
    REQUIRED_TOP_FILES,
    is_dangerous_arcname,
    policy_summary,
    should_exclude_relative,
)
from review_package_quality import (  # noqa: E402
    QualityError,
    QualitySummary,
    assert_document_consistency,
    parse_coverage_xml,
    parse_junit_xml,
    render_metrics_block,
    upsert_metrics_block,
    write_quality_summary_json,
)

PACKAGE_PHASE_DEFAULT = 3
PACKAGE_VERSION_DEFAULT = "1.0"
QUANTLAB_VERSION = "0.3.0"


@dataclass(frozen=True, slots=True)
class CmdResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    started_at: str


@dataclass(frozen=True, slots=True)
class ZipValidationResult:
    member_count: int
    members: tuple[str, ...]
    required_present: bool
    forbidden_absent: bool
    no_absolute_paths: bool
    no_traversal: bool
    no_symlinks: bool
    no_nested_zips: bool
    secrets_clean: bool
    extract_ok: bool
    notes: tuple[str, ...]


class ReviewPackageError(RuntimeError):
    """Error fatal en la generación o validación del Review Package."""


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_cmd(cmd: list[str], cwd: Path) -> CmdResult:
    started = utc_now().isoformat()
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return CmdResult(
        command=cmd,
        returncode=result.returncode,
        stdout=result.stdout or "",
        stderr=result.stderr or "",
        started_at=started,
    )


def write_report(path: Path, result: CmdResult, *, extra: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    verdict = "PASS" if result.returncode == 0 else "FAIL"
    body = "\n".join(
        [
            f"command: {' '.join(result.command)}",
            f"started_at_utc: {result.started_at}",
            f"exit_code: {result.returncode}",
            f"result: {verdict}",
            "",
            "----- STDOUT -----",
            result.stdout.rstrip(),
            "",
            "----- STDERR -----",
            result.stderr.rstrip(),
            "",
            extra.rstrip(),
            "",
        ]
    )
    path.write_text(body, encoding="utf-8")


def git_commit(root: Path) -> str:
    result = run_cmd(["git", "rev-parse", "HEAD"], root)
    if result.returncode != 0:
        return "unknown"
    return (result.stdout or "").strip() or "unknown"


def detect_lockfile(root: Path) -> tuple[str, str]:
    lock = root / "uv.lock"
    if not lock.exists():
        raise ReviewPackageError("Falta uv.lock (requerido para Review Package)")
    return lock.name, sha256_file(lock)


def collect_candidate_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        rel_dir = current.relative_to(root)
        kept: list[str] = []
        for name in sorted(dirnames):
            child_rel = rel_dir / name if rel_dir.parts else Path(name)
            if not should_exclude_relative(child_rel).excluded:
                kept.append(name)
        dirnames[:] = kept
        for filename in sorted(filenames):
            rel = rel_dir / filename if rel_dir.parts else Path(filename)
            if should_exclude_relative(rel).excluded:
                continue
            path = current / filename
            if path.is_symlink():
                raise ReviewPackageError(f"Enlace simbólico no permitido: {rel.as_posix()}")
            if path.is_file():
                files.append(path)
    files.sort(key=lambda p: p.relative_to(root).as_posix())
    return files


def validate_file_for_package(root: Path, path: Path) -> None:
    rel = path.relative_to(root)
    decision = should_exclude_relative(rel)
    if decision.excluded:
        raise ReviewPackageError(
            f"Archivo prohibido incluido: {rel.as_posix()} ({decision.reason})"
        )
    if path.is_symlink():
        raise ReviewPackageError(f"Enlace simbólico inseguro: {rel.as_posix()}")
    size = path.stat().st_size
    if size > MAX_FILE_SIZE_BYTES:
        raise ReviewPackageError(
            f"Archivo excesivo ({size} bytes > {MAX_FILE_SIZE_BYTES}): {rel.as_posix()}"
        )
    if "\x00" in rel.as_posix() or any(ord(ch) < 32 for ch in rel.as_posix()):
        raise ReviewPackageError(f"Nombre de archivo inválido: {rel.as_posix()}")


def scan_secrets_in_text(rel: str, text: str, findings: list[str]) -> None:
    from review_package_policy import SECRET_PATTERNS

    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            findings.append(f"{rel}: coincide patrón secreto {pattern.pattern!r}")


def scan_secrets(root: Path, files: list[Path]) -> list[str]:
    findings: list[str] = []
    binary_ext = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".zip", ".gz", ".xz"}
    for path in files:
        rel = path.relative_to(root).as_posix()
        if path.suffix.lower() in binary_ext:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(f"{rel}: contenido no UTF-8 (posible binario)")
            continue
        scan_secrets_in_text(rel, text, findings)
    return findings


def generate_tree(root: Path, out: Path, files: list[Path]) -> None:
    lines = [f"{root.name}/"]
    seen_dirs: set[str] = set()
    for path in files:
        rel = path.relative_to(root)
        parts = rel.parts
        for i in range(len(parts) - 1):
            dir_key = "/".join(parts[: i + 1])
            if dir_key not in seen_dirs:
                indent = "    " * i
                lines.append(f"{indent}{parts[i]}/")
                seen_dirs.add(dir_key)
        indent = "    " * (len(parts) - 1)
        lines.append(f"{indent}{parts[-1]}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_project_status(
    root: Path,
    *,
    phase: int,
    version: str,
    summary: QualitySummary,
) -> None:
    py_files = [
        p
        for p in list((root / "src").rglob("*.py")) + list((root / "tests").rglob("*.py"))
        if "__pycache__" not in p.parts
    ]
    loc = sum(len(p.read_text(encoding="utf-8").splitlines()) for p in py_files)
    auth_note = (
        ""
        if summary.authoritative
        else "\n**ADVERTENCIA:** métricas NON_AUTHORITATIVE (`--skip-tests`).\n"
    )
    content = f"""# PROJECT STATUS — QuantLab

**Fase actual:** {phase}  
**Estado:** Fase {phase} — pendiente de aprobación final v{version}  
**Versión del paquete:** {version}  
**Fecha:** {utc_now().strftime("%Y-%m-%d %H:%M UTC")}  
**Versión del proyecto:** {QUANTLAB_VERSION}
{auth_note}
---

## Resumen ejecutivo

Fase {phase} (paquete v{version}): Data Layer + adaptador A3 (anticorrupción),
catálogo SQLite, raw append-only, barras OHLCV desde trades, execution plane
en simulation con risk gate y kill switch. **Order routing real BLOQUEADO.**

---

## Módulos implementados

| Módulo | Estado |
|--------|--------|
| `core/types` | ✅ tipos + invariantes de dominio |
| `core/contracts` | ✅ Strategy Protocol |
| `core/exceptions` | ✅ Jerarquía base |
| `infra/config` | ✅ YAML + Pydantic |
| `infra/logging` | ✅ structlog |
| `infra/utils` | ✅ Reproducibilidad |
| `research/strategies` | ✅ DummyStrategy |
| `vertical_slice` | ✅ Demo end-to-end |
| `data/catalog` | ✅ SQLite local |
| `data/storage` | ✅ Raw/Processed append-only |
| `data/normalization` | ✅ Barras desde trades |
| `data/exchanges/a3` | ✅ Adapter + Fake + pyRofex boundary |
| `scripts/build_review_package.py` | ✅ Generador + validación ZIP |

---

## Módulos pendientes (bloqueados)

- `features/` — Fase 5
- `simulation/` — Fases 6-7
- `metrics/`, `reporting/` — Fase 8
- `execution/` producción — BLOQUEADO (gates + Director)

---

## Deuda técnica

- Processed aún JSONL (Parquet/DuckDB diferidos)
- Suite simulation reMarkets opt-in (credenciales)
- `from_dict` completo / schemas YAML pendientes
- Framework de migraciones de manifests documentado, no implementado

---

## Riesgos

- pyRofex API privada no usada; trades→bars es aproximación versionada
- Secret scanning basado en patrones + gitleaks; no sustituye revisión humana
- Producción: múltiples gates — no interpretar simulation como listo LIVE

---

## Calidad

| Métrica | Valor |
|---------|-------|
| Tests | {summary.test_count} |
| Cobertura | {summary.coverage_display()}% |
| Archivos Python (src+tests) | {len(py_files)} |
| LOC (src+tests) | {loc} |
| Lockfile | uv.lock |

Fuente: `reports/quality_summary.json` (JUnit + coverage.xml).

---

## Próximas fases

1. **Auditoría GPT** — aprobación Fase 3 v{version}
2. **Fase 4+** — solo tras: APROBADO — Fase 3
3. **Order routing real** — solo tras checklist `A3_PRODUCTION_READINESS.md`

Ver [docs/Roadmap.md](docs/Roadmap.md).
"""
    (root / "PROJECT_STATUS.md").write_text(content, encoding="utf-8")


def update_review_request_metrics(
    root: Path,
    *,
    phase: int,
    version: str,
    summary: QualitySummary,
) -> None:
    path = root / "REVIEW_REQUEST.md"
    text = path.read_text(encoding="utf-8")
    block = render_metrics_block(summary, phase=phase, version=version)
    # Tabla de calidad compacta + bloque machine-readable
    table_rows = [
        "## Calidad (fuente estructurada)",
        "",
        "| Check | Resultado |",
        "|-------|-----------|",
        f"| Tests | **{summary.test_count} passed** |",
        f"| Cobertura | **~{summary.coverage_display()}%** |",
        (
            "| Ruff / format / mypy | PASS |"
            if summary.authoritative
            else "| Ruff / format / mypy | NON_AUTHORITATIVE |"
        ),
        (f"| Vertical slice | {'PASS' if summary.vertical_slice_exit_code == 0 else 'FAIL'} |"),
        (f"| Secret scan | {'PASS' if summary.secret_scan_exit_code == 0 else 'FAIL'} |"),
        "| ZIP validation | PASS (ver reports/review_package_validation.txt) |",
        "",
        block,
        "",
    ]
    table = "\n".join(table_rows)
    marker_start = "<!-- BEGIN_GENERATED_QUALITY_SECTION -->"
    marker_end = "<!-- END_GENERATED_QUALITY_SECTION -->"
    section = f"{marker_start}\n{table}{marker_end}"
    if marker_start in text and marker_end in text:
        pre, rest = text.split(marker_start, 1)
        _, post = rest.split(marker_end, 1)
        text = pre + section + post
    else:
        text = upsert_metrics_block(text, block)
        if marker_start not in text:
            text = text.rstrip() + "\n\n" + section + "\n"
    path.write_text(text, encoding="utf-8")


def quality_dict(summary: QualitySummary) -> dict[str, Any]:
    return {
        "test_count": summary.test_count,
        "passed": summary.passed,
        "failed": summary.failed,
        "errors": summary.errors,
        "skipped": summary.skipped,
        "coverage_pct": str(summary.coverage_pct),
        "ruff_exit_code": summary.ruff_exit_code,
        "format_exit_code": summary.format_exit_code,
        "mypy_exit_code": summary.mypy_exit_code,
        "pytest_exit_code": summary.pytest_exit_code,
        "coverage_exit_code": summary.coverage_exit_code,
        "vertical_slice_exit_code": summary.vertical_slice_exit_code,
        "secret_scan_exit_code": summary.secret_scan_exit_code,
        "authoritative": summary.authoritative,
        "junit_report": summary.junit_report,
        "coverage_report": summary.coverage_report,
    }


def write_package_manifest(
    root: Path,
    *,
    phase: int,
    version: str,
    files: list[Path],
    summary: QualitySummary,
) -> dict[str, Any]:
    lock_name, lock_hash = detect_lockfile(root)
    file_list = [p.relative_to(root).as_posix() for p in files]
    content_hash = hashlib.sha256()
    for rel in file_list:
        if rel == "REVIEW_PACKAGE_MANIFEST.json":
            continue
        payload = (root / rel).read_bytes()
        content_hash.update(rel.encode("utf-8"))
        content_hash.update(b"\0")
        content_hash.update(payload)
        content_hash.update(b"\0")

    # file_count incluye al propio REVIEW_PACKAGE_MANIFEST.json en la lista final.
    manifest: dict[str, Any] = {
        "project_name": "QuantLab",
        "phase": phase,
        "package_version": version,
        "created_at_utc": utc_now().isoformat(),
        "git_commit": git_commit(root),
        "python_version": sys.version.split()[0],
        "quantlab_version": QUANTLAB_VERSION,
        "lockfile_name": lock_name,
        "lockfile_sha256": lock_hash,
        "content_sha256": content_hash.hexdigest(),
        "file_count": len(file_list),
        "file_count_includes_manifest": True,
        "files": file_list,
        "exclusion_policy": policy_summary(),
        "quality": quality_dict(summary),
        "generator_version": GENERATOR_VERSION,
    }
    out = root / "REVIEW_PACKAGE_MANIFEST.json"
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def ensure_required_present(root: Path) -> None:
    missing: list[str] = []
    for name in REQUIRED_TOP_FILES:
        if name in {"REVIEW_PACKAGE_MANIFEST.json", "tree.txt"}:
            continue
        if not (root / name).exists():
            missing.append(name)
    for name in REQUIRED_TOP_DIRS:
        if not (root / name).is_dir():
            missing.append(name + "/")
    for name in REQUIRED_DOC_FILES:
        if not (root / name).exists():
            missing.append(name)
    if missing:
        raise ReviewPackageError("Faltan archivos/dirs obligatorios: " + ", ".join(missing))


def build_zip(root: Path, zip_path: Path, files: list[Path]) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            rel = path.relative_to(root).as_posix()
            danger = is_dangerous_arcname(rel)
            if danger:
                raise ReviewPackageError(f"Arcname inseguro ({danger}): {rel}")
            info = zipfile.ZipInfo(filename=rel, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            zf.writestr(info, path.read_bytes())


def validate_zip(root: Path, zip_path: Path, expected_files: list[str]) -> ZipValidationResult:
    notes: list[str] = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = list(zf.namelist())
        if sorted(names) != sorted(expected_files):
            only_zip = sorted(set(names) - set(expected_files))
            only_exp = sorted(set(expected_files) - set(names))
            raise ReviewPackageError(
                f"Lista de archivos del ZIP no coincide. "
                f"solo_zip={only_zip[:20]} solo_esperado={only_exp[:20]}"
            )

        no_absolute = True
        no_traversal = True
        no_nested = True
        forbidden_absent = True
        for name in names:
            danger = is_dangerous_arcname(name)
            if danger:
                if "absoluta" in danger:
                    no_absolute = False
                if "traversal" in danger:
                    no_traversal = False
                raise ReviewPackageError(f"Miembro ZIP inseguro ({danger}): {name}")
            decision = should_exclude_relative(Path(name))
            if decision.excluded:
                forbidden_absent = False
                raise ReviewPackageError(
                    f"ZIP contiene elemento prohibido: {name} ({decision.reason})"
                )
            if name.lower().endswith(".zip"):
                no_nested = False
                raise ReviewPackageError(f"ZIP anidado no permitido: {name}")
            info = zf.getinfo(name)
            if info.file_size > MAX_FILE_SIZE_BYTES:
                raise ReviewPackageError(f"Miembro demasiado grande: {name}")

        no_symlinks = True
        with tempfile.TemporaryDirectory(prefix="quantlab_review_") as tmp:
            tmp_path = Path(tmp)
            # Extracción segura: rechazar traversal al escribir
            for info in zf.infolist():
                target = (tmp_path / info.filename).resolve()
                if not str(target).startswith(str(tmp_path.resolve())):
                    no_traversal = False
                    raise ReviewPackageError(f"traversal al extraer: {info.filename}")
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info, "r") as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
                if target.is_symlink():
                    no_symlinks = False
                    raise ReviewPackageError(f"symlink en extracción: {info.filename}")

            for req in REQUIRED_TOP_FILES:
                if not (tmp_path / req).exists():
                    raise ReviewPackageError(f"Tras descomprimir falta: {req}")
            for req in REQUIRED_TOP_DIRS:
                if not (tmp_path / req).is_dir():
                    raise ReviewPackageError(f"Tras descomprimir falta dir: {req}")
            for req in REQUIRED_REPORT_FILES:
                if not (tmp_path / req).exists():
                    raise ReviewPackageError(f"Tras descomprimir falta reporte: {req}")
            for req in REQUIRED_DOC_FILES:
                if not (tmp_path / req).exists():
                    raise ReviewPackageError(f"Tras descomprimir falta doc: {req}")

            extracted = [p for p in tmp_path.rglob("*") if p.is_file()]
            findings = scan_secrets(tmp_path, extracted)
            secrets_clean = not findings
            if findings:
                raise ReviewPackageError("Secretos en ZIP descomprimido:\n" + "\n".join(findings))

            notes.append(f"miembros_zip={len(names)}")
            notes.append("descompresión=ok")
            notes.append("secret_scan_extracted=ok")
            notes.append(f"git_head={git_commit(root)}")

    return ZipValidationResult(
        member_count=len(names),
        members=tuple(sorted(names)),
        required_present=True,
        forbidden_absent=forbidden_absent,
        no_absolute_paths=no_absolute,
        no_traversal=no_traversal,
        no_symlinks=no_symlinks,
        no_nested_zips=no_nested,
        secrets_clean=secrets_clean,
        extract_ok=True,
        notes=tuple(notes),
    )


def write_structural_validation_report(
    path: Path,
    *,
    zip_name: str,
    phase: int,
    version: str,
    result: ZipValidationResult,
) -> None:
    members_preview = "\n".join(f"  - {m}" for m in result.members)
    body = "\n".join(
        [
            f"command: validate-review-package {zip_name}",
            f"started_at_utc: {utc_now().isoformat()}",
            "exit_code: 0",
            "result: PASS",
            "",
            f"package_name={zip_name}",
            f"phase={phase}",
            f"package_version={version}",
            f"generator_version={GENERATOR_VERSION}",
            f"file_count={result.member_count}",
            f"required_files_present={result.required_present}",
            f"forbidden_files_absent={result.forbidden_absent}",
            f"no_absolute_paths={result.no_absolute_paths}",
            f"no_path_traversal={result.no_traversal}",
            f"no_symlinks={result.no_symlinks}",
            f"no_nested_zips={result.no_nested_zips}",
            f"secrets_clean={result.secrets_clean}",
            f"temp_extract_ok={result.extract_ok}",
            "validation=PASS",
            "validation_scope=structural_members_and_content",
            "sha256_location=sidecar_only",
            "note=Final ZIP byte SHA-256 is written ONLY to the .sha256 sidecar "
            "(and external .validation.txt). Including the hash inside the ZIP "
            "would change the bytes and invalidate the hash (circular dependency).",
            "",
            "----- VALIDATED_MEMBERS -----",
            members_preview,
            "",
            "----- NOTES -----",
            *result.notes,
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def write_external_validation_report(
    path: Path,
    *,
    zip_name: str,
    zip_path: Path,
    digest: str,
    result: ZipValidationResult,
    manifest: dict[str, Any],
    commit: str,
) -> None:
    body = "\n".join(
        [
            f"package_name={zip_name}",
            f"created_at_utc={utc_now().isoformat()}",
            f"git_commit={commit}",
            f"sha256={digest}",
            f"zip_size_bytes={zip_path.stat().st_size}",
            f"member_count={result.member_count}",
            f"manifest_file_count={manifest.get('file_count')}",
            "reopen_ok=true",
            f"extract_ok={result.extract_ok}",
            f"secret_scan_extracted={result.secrets_clean}",
            f"manifest_members_match={result.member_count == manifest.get('file_count')}",
            "validation=PASS",
            "scope=external_final_byte_stream",
            "",
        ]
    )
    path.write_text(body, encoding="utf-8")


def _resolve_cmd(cmd: list[str]) -> list[str]:
    use_uv = shutil.which("uv") is not None
    if use_uv:
        return cmd
    if cmd[:2] == ["uv", "sync"]:
        return [sys.executable, "-m", "pip", "install", "-e", ".[dev]"]
    if cmd[:2] == ["uv", "run"]:
        rest = cmd[2:]
        if rest and rest[0] in {"pytest", "ruff", "mypy"}:
            return [sys.executable, "-m", rest[0], *rest[1:]]
        return rest
    return cmd


def run_quality_suite(root: Path, *, skip_tests: bool) -> QualitySummary:
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    junit_path = reports / "pytest_junit.xml"
    coverage_xml = reports / "coverage.xml"

    install = run_cmd(_resolve_cmd(["uv", "sync", "--frozen", "--extra", "dev"]), root)
    write_report(reports / "install_report.txt", install)
    if install.returncode != 0:
        raise ReviewPackageError("Instalación/sync falló")

    if skip_tests:
        # Placeholders no autoritativos — no aptos para auditoría.
        for name in REQUIRED_REPORT_FILES:
            path = root / name
            if not path.exists():
                if name.endswith(".json"):
                    path.write_text("{}\n", encoding="utf-8")
                elif name.endswith(".xml"):
                    path.write_text(
                        '<?xml version="1.0"?><testsuites></testsuites>\n',
                        encoding="utf-8",
                    )
                else:
                    path.write_text(
                        "command: skipped\nstarted_at_utc: n/a\nexit_code: 0\nresult: SKIP\n",
                        encoding="utf-8",
                    )
        summary = QualitySummary(
            test_count=0,
            passed=0,
            failed=0,
            errors=0,
            skipped=0,
            coverage_pct=Decimal("0"),
            ruff_exit_code=0,
            format_exit_code=0,
            mypy_exit_code=0,
            pytest_exit_code=0,
            coverage_exit_code=0,
            vertical_slice_exit_code=0,
            secret_scan_exit_code=0,
            authoritative=False,
            junit_report="reports/pytest_junit.xml",
            coverage_report="reports/coverage.xml",
        )
        write_quality_summary_json(reports / "quality_summary.json", summary)
        return summary

    ruff = run_cmd(_resolve_cmd(["uv", "run", "ruff", "check", "."]), root)
    write_report(reports / "ruff_report.txt", ruff)
    fmt = run_cmd(_resolve_cmd(["uv", "run", "ruff", "format", "--check", "."]), root)
    write_report(reports / "format_report.txt", fmt)
    mypy = run_cmd(
        _resolve_cmd(["uv", "run", "mypy", "src", "tests", "scripts"]),
        root,
    )
    write_report(reports / "mypy_report.txt", mypy)

    # Una sola corrida autoritativa: pytest + JUnit + coverage
    pytest_cmd = [
        "uv",
        "run",
        "pytest",
        f"--junitxml={junit_path.as_posix()}",
        "--cov=quantlab",
        "--cov-report=term-missing",
        f"--cov-report=xml:{coverage_xml.as_posix()}",
    ]
    pytest_res = run_cmd(_resolve_cmd(pytest_cmd), root)
    write_report(reports / "pytest_report.txt", pytest_res)
    write_report(reports / "coverage.txt", pytest_res)

    vs = run_cmd(_resolve_cmd(["uv", "run", "quantlab-vertical-slice"]), root)
    write_report(reports / "vertical_slice_report.txt", vs)

    for name, res in (
        ("ruff", ruff),
        ("format", fmt),
        ("mypy", mypy),
        ("pytest", pytest_res),
        ("vertical_slice", vs),
    ):
        if res.returncode != 0:
            raise ReviewPackageError(f"Check {name} falló — ver reports/")

    try:
        tests, passed, failed, errors, skipped = parse_junit_xml(junit_path)
        coverage_pct = parse_coverage_xml(coverage_xml)
    except QualityError as exc:
        raise ReviewPackageError(str(exc)) from exc

    summary = QualitySummary(
        test_count=tests,
        passed=passed,
        failed=failed,
        errors=errors,
        skipped=skipped,
        coverage_pct=coverage_pct,
        ruff_exit_code=ruff.returncode,
        format_exit_code=fmt.returncode,
        mypy_exit_code=mypy.returncode,
        pytest_exit_code=pytest_res.returncode,
        coverage_exit_code=pytest_res.returncode,
        vertical_slice_exit_code=vs.returncode,
        secret_scan_exit_code=0,  # se actualiza tras el scan
        authoritative=True,
        junit_report="reports/pytest_junit.xml",
        coverage_report="reports/coverage.xml",
    )
    try:
        summary.validate()
    except QualityError as exc:
        raise ReviewPackageError(str(exc)) from exc
    write_quality_summary_json(reports / "quality_summary.json", summary)
    return summary


def prepare_file_set(
    root: Path,
    *,
    phase: int,
    version: str,
    summary: QualitySummary,
) -> tuple[list[Path], dict[str, Any]]:
    staging = collect_candidate_files(root)
    generate_tree(root, root / "tree.txt", staging)
    write_package_manifest(root, phase=phase, version=version, files=staging, summary=summary)
    files = collect_candidate_files(root)
    write_package_manifest(root, phase=phase, version=version, files=files, summary=summary)
    files = collect_candidate_files(root)
    for path in files:
        validate_file_for_package(root, path)
    findings = scan_secrets(root, files)
    if findings:
        raise ReviewPackageError("Secret scan pre-ZIP falló:\n" + "\n".join(findings))
    write_report(
        root / "reports" / "secret_scan_report.txt",
        CmdResult(
            command=["quantlab-secret-scan"],
            returncode=0,
            stdout="No secrets detected.",
            stderr="",
            started_at=utc_now().isoformat(),
        ),
    )
    # Actualizar summary con secret_scan y reescribir JSON
    summary = QualitySummary(
        test_count=summary.test_count,
        passed=summary.passed,
        failed=summary.failed,
        errors=summary.errors,
        skipped=summary.skipped,
        coverage_pct=summary.coverage_pct,
        ruff_exit_code=summary.ruff_exit_code,
        format_exit_code=summary.format_exit_code,
        mypy_exit_code=summary.mypy_exit_code,
        pytest_exit_code=summary.pytest_exit_code,
        coverage_exit_code=summary.coverage_exit_code,
        vertical_slice_exit_code=summary.vertical_slice_exit_code,
        secret_scan_exit_code=0,
        authoritative=summary.authoritative,
        junit_report=summary.junit_report,
        coverage_report=summary.coverage_report,
    )
    write_quality_summary_json(root / "reports" / "quality_summary.json", summary)
    files = collect_candidate_files(root)
    manifest = write_package_manifest(
        root, phase=phase, version=version, files=files, summary=summary
    )
    files = collect_candidate_files(root)
    for path in files:
        validate_file_for_package(root, path)
    return files, manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build QuantLab Review Package")
    parser.add_argument("--phase", type=int, default=PACKAGE_PHASE_DEFAULT)
    parser.add_argument("--version", default=PACKAGE_VERSION_DEFAULT)
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Solo desarrollo local; produce ZIP NON_AUTHORITATIVE (no auditable)",
    )
    args = parser.parse_args(argv)

    root = project_root()
    phase_str = f"{args.phase:02d}"
    if args.skip_tests:
        zip_name = f"QuantLab_Review_Fase_{phase_str}_v{args.version}.NON_AUTHORITATIVE.zip"
        print("WARNING: --skip-tests → artefacto NON_AUTHORITATIVE (no auditable)")
    else:
        zip_name = f"QuantLab_Review_Fase_{phase_str}_v{args.version}.zip"
    zip_path = root / zip_name
    sha_path = Path(str(zip_path) + ".sha256")
    external_validation = root / zip_name.replace(".zip", ".validation.txt")

    print(f"== QuantLab Review Package generator v{GENERATOR_VERSION} ==")
    print(f"root={root}")
    print(f"phase={args.phase} version={args.version}")

    try:
        ensure_required_present(root)
        summary = run_quality_suite(root, skip_tests=args.skip_tests)
        write_project_status(root, phase=args.phase, version=args.version, summary=summary)
        update_review_request_metrics(root, phase=args.phase, version=args.version, summary=summary)

        # Placeholder de validación para que el archivo exista en el ZIP provisional
        (root / "reports" / "review_package_validation.txt").write_text(
            "validation=PROVISIONAL\nphase=awaiting_zip_validation\n",
            encoding="utf-8",
        )

        files, _manifest = prepare_file_set(
            root, phase=args.phase, version=args.version, summary=summary
        )
        expected = [p.relative_to(root).as_posix() for p in files]

        with tempfile.TemporaryDirectory(prefix="quantlab_prov_") as prov_dir:
            provisional = Path(prov_dir) / "provisional.zip"
            print(f"Building provisional ZIP ({len(files)} files)...")
            build_zip(root, provisional, files)
            provisional_result = validate_zip(root, provisional, expected)

            # Reporte estructural completo (sin SHA del ZIP)
            write_structural_validation_report(
                root / "reports" / "review_package_validation.txt",
                zip_name=zip_name,
                phase=args.phase,
                version=args.version,
                result=provisional_result,
            )

            # Regenerar manifiesto + lista (mismos paths; contenido de validation cambió)
            files_final, manifest = prepare_file_set(
                root, phase=args.phase, version=args.version, summary=summary
            )
            expected_final = [p.relative_to(root).as_posix() for p in files_final]
            if sorted(expected_final) != sorted(expected):
                raise ReviewPackageError(
                    "La lista de miembros cambió entre pasada provisional y final"
                )

            print(f"Building final ZIP {zip_name} ({len(files_final)} files)...")
            build_zip(root, zip_path, files_final)

            final_result = validate_zip(root, zip_path, expected_final)
            if final_result.members != provisional_result.members:
                raise ReviewPackageError(
                    "Miembros del ZIP final difieren de los validados en la pasada provisional"
                )

        with zipfile.ZipFile(zip_path) as zf:
            packed = zf.read("reports/review_package_validation.txt").decode("utf-8")
        if "validation=PASS" not in packed:
            raise ReviewPackageError("ZIP final sin validation=PASS en reporte incluido")
        if "pre_zip_structural_gate" in packed or "reports_ready" in packed:
            raise ReviewPackageError("ZIP final con reporte de prevalidación incompleto")
        if "validation_scope=structural_members_and_content" not in packed:
            raise ReviewPackageError("ZIP final sin evidencia estructural completa")

        digest = sha256_file(zip_path)
        sha_path.write_text(f"{digest}  {zip_name}\n", encoding="utf-8")
        commit = git_commit(root)
        write_external_validation_report(
            external_validation,
            zip_name=zip_name,
            zip_path=zip_path,
            digest=digest,
            result=final_result,
            manifest=manifest,
            commit=commit,
        )

        # Consistencia documental contra la fuente estructurada
        assert_document_consistency(
            summary=summary,
            phase=args.phase,
            version=args.version,
            project_status=(root / "PROJECT_STATUS.md").read_text(encoding="utf-8"),
            review_request=(root / "REVIEW_REQUEST.md").read_text(encoding="utf-8"),
            manifest=manifest,
            zip_member_count=final_result.member_count,
        )

        # Verificar sidecar vs bytes
        if sha_path.read_text(encoding="utf-8").split()[0] != digest:
            raise ReviewPackageError("sidecar SHA-256 no coincide con bytes del ZIP")
        if f"sha256={digest}" not in external_validation.read_text(encoding="utf-8"):
            raise ReviewPackageError("reporte externo sin el SHA-256 final")

        print(f"Done: {zip_path}")
        print(f"SHA256: {digest}")
        print(f"Sidecar: {sha_path.name}")
        print(f"External validation: {external_validation.name}")
        print(f"Files: {final_result.member_count}")
        print(f"Tests: {summary.test_count}")
        print(f"Coverage: {summary.coverage_display()}%")
        return 0
    except (ReviewPackageError, QualityError) as exc:
        write_report(
            root / "reports" / "review_package_validation.txt",
            CmdResult(
                command=["build_review_package"],
                returncode=1,
                stdout="",
                stderr=str(exc),
                started_at=utc_now().isoformat(),
            ),
        )
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
