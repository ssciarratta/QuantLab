"""Tests del generador y política del Review Package."""

from __future__ import annotations

import json
import shutil
import sys
import zipfile
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_review_package import (  # noqa: E402
    ReviewPackageError,
    build_zip,
    collect_candidate_files,
    scan_secrets,
    sha256_file,
    validate_file_for_package,
    validate_zip,
    write_package_manifest,
    write_structural_validation_report,
)
from review_package_policy import (  # noqa: E402
    MAX_FILE_SIZE_BYTES,
    REQUIRED_DOC_FILES,
    is_dangerous_arcname,
    should_exclude_relative,
)
from review_package_quality import QualitySummary  # noqa: E402


def _sample_summary(**overrides: object) -> QualitySummary:
    data: dict[str, object] = {
        "test_count": 34,
        "passed": 34,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "coverage_pct": Decimal("89.66"),
        "ruff_exit_code": 0,
        "format_exit_code": 0,
        "mypy_exit_code": 0,
        "pytest_exit_code": 0,
        "coverage_exit_code": 0,
        "vertical_slice_exit_code": 0,
        "secret_scan_exit_code": 0,
        "authoritative": True,
        "junit_report": "reports/pytest_junit.xml",
        "coverage_report": "reports/coverage.xml",
    }
    data.update(overrides)
    return QualitySummary(**data)  # type: ignore[arg-type]


def _seed_min_project(tmp: Path) -> None:
    """Crea un proyecto mínimo compatible con el generador."""
    (tmp / "src" / "quantlab").mkdir(parents=True)
    (tmp / "tests").mkdir()
    (tmp / "scripts").mkdir()
    (tmp / "config").mkdir()
    (tmp / "docs").mkdir()
    (tmp / "learning").mkdir()
    (tmp / "reports").mkdir()
    (tmp / ".github" / "workflows").mkdir(parents=True)

    for name in (
        "README.md",
        "CHANGELOG.md",
        "LESSONS_LEARNED.md",
        "PROJECT_STATUS.md",
        "REVIEW_REQUEST.md",
        "LICENSE",
        ".gitignore",
        "pyproject.toml",
        "tree.txt",
    ):
        (tmp / name).write_text(f"{name}\n", encoding="utf-8")

    (tmp / "uv.lock").write_text("version = 1\n", encoding="utf-8")
    (tmp / ".gitleaks.toml").write_text("title = 'quantlab'\n", encoding="utf-8")
    (tmp / "docs" / "MANIFEST_VERSIONING.md").write_text("# versioning\n", encoding="utf-8")
    (tmp / "docs" / "REVIEW_PACKAGE.md").write_text("# review package\n", encoding="utf-8")
    for rel in REQUIRED_DOC_FILES:
        path = tmp / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(f"# {path.name}\n", encoding="utf-8")
    (tmp / "config" / "defaults.yaml").write_text("project: test\n", encoding="utf-8")
    (tmp / "learning" / "decisiones.txt").write_text("DEC-000\n", encoding="utf-8")
    (tmp / "src" / "quantlab" / "__init__.py").write_text(
        "__version__='0.2.0'\n",
        encoding="utf-8",
    )
    (tmp / "tests" / "test_smoke.py").write_text(
        "def test_ok():\n    assert True\n",
        encoding="utf-8",
    )
    (tmp / "scripts" / "build_review_package.py").write_text("# stub\n", encoding="utf-8")
    (tmp / ".github" / "workflows" / "ci.yml").write_text("name: ci\n", encoding="utf-8")

    for report in (
        "ruff_report.txt",
        "format_report.txt",
        "mypy_report.txt",
        "pytest_report.txt",
        "coverage.txt",
        "vertical_slice_report.txt",
        "secret_scan_report.txt",
        "install_report.txt",
        "review_package_validation.txt",
    ):
        (tmp / "reports" / report).write_text(
            "command: test\nstarted_at_utc: t\nexit_code: 0\nresult: PASS\nvalidation=PASS\n",
            encoding="utf-8",
        )
    (tmp / "reports" / "coverage.xml").write_text(
        '<?xml version="1.0"?><coverage line-rate="0.9" branch-rate="0.8" '
        'version="7" timestamp="1"></coverage>\n',
        encoding="utf-8",
    )
    (tmp / "reports" / "pytest_junit.xml").write_text(
        '<?xml version="1.0"?><testsuite name="pytest" tests="34" '
        'failures="0" errors="0" skipped="0"></testsuite>\n',
        encoding="utf-8",
    )
    (tmp / "reports" / "quality_summary.json").write_text(
        json.dumps(_sample_summary().to_dict(), indent=2) + "\n",
        encoding="utf-8",
    )


