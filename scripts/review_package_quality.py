"""Métricas de calidad tipadas — fuente única para el Review Package."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any


class QualityError(RuntimeError):
    """Inconsistencia o parseo inválido de métricas de calidad."""


@dataclass(frozen=True, slots=True)
class QualitySummary:
    """Fuente autoritativa de métricas del Review Package."""

    test_count: int
    passed: int
    failed: int
    errors: int
    skipped: int
    coverage_pct: Decimal
    ruff_exit_code: int
    format_exit_code: int
    mypy_exit_code: int
    pytest_exit_code: int
    coverage_exit_code: int
    vertical_slice_exit_code: int
    secret_scan_exit_code: int
    authoritative: bool
    junit_report: str
    coverage_report: str

    def validate(self) -> None:
        if self.test_count < 0 or self.passed < 0 or self.failed < 0:
            raise QualityError("conteos de tests no pueden ser negativos")
        if self.errors < 0 or self.skipped < 0:
            raise QualityError("conteos de tests no pueden ser negativos")
        accounted = self.passed + self.failed + self.errors + self.skipped
        if accounted != self.test_count:
            raise QualityError(
                f"inconsistencia JUnit: passed+failed+errors+skipped={accounted} "
                f"!= tests={self.test_count}"
            )
        if self.authoritative and self.pytest_exit_code == 0 and self.test_count == 0:
            raise QualityError(
                "pytest PASS con test_count==0 — métrica no autoritativa / suite vacía"
            )
        if not (Decimal("0") <= self.coverage_pct <= Decimal("100")):
            raise QualityError(f"coverage_pct fuera de rango: {self.coverage_pct}")
        if self.authoritative:
            for name, code in (
                ("ruff", self.ruff_exit_code),
                ("format", self.format_exit_code),
                ("mypy", self.mypy_exit_code),
                ("pytest", self.pytest_exit_code),
                ("coverage", self.coverage_exit_code),
                ("vertical_slice", self.vertical_slice_exit_code),
                ("secret_scan", self.secret_scan_exit_code),
            ):
                if code != 0:
                    raise QualityError(f"check {name} no está en PASS (exit={code})")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["coverage_pct"] = str(self.coverage_pct)
        return data

    def coverage_display(self) -> str:
        return f"{self.coverage_pct.quantize(Decimal('0.1'))}"


def parse_junit_xml(path: Path) -> tuple[int, int, int, int, int]:
    """Retorna (tests, passed, failed, errors, skipped) desde JUnit XML."""
    if not path.exists():
        raise QualityError(f"falta reporte JUnit: {path}")
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise QualityError(f"JUnit malformado: {exc}") from exc

    suites: list[ET.Element] = []
    if root.tag == "testsuite":
        suites = [root]
    elif root.tag == "testsuites":
        suites = [el for el in root if el.tag == "testsuite"]
    else:
        raise QualityError(f"raíz JUnit inesperada: {root.tag}")

    if not suites:
        raise QualityError("JUnit sin testsuites")

    tests = failed = errors = skipped = 0
    for suite in suites:
        tests += int(suite.attrib.get("tests", "0"))
        failed += int(suite.attrib.get("failures", "0"))
        errors += int(suite.attrib.get("errors", "0"))
        skipped += int(suite.attrib.get("skipped", "0"))

    passed = tests - failed - errors - skipped
    if passed < 0:
        raise QualityError("JUnit inconsistente: passed negativo")
    return tests, passed, failed, errors, skipped


def parse_coverage_xml(path: Path) -> Decimal:
    """Lee line-rate de coverage.xml (cobertura de líneas 0–100)."""
    if not path.exists():
        raise QualityError(f"falta coverage.xml: {path}")
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise QualityError(f"coverage.xml malformado: {exc}") from exc

    rate_raw = root.attrib.get("line-rate")
    if rate_raw is None:
        # Cobertura branch-aware a veces solo en packages; sumar lines
        lines_valid = 0
        lines_covered = 0
        for line in root.iter("line"):
            lines_valid += 1
            if line.attrib.get("hits", "0") not in {"0", ""}:
                lines_covered += 1
        if lines_valid == 0:
            raise QualityError("coverage.xml sin line-rate ni líneas")
        pct = (Decimal(lines_covered) / Decimal(lines_valid)) * Decimal(100)
    else:
        pct = Decimal(rate_raw) * Decimal(100)
    return pct.quantize(Decimal("0.01"))


def write_quality_summary_json(path: Path, summary: QualitySummary) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(summary.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def load_quality_summary_json(path: Path) -> QualitySummary:
    data = json.loads(path.read_text(encoding="utf-8"))
    summary = QualitySummary(
        test_count=int(data["test_count"]),
        passed=int(data["passed"]),
        failed=int(data["failed"]),
        errors=int(data["errors"]),
        skipped=int(data["skipped"]),
        coverage_pct=Decimal(str(data["coverage_pct"])),
        ruff_exit_code=int(data["ruff_exit_code"]),
        format_exit_code=int(data["format_exit_code"]),
        mypy_exit_code=int(data["mypy_exit_code"]),
        pytest_exit_code=int(data["pytest_exit_code"]),
        coverage_exit_code=int(data["coverage_exit_code"]),
        vertical_slice_exit_code=int(data["vertical_slice_exit_code"]),
        secret_scan_exit_code=int(data["secret_scan_exit_code"]),
        authoritative=bool(data["authoritative"]),
        junit_report=str(data["junit_report"]),
        coverage_report=str(data["coverage_report"]),
    )
    summary.validate()
    return summary


_STATUS_TESTS_RE = re.compile(r"\|\s*Tests\s*\|\s*(\d+)\s*\|")
_STATUS_COV_RE = re.compile(r"\|\s*Cobertura\s*\|\s*([0-9]+(?:\.[0-9]+)?)%\s*\|")
_STATUS_VERSION_RE = re.compile(r"\*\*Versión del paquete:\*\*\s*([0-9.]+)")
_STATUS_PHASE_RE = re.compile(r"\*\*Fase actual:\*\*\s*(\d+)")
_REQUEST_TESTS_RE = re.compile(r"\|\s*Tests\s*\|\s*\*\*(\d+)\s+passed\*\*\s*\|")
_REQUEST_COV_RE = re.compile(
    r"\|\s*Cobertura\s*\|\s*\*\*~?([0-9]+(?:\.[0-9]+)?)%\*\*",
)
_METRICS_BLOCK_RE = re.compile(
    r"<!-- BEGIN_QUALITY_METRICS -->\n(.*?)\n<!-- END_QUALITY_METRICS -->",
    re.DOTALL,
)


def render_metrics_block(summary: QualitySummary, *, phase: int, version: str) -> str:
    return "\n".join(
        [
            "<!-- BEGIN_QUALITY_METRICS -->",
            f"phase: {phase}",
            f"package_version: {version}",
            f"test_count: {summary.test_count}",
            f"passed: {summary.passed}",
            f"failed: {summary.failed}",
            f"errors: {summary.errors}",
            f"skipped: {summary.skipped}",
            f"coverage_pct: {summary.coverage_display()}",
            f"authoritative: {str(summary.authoritative).lower()}",
            "<!-- END_QUALITY_METRICS -->",
        ]
    )


def upsert_metrics_block(text: str, block: str) -> str:
    if _METRICS_BLOCK_RE.search(text):
        return _METRICS_BLOCK_RE.sub(block, text, count=1)
    return text.rstrip() + "\n\n" + block + "\n"


def parse_metrics_block(text: str) -> dict[str, str]:
    match = _METRICS_BLOCK_RE.search(text)
    if not match:
        raise QualityError("REVIEW_REQUEST.md sin bloque BEGIN_QUALITY_METRICS")
    data: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def assert_document_consistency(
    *,
    summary: QualitySummary,
    phase: int,
    version: str,
    project_status: str,
    review_request: str,
    manifest: dict[str, Any],
    zip_member_count: int | None = None,
) -> None:
    """Falla si los artefactos generados no coinciden con QualitySummary."""
    summary.validate()

    status_tests = _STATUS_TESTS_RE.search(project_status)
    status_cov = _STATUS_COV_RE.search(project_status)
    status_ver = _STATUS_VERSION_RE.search(project_status)
    status_phase = _STATUS_PHASE_RE.search(project_status)
    if not status_tests:
        raise QualityError("PROJECT_STATUS.md sin fila Tests")
    if int(status_tests.group(1)) != summary.test_count:
        raise QualityError(f"PROJECT_STATUS Tests={status_tests.group(1)} != {summary.test_count}")
    if not status_cov:
        raise QualityError("PROJECT_STATUS.md sin fila Cobertura")
    status_cov_dec = Decimal(status_cov.group(1))
    if abs(status_cov_dec - Decimal(summary.coverage_display())) > Decimal("0.15"):
        raise QualityError(
            f"PROJECT_STATUS Cobertura={status_cov_dec} != {summary.coverage_display()}"
        )
    if not status_ver or status_ver.group(1) != version:
        raise QualityError("PROJECT_STATUS versión de paquete inconsistente")
    if not status_phase or int(status_phase.group(1)) != phase:
        raise QualityError("PROJECT_STATUS fase inconsistente")

    metrics = parse_metrics_block(review_request)
    if int(metrics.get("test_count", "-1")) != summary.test_count:
        raise QualityError("REVIEW_REQUEST test_count inconsistente")
    if metrics.get("package_version") != version:
        raise QualityError("REVIEW_REQUEST package_version inconsistente")
    if int(metrics.get("phase", "-1")) != phase:
        raise QualityError("REVIEW_REQUEST phase inconsistente")
    req_cov = Decimal(metrics["coverage_pct"])
    if abs(req_cov - Decimal(summary.coverage_display())) > Decimal("0.15"):
        raise QualityError("REVIEW_REQUEST coverage inconsistente")

    q = manifest.get("quality")
    if not isinstance(q, dict):
        raise QualityError("manifest.quality ausente")
    if int(q.get("test_count", -1)) != summary.test_count:
        raise QualityError("manifest.quality.test_count inconsistente")
    man_cov = Decimal(str(q.get("coverage_pct")))
    if abs(man_cov - summary.coverage_pct) > Decimal("0.2") and abs(
        man_cov - Decimal(summary.coverage_display())
    ) > Decimal("0.2"):
        raise QualityError("manifest.quality.coverage_pct inconsistente")
    if int(manifest.get("phase", -1)) != phase:
        raise QualityError("manifest.phase inconsistente")
    if str(manifest.get("package_version")) != version:
        raise QualityError("manifest.package_version inconsistente")

    files = manifest.get("files")
    if not isinstance(files, list):
        raise QualityError("manifest.files ausente")
    if int(manifest.get("file_count", -1)) != len(files):
        raise QualityError("manifest.file_count != len(files)")
    if "REVIEW_PACKAGE_MANIFEST.json" not in files:
        raise QualityError("manifest no se incluye a sí mismo en files")
    if zip_member_count is not None and zip_member_count != len(files):
        raise QualityError(f"ZIP members={zip_member_count} != manifest.file_count={len(files)}")
