"""Tests de métricas estructuradas y del defecto v1.2 (test_count)."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from review_package_quality import (  # noqa: E402
    QualityError,
    QualitySummary,
    assert_document_consistency,
    parse_coverage_xml,
    parse_junit_xml,
    render_metrics_block,
    upsert_metrics_block,
)


def _write_junit(
    path: Path,
    *,
    tests: int,
    failures: int = 0,
    errors: int = 0,
    skipped: int = 0,
) -> None:
    path.write_text(
        (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            f'<testsuite name="pytest" tests="{tests}" failures="{failures}" '
            f'errors="{errors}" skipped="{skipped}"></testsuite>\n'
        ),
        encoding="utf-8",
    )


def _write_coverage(path: Path, line_rate: str = "0.8966") -> None:
    path.write_text(
        f'<?xml version="1.0" ?><coverage line-rate="{line_rate}" '
        f'branch-rate="0.8" version="7.0" timestamp="1"></coverage>\n',
        encoding="utf-8",
    )


def test_junit_parses_34_tests(tmp_path: Path) -> None:
    junit = tmp_path / "junit.xml"
    _write_junit(junit, tests=34)
    tests, passed, failed, errors, skipped = parse_junit_xml(junit)
    assert tests == 34
    assert passed == 34
    assert failed == errors == skipped == 0


def test_junit_counts_skipped_and_parametrized_totals(tmp_path: Path) -> None:
    junit = tmp_path / "junit.xml"
    _write_junit(junit, tests=10, failures=1, errors=1, skipped=2)
    tests, passed, failed, errors, skipped = parse_junit_xml(junit)
    assert tests == 10
    assert passed == 6
    assert failed == 1
    assert errors == 1
    assert skipped == 2


def test_junit_malformed_rejected(tmp_path: Path) -> None:
    bad = tmp_path / "bad.xml"
    bad.write_text("<not-closed>", encoding="utf-8")
    with pytest.raises(QualityError, match="malformado"):
        parse_junit_xml(bad)


def test_pass_with_zero_tests_rejected() -> None:
    summary = QualitySummary(
        test_count=0,
        passed=0,
        failed=0,
        errors=0,
        skipped=0,
        coverage_pct=Decimal("90.0"),
        ruff_exit_code=0,
        format_exit_code=0,
        mypy_exit_code=0,
        pytest_exit_code=0,
        coverage_exit_code=0,
        vertical_slice_exit_code=0,
        secret_scan_exit_code=0,
        authoritative=True,
        junit_report="reports/pytest_junit.xml",
        coverage_report="reports/coverage.xml",
    )
    with pytest.raises(QualityError, match="test_count==0"):
        summary.validate()


def test_coverage_xml_independent_of_console_locale(tmp_path: Path) -> None:
    cov = tmp_path / "coverage.xml"
    _write_coverage(cov, "0.9")
    assert parse_coverage_xml(cov) == Decimal("90.00")


def test_consistency_rejects_mismatched_test_count() -> None:
    summary = QualitySummary(
        test_count=34,
        passed=34,
        failed=0,
        errors=0,
        skipped=0,
        coverage_pct=Decimal("89.7"),
        ruff_exit_code=0,
        format_exit_code=0,
        mypy_exit_code=0,
        pytest_exit_code=0,
        coverage_exit_code=0,
        vertical_slice_exit_code=0,
        secret_scan_exit_code=0,
        authoritative=True,
        junit_report="reports/pytest_junit.xml",
        coverage_report="reports/coverage.xml",
    )
    status = (
        "# PROJECT STATUS\n**Fase actual:** 2\n**Versión del paquete:** 1.3\n"
        "| Tests | 0 |\n| Cobertura | 89.7% |\n"
    )
    request = upsert_metrics_block(
        "# REVIEW\n",
        render_metrics_block(summary, phase=2, version="1.3"),
    )
    manifest = {
        "phase": 2,
        "package_version": "1.3",
        "file_count": 1,
        "files": ["REVIEW_PACKAGE_MANIFEST.json"],
        "quality": summary.to_dict(),
    }
    with pytest.raises(QualityError, match="PROJECT_STATUS Tests"):
        assert_document_consistency(
            summary=summary,
            phase=2,
            version="1.3",
            project_status=status,
            review_request=request,
            manifest=manifest,
        )


def test_consistency_rejects_file_count_mismatch() -> None:
    summary = QualitySummary(
        test_count=34,
        passed=34,
        failed=0,
        errors=0,
        skipped=0,
        coverage_pct=Decimal("89.7"),
        ruff_exit_code=0,
        format_exit_code=0,
        mypy_exit_code=0,
        pytest_exit_code=0,
        coverage_exit_code=0,
        vertical_slice_exit_code=0,
        secret_scan_exit_code=0,
        authoritative=True,
        junit_report="reports/pytest_junit.xml",
        coverage_report="reports/coverage.xml",
    )
    status = (
        "# PROJECT STATUS\n**Fase actual:** 2\n**Versión del paquete:** 1.3\n"
        "| Tests | 34 |\n| Cobertura | 89.7% |\n"
    )
    request = upsert_metrics_block(
        "# REVIEW\n",
        render_metrics_block(summary, phase=2, version="1.3"),
    )
    manifest = {
        "phase": 2,
        "package_version": "1.3",
        "file_count": 2,
        "files": ["REVIEW_PACKAGE_MANIFEST.json"],
        "quality": summary.to_dict(),
    }
    with pytest.raises(QualityError, match="file_count"):
        assert_document_consistency(
            summary=summary,
            phase=2,
            version="1.3",
            project_status=status,
            review_request=request,
            manifest=manifest,
        )


def test_consistency_accepts_aligned_artifacts() -> None:
    summary = QualitySummary(
        test_count=34,
        passed=34,
        failed=0,
        errors=0,
        skipped=0,
        coverage_pct=Decimal("89.66"),
        ruff_exit_code=0,
        format_exit_code=0,
        mypy_exit_code=0,
        pytest_exit_code=0,
        coverage_exit_code=0,
        vertical_slice_exit_code=0,
        secret_scan_exit_code=0,
        authoritative=True,
        junit_report="reports/pytest_junit.xml",
        coverage_report="reports/coverage.xml",
    )
    status = (
        "# PROJECT STATUS\n**Fase actual:** 2\n**Versión del paquete:** 1.3\n"
        f"| Tests | 34 |\n| Cobertura | {summary.coverage_display()}% |\n"
    )
    request = upsert_metrics_block(
        "# REVIEW\n",
        render_metrics_block(summary, phase=2, version="1.3"),
    )
    files = ["README.md", "REVIEW_PACKAGE_MANIFEST.json"]
    manifest = {
        "phase": 2,
        "package_version": "1.3",
        "file_count": len(files),
        "files": files,
        "quality": summary.to_dict(),
    }
    assert_document_consistency(
        summary=summary,
        phase=2,
        version="1.3",
        project_status=status,
        review_request=request,
        manifest=manifest,
        zip_member_count=2,
    )