def test_policy_excludes_caches_venv_git_env_and_prior_zips() -> None:
    assert should_exclude_relative(Path("__pycache__/x.py")).excluded
    assert should_exclude_relative(Path("src/a.pyc")).excluded
    assert should_exclude_relative(Path(".venv/lib/x.py")).excluded
    assert should_exclude_relative(Path("venv/lib/x.py")).excluded
    assert should_exclude_relative(Path(".git/config")).excluded
    assert should_exclude_relative(Path(".env")).excluded
    assert should_exclude_relative(Path("QuantLab_Review_Fase_02_v1.1.zip")).excluded
    assert should_exclude_relative(Path("QuantLab_Review_Fase_02_v1.1.zip.sha256")).excluded
    assert should_exclude_relative(Path("QuantLab_Review_Fase_02_v1.3.validation.txt")).excluded
    assert not should_exclude_relative(Path("src/quantlab/core/types/orders.py")).excluded


def test_dangerous_paths_and_credential_url_rejected(tmp_path: Path) -> None:
    assert is_dangerous_arcname("../etc/passwd") is not None
    assert is_dangerous_arcname("/abs/path") is not None
    assert is_dangerous_arcname("C:/Windows/x") is not None
    assert is_dangerous_arcname("src/ok.py") is None

    _seed_min_project(tmp_path)
    bad = tmp_path / "docs" / "leak.md"
    leaked = "https://" + "user" + ":" + "xsecret" + "@" + "example.com/repo"
    bad.write_text("url=" + leaked + "\n", encoding="utf-8")
    findings = scan_secrets(tmp_path, [bad])
    assert findings


def test_large_file_rejected(tmp_path: Path) -> None:
    _seed_min_project(tmp_path)
    big = tmp_path / "docs" / "huge.bin"
    big.write_bytes(b"x" * (MAX_FILE_SIZE_BYTES + 1))
    with pytest.raises(ReviewPackageError):
        validate_file_for_package(tmp_path, big)


def test_collect_is_deterministic_and_excludes_pycache(tmp_path: Path) -> None:
    _seed_min_project(tmp_path)
    cache = tmp_path / "src" / "quantlab" / "__pycache__"
    cache.mkdir()
    (cache / "x.pyc").write_bytes(b"\0\0")
    (tmp_path / "src" / "quantlab" / "mod.py").write_text("x=1\n", encoding="utf-8")

    a = [p.relative_to(tmp_path).as_posix() for p in collect_candidate_files(tmp_path)]
    b = [p.relative_to(tmp_path).as_posix() for p in collect_candidate_files(tmp_path)]
    assert a == b
    assert all("__pycache__" not in n for n in a)
    assert all(not n.endswith(".pyc") for n in a)
    assert "src/quantlab/mod.py" in a


def test_zip_roundtrip_and_does_not_modify_unrelated_repo_files(tmp_path: Path) -> None:
    _seed_min_project(tmp_path)
    sentinel = tmp_path / "sentinel.txt"
    sentinel.write_text("keep\n", encoding="utf-8")
    files = collect_candidate_files(tmp_path)
    write_package_manifest(
        tmp_path,
        phase=2,
        version="1.3",
        files=files,
        summary=_sample_summary(),
    )
    files = collect_candidate_files(tmp_path)
    expected = [p.relative_to(tmp_path).as_posix() for p in files]
    out_dir = tmp_path / "_out"
    out_dir.mkdir()
    zip_path = out_dir / "pkg.zip"
    before = sentinel.read_text(encoding="utf-8")
    build_zip(tmp_path, zip_path, files)
    assert zipfile.is_zipfile(zip_path)
    result = validate_zip(tmp_path, zip_path, expected)
    assert result.extract_ok
    assert result.member_count == len(expected)
    assert sentinel.read_text(encoding="utf-8") == before
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    assert "README.md" in names
    assert "REVIEW_PACKAGE_MANIFEST.json" in names
    assert all("__pycache__" not in n for n in names)


def test_missing_required_file_fails_validation(tmp_path: Path) -> None:
    _seed_min_project(tmp_path)
    (tmp_path / "README.md").unlink()
    files = collect_candidate_files(tmp_path)
    write_package_manifest(
        tmp_path,
        phase=2,
        version="1.3",
        files=files,
        summary=_sample_summary(),
    )
    files = collect_candidate_files(tmp_path)
    expected = [p.relative_to(tmp_path).as_posix() for p in files]
    zip_path = tmp_path / "_out.zip"
    build_zip(tmp_path, zip_path, files)
    with pytest.raises(ReviewPackageError, match="falta"):
        validate_zip(tmp_path, zip_path, expected)


