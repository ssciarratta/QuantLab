"""Política centralizada de exclusiones e inclusión del Review Package.

Fuente única de verdad (testeable, determinista, OS-independent).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

GENERATOR_VERSION = "1.3.0"

# Tamaño máximo razonable por archivo en el paquete (10 MiB).
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

EXCLUDE_DIR_NAMES: frozenset[str] = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        ".tox",
        ".nox",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".hypothesis",
        ".coverage",
        "htmlcov",
        "dist",
        "build",
        "logs",
        "review_staging",
        ".idea",
        ".vscode",
        ".ipynb_checkpoints",
        "node_modules",
        "egg-info",
    }
)

EXCLUDE_DIR_SUFFIXES: frozenset[str] = frozenset({".egg-info"})

EXCLUDE_FILE_NAMES: frozenset[str] = frozenset(
    {
        ".coverage",
        ".DS_Store",
        "Thumbs.db",
        "desktop.ini",
        ".env",
        "sync_token.txt",
        "sync_approved.txt",
    }
)

# Reportes legacy en la raíz (la fuente de verdad está en reports/).
EXCLUDE_ROOT_LEGACY_FILES: frozenset[str] = frozenset(
    {
        "coverage.xml",
        "coverage.txt",
        "pytest_report.txt",
        "mypy_report.txt",
        "ruff_report.txt",
        "format_report.txt",
        "requirements.txt",
    }
)

EXCLUDE_FILE_SUFFIXES: frozenset[str] = frozenset(
    {
        ".pyc",
        ".pyo",
        ".pyd",
        ".so",
        ".dll",
        ".exe",
        ".whl",
        ".egg",
        ".secret",
    }
)

EXCLUDE_NAME_PREFIXES: tuple[str, ...] = ("QuantLab_Review_Fase_",)

EXCLUDE_NAME_SUFFIXES: tuple[str, ...] = (".zip", ".zip.sha256", ".validation.txt")

# Rutas top-level que nunca se incluyen (aunque existan).
EXCLUDE_TOP_LEVEL: frozenset[str] = frozenset(
    {
        "data",
        "experiments",
        ".git",
        ".venv",
        "venv",
        ".cursor",
        ".codex",
    }
)

REQUIRED_TOP_FILES: tuple[str, ...] = (
    "README.md",
    "CHANGELOG.md",
    "LESSONS_LEARNED.md",
    "PROJECT_STATUS.md",
    "REVIEW_REQUEST.md",
    "pyproject.toml",
    "uv.lock",
    ".gitignore",
    "LICENSE",
    "tree.txt",
    "REVIEW_PACKAGE_MANIFEST.json",
    ".gitleaks.toml",
)

REQUIRED_TOP_DIRS: tuple[str, ...] = (
    "src",
    "tests",
    "scripts",
    "config",
    "docs",
    "learning",
    "reports",
    ".github",
)

REQUIRED_REPORT_FILES: tuple[str, ...] = (
    "reports/ruff_report.txt",
    "reports/format_report.txt",
    "reports/mypy_report.txt",
    "reports/pytest_report.txt",
    "reports/pytest_junit.xml",
    "reports/quality_summary.json",
    "reports/coverage.txt",
    "reports/coverage.xml",
    "reports/vertical_slice_report.txt",
    "reports/secret_scan_report.txt",
    "reports/install_report.txt",
    "reports/review_package_validation.txt",
)

REQUIRED_DOC_FILES: tuple[str, ...] = (
    "docs/MANIFEST_VERSIONING.md",
    "docs/REVIEW_PACKAGE.md",
    "docs/A3_DISCOVERY_REPORT.md",
    "docs/A3_INTEGRATION.md",
    "docs/A3_RUNBOOK.md",
    "docs/A3_SECURITY.md",
    "docs/A3_DATA_DICTIONARY.md",
    "docs/A3_SIMULATION_TESTING.md",
    "docs/A3_PRODUCTION_READINESS.md",
)

# Patrones de secretos / URLs autenticadas (contenido).
SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*['\"][^'\"]{8,}"),
    re.compile(r"(?i)-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)password\s*[:=]\s*['\"][^'\"]{4,}"),
    re.compile(r"https?://[^/\s:]+:[^/@\s]+@"),  # URL con credenciales
    re.compile(r"(?i)aws_secret_access_key\s*[:=]"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
)

DANGEROUS_ARCNAME_RE = re.compile(r"(^|/|\\)\.\.(/|\\|$)|^([A-Za-z]:[/\\]|/)")


@dataclass(frozen=True, slots=True)
class ExclusionDecision:
    excluded: bool
    reason: str | None = None


def _has_excluded_dir_part(path: Path) -> ExclusionDecision:
    for part in path.parts:
        if part in EXCLUDE_DIR_NAMES:
            return ExclusionDecision(True, f"directorio excluido: {part}")
        if any(part.endswith(suf) for suf in EXCLUDE_DIR_SUFFIXES):
            return ExclusionDecision(True, f"sufijo de directorio excluido: {part}")
    return ExclusionDecision(False)


def should_exclude_relative(rel: Path) -> ExclusionDecision:
    """Decide exclusión a partir de una ruta relativa al root del proyecto."""
    if rel.is_absolute():
        return ExclusionDecision(True, "ruta absoluta")

    parts = rel.parts
    if not parts:
        return ExclusionDecision(True, "ruta vacía")

    if parts[0] in EXCLUDE_TOP_LEVEL:
        return ExclusionDecision(True, f"top-level excluido: {parts[0]}")

    dir_decision = _has_excluded_dir_part(rel)
    if dir_decision.excluded:
        return dir_decision

    name = rel.name
    if len(rel.parts) == 1 and name in EXCLUDE_ROOT_LEGACY_FILES:
        return ExclusionDecision(True, f"reporte legacy en raíz: {name}")

    if name in EXCLUDE_FILE_NAMES:
        return ExclusionDecision(True, f"archivo excluido: {name}")

    suffix = rel.suffix.lower()
    if suffix in EXCLUDE_FILE_SUFFIXES:
        return ExclusionDecision(True, f"sufijo excluido: {suffix}")

    if name.startswith(EXCLUDE_NAME_PREFIXES) and name.endswith(EXCLUDE_NAME_SUFFIXES):
        return ExclusionDecision(True, "artefacto Review Package previo")

    if name.startswith(EXCLUDE_NAME_PREFIXES) and suffix == ".zip":
        return ExclusionDecision(True, "ZIP de Review Package previo")

    if name.endswith(".zip.sha256") and name.startswith("QuantLab_Review_Fase_"):
        return ExclusionDecision(True, "hash de Review Package previo")

    # Editor / temporales
    if name.startswith("~$") or name.endswith("~") or name.endswith(".swp"):
        return ExclusionDecision(True, "archivo temporal de editor")

    return ExclusionDecision(False)


def is_dangerous_arcname(arcname: str) -> str | None:
    """Retorna motivo si el nombre de miembro ZIP es inseguro."""
    normalized = arcname.replace("\\", "/")
    if normalized.startswith("/") or re.match(r"^[A-Za-z]:/", normalized):
        return "ruta absoluta en ZIP"
    if ".." in normalized.split("/"):
        return "path traversal (..)"
    if DANGEROUS_ARCNAME_RE.search(normalized):
        return "nombre de archivo peligroso"
    return None


def policy_summary() -> dict[str, object]:
    """Resumen serializable de la política (para el manifiesto del paquete)."""
    return {
        "generator_version": GENERATOR_VERSION,
        "max_file_size_bytes": MAX_FILE_SIZE_BYTES,
        "exclude_dir_names": sorted(EXCLUDE_DIR_NAMES),
        "exclude_dir_suffixes": sorted(EXCLUDE_DIR_SUFFIXES),
        "exclude_file_names": sorted(EXCLUDE_FILE_NAMES),
        "exclude_root_legacy_files": sorted(EXCLUDE_ROOT_LEGACY_FILES),
        "exclude_file_suffixes": sorted(EXCLUDE_FILE_SUFFIXES),
        "exclude_top_level": sorted(EXCLUDE_TOP_LEVEL),
        "exclude_name_prefixes": list(EXCLUDE_NAME_PREFIXES),
        "required_top_files": list(REQUIRED_TOP_FILES),
        "required_top_dirs": list(REQUIRED_TOP_DIRS),
        "required_report_files": list(REQUIRED_REPORT_FILES),
        "required_doc_files": list(REQUIRED_DOC_FILES),
    }