def test_manifest_lists_files_deterministically(tmp_path: Path) -> None:
    _seed_min_project(tmp_path)
    files = collect_candidate_files(tmp_path)
    m1 = write_package_manifest(
        tmp_path, phase=2, version="1.3", files=files, summary=_sample_summary()
    )
    m2 = write_package_manifest(
        tmp_path, phase=2, version="1.3", files=files, summary=_sample_summary()
    )
    assert m1["files"] == m2["files"]
    assert m1["files"] == sorted(m1["files"])
    assert m1["quality"]["test_count"] == 34
    data = json.loads((tmp_path / "REVIEW_PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
    assert data["project_name"] == "QuantLab"
    assert data["file_count_includes_manifest"] is True


def test_original_tree_not_deleted_by_collect(tmp_path: Path) -> None:
    _seed_min_project(tmp_path)
    marker = tmp_path / "src" / "quantlab" / "keep_me.py"
    marker.write_text("ok\n", encoding="utf-8")
    collect_candidate_files(tmp_path)
    assert marker.exists()
    clone = tmp_path / "clone"
    shutil.copytree(
        tmp_path,
        clone,
        ignore=shutil.ignore_patterns("_out", "clone"),
    )
    collect_candidate_files(clone)
    assert (tmp_path / "src" / "quantlab" / "keep_me.py").read_text(encoding="utf-8") == "ok\n"


def test_structural_report_contains_validation_pass_not_preonly(tmp_path: Path) -> None:
    _seed_min_project(tmp_path)
    files = collect_candidate_files(tmp_path)
    write_package_manifest(tmp_path, phase=2, version="1.3", files=files, summary=_sample_summary())
    files = collect_candidate_files(tmp_path)
    expected = [p.relative_to(tmp_path).as_posix() for p in files]
    out = tmp_path / "_out"
    out.mkdir()
    zip_path = out / "pkg.zip"
    build_zip(tmp_path, zip_path, files)
    result = validate_zip(tmp_path, zip_path, expected)
    report = tmp_path / "reports" / "review_package_validation.txt"
    write_structural_validation_report(
        report,
        zip_name="QuantLab_Review_Fase_02_v1.3.zip",
        phase=2,
        version="1.3",
        result=result,
    )
    text = report.read_text(encoding="utf-8")
    assert "validation=PASS" in text
    assert "pre_zip_structural_gate" not in text
    assert "reports_ready" not in text
    assert "validated_members".upper() in text.upper() or "VALIDATED_MEMBERS" in text
    assert "sha256_location=sidecar_only" in text


def test_sidecar_matches_zip_bytes_and_tamper_detected(tmp_path: Path) -> None:
    _seed_min_project(tmp_path)
    files = collect_candidate_files(tmp_path)
    out = tmp_path / "_out"
    out.mkdir()
    zip_path = out / "pkg.zip"
    build_zip(tmp_path, zip_path, files)
    digest = sha256_file(zip_path)
    sidecar = out / "pkg.zip.sha256"
    sidecar.write_text(f"{digest}  pkg.zip\n", encoding="utf-8")
    assert sidecar.read_text(encoding="utf-8").split()[0] == digest

    # Tamper
    raw = bytearray(zip_path.read_bytes())
    raw[-1] = (raw[-1] + 1) % 256
    zip_path.write_bytes(raw)
    assert sha256_file(zip_path) != digest


def test_member_list_mismatch_after_validate_fails(tmp_path: Path) -> None:
    _seed_min_project(tmp_path)
    files = collect_candidate_files(tmp_path)
    write_package_manifest(tmp_path, phase=2, version="1.3", files=files, summary=_sample_summary())
    files = collect_candidate_files(tmp_path)
    expected = [p.relative_to(tmp_path).as_posix() for p in files]
    out = tmp_path / "_out"
    out.mkdir()
    zip_path = out / "pkg.zip"
    build_zip(tmp_path, zip_path, files)
    validate_zip(tmp_path, zip_path, expected)
    # Reconstruir con miembro extra no esperado
    with zipfile.ZipFile(zip_path, "w") as zf:
        for path in files:
            zf.write(path, arcname=path.relative_to(tmp_path).as_posix())
        zf.writestr("extra_smuggled.txt", "x")
    with pytest.raises(ReviewPackageError, match="no coincide"):
        validate_zip(tmp_path, zip_path, expected)


def test_extract_rejects_traversal(tmp_path: Path) -> None:
    out = tmp_path / "_out"
    out.mkdir()
    zip_path = out / "evil.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("../evil.txt", "x")
    with pytest.raises(ReviewPackageError):
        validate_zip(tmp_path, zip_path, ["../evil.txt"])
