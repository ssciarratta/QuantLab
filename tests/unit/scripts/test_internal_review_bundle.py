"""Tests mínimos del bundle INTERNAL de evidencia F19–F32."""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_internal_review_bundle import (  # noqa: E402
    DEFAULT_TO_PHASE,
    InternalBundleError,
    build_bundle,
    collect_bundle_files,
    relative_arcname,
)


def _seed_project(tmp: Path) -> Path:
    (tmp / "src" / "quantlab").mkdir(parents=True)
    (tmp / "docs" / "audit").mkdir(parents=True)
    (tmp / "docs" / "ops").mkdir(parents=True)
    (tmp / "reports").mkdir(parents=True)
    (tmp / "data").mkdir(parents=True)
    (tmp / "src" / "quantlab" / "__init__.py").write_text(
        '__version__ = "0.24.0"\n',
        encoding="utf-8",
    )

    # Phase docs
    for phase, slug in (
        (19, "OPERATING_MODES"),
        (20, "WORKBENCH"),
        (26, "PAPER_SESSION"),
        (27, "STRATEGY_CATALOG"),
        (28, "LAYOUT_JOURNAL"),
        (29, "REPORTS"),
        (30, "UNIVERSE_CATALOG"),
        (31, "FEATURES_UI"),
        (32, "VALIDATION_UI"),
    ):
        (tmp / "docs" / f"FASE_{phase:02d}_{slug}.md").write_text(f"# F{phase}\n", encoding="utf-8")

    audit = tmp / "docs" / "audit"
    for name, body in (
        ("AUTO_AUDIT_2026-07-26_F19.md", "# auto F19\n"),
        ("AUTO_AUDIT_2026-07-26_F26.md", "# auto F26\n"),
        ("AUTO_AUDIT_2026-07-26_F27.md", "# auto F27\n"),
        ("AUTO_AUDIT_2026-07-26_F28.md", "# auto F28\n"),
        ("AUTO_AUDIT_2026-07-26_F29.md", "# auto F29\n"),
        ("AUTO_AUDIT_2026-07-26_F30.md", "# auto F30\n"),
        ("AUTO_AUDIT_2026-07-26_F31.md", "# auto F31\n"),
        ("AUTO_AUDIT_2026-07-26_F32.md", "# auto F32\n"),
        ("INTERNAL_AUDIT_F19.md", "# internal F19\n"),
        ("INTERNAL_AUDIT_F26.md", "# internal F26\n"),
        ("INTERNAL_AUDIT_F27.md", "# internal F27\n"),
        ("INTERNAL_AUDIT_F28.md", "# internal F28\n"),
        ("INTERNAL_AUDIT_F29.md", "# internal F29\n"),
        ("INTERNAL_AUDIT_F30.md", "# internal F30\n"),
        ("INTERNAL_AUDIT_F31.md", "# internal F31\n"),
        ("INTERNAL_AUDIT_F32.md", "# internal F32\n"),
        ("INTERNAL_AUDIT_F19_F26_NIGHT.md", "# night 26\n"),
        ("INTERNAL_AUDIT_F19_F27_NIGHT.md", "# night 27\n"),
        ("INTERNAL_AUDIT_F19_F28_NIGHT.md", "# night 28\n"),
        ("INTERNAL_AUDIT_F19_F29_NIGHT.md", "# night 29\n"),
        ("INTERNAL_AUDIT_F19_F30_NIGHT.md", "# night 30\n"),
        ("INTERNAL_AUDIT_F19_F31_NIGHT.md", "# night 31\n"),
        ("INTERNAL_AUDIT_F19_F32_NIGHT.md", "# night 32\n"),
        ("INTERNAL_AUDIT_F23_F25_ARC.md", "# arc\n"),
        ("FASE_19_REVIEW_PACKAGE.md", "# review pkg\n"),
        ("FASE_19_IMPLEMENTATION_REPORT.md", "# impl\n"),
        ("FASE_26_REVIEW_PACKAGE.md", "# review pkg 26\n"),
        ("FASE_26_IMPLEMENTATION_REPORT.md", "# impl 26\n"),
        ("FASE_27_REVIEW_PACKAGE.md", "# review pkg 27\n"),
        ("FASE_27_IMPLEMENTATION_REPORT.md", "# impl 27\n"),
        ("FASE_28_REVIEW_PACKAGE.md", "# review pkg 28\n"),
        ("FASE_28_IMPLEMENTATION_REPORT.md", "# impl 28\n"),
        ("FASE_29_REVIEW_PACKAGE.md", "# review pkg 29\n"),
        ("FASE_29_IMPLEMENTATION_REPORT.md", "# impl 29\n"),
        ("FASE_30_REVIEW_PACKAGE.md", "# review pkg 30\n"),
        ("FASE_30_IMPLEMENTATION_REPORT.md", "# impl 30\n"),
        ("FASE_31_REVIEW_PACKAGE.md", "# review pkg 31\n"),
        ("FASE_31_IMPLEMENTATION_REPORT.md", "# impl 31\n"),
        ("FASE_32_REVIEW_PACKAGE.md", "# review pkg 32\n"),
        ("FASE_32_IMPLEMENTATION_REPORT.md", "# impl 32\n"),
        ("MAPA_FASES_PARA_AUDITOR.md", "# mapa\n"),
        # Must NEVER be included
        ("FASE_19_APPROVED.md", "# SHOULD NOT SHIP\n"),
        ("FASE_26_APPROVED.md", "# SHOULD NOT SHIP\n"),
        ("FASE_27_APPROVED.md", "# SHOULD NOT SHIP\n"),
        ("FASE_28_APPROVED.md", "# SHOULD NOT SHIP\n"),
        ("FASE_29_APPROVED.md", "# SHOULD NOT SHIP\n"),
        ("FASE_30_APPROVED.md", "# SHOULD NOT SHIP\n"),
        ("FASE_31_APPROVED.md", "# SHOULD NOT SHIP\n"),
        ("FASE_32_APPROVED.md", "# SHOULD NOT SHIP\n"),
        # Outside range
        ("AUTO_AUDIT_2026-07-26_F18.md", "# F18 out\n"),
        ("INTERNAL_AUDIT_F18.md", "# F18 out\n"),
    ):
        (audit / name).write_text(body, encoding="utf-8")

    (tmp / "docs" / "ROADMAP_ALIGNED.md").write_text("# roadmap\n", encoding="utf-8")
    (tmp / "docs" / "ops" / "LIVE_FLIP_CHECKLIST.md").write_text(
        "# live flip\nLIVE_BLOCKED\n", encoding="utf-8"
    )
    (tmp / "RESUMEN_PROYECTO.txt").write_text("resumen\n", encoding="utf-8")

    # Exclusions
    (tmp / ".env").write_text("SECRET=1\n", encoding="utf-8")
    (tmp / "data" / "secret.bin").write_bytes(b"nope")
    cache = tmp / "docs" / "audit" / "__pycache__"
    cache.mkdir()
    (cache / "x.pyc").write_bytes(b"\0")

    return tmp


def test_default_to_phase_is_93() -> None:
    assert DEFAULT_TO_PHASE == 93


def test_collect_includes_expected_and_excludes_approved(tmp_path: Path) -> None:
    root = _seed_project(tmp_path)
    files = collect_bundle_files(root, from_phase=19, to_phase=32)
    names = {relative_arcname(p, root) for p in files}

    assert "docs/FASE_19_OPERATING_MODES.md" in names
    assert "docs/FASE_26_PAPER_SESSION.md" in names
    assert "docs/FASE_27_STRATEGY_CATALOG.md" in names
    assert "docs/FASE_28_LAYOUT_JOURNAL.md" in names
    assert "docs/FASE_29_REPORTS.md" in names
    assert "docs/FASE_30_UNIVERSE_CATALOG.md" in names
    assert "docs/FASE_31_FEATURES_UI.md" in names
    assert "docs/FASE_32_VALIDATION_UI.md" in names
    assert "docs/audit/AUTO_AUDIT_2026-07-26_F19.md" in names
    assert "docs/audit/AUTO_AUDIT_2026-07-26_F31.md" in names
    assert "docs/audit/AUTO_AUDIT_2026-07-26_F32.md" in names
    assert "docs/audit/INTERNAL_AUDIT_F19_F32_NIGHT.md" in names
    assert "docs/audit/INTERNAL_AUDIT_F19_F31_NIGHT.md" in names
    assert "docs/audit/INTERNAL_AUDIT_F23_F25_ARC.md" in names
    assert "docs/audit/FASE_19_IMPLEMENTATION_REPORT.md" in names
    assert "docs/audit/FASE_32_REVIEW_PACKAGE.md" in names
    assert "docs/ops/LIVE_FLIP_CHECKLIST.md" in names
    assert "RESUMEN_PROYECTO.txt" in names
    assert "docs/ROADMAP_ALIGNED.md" in names
    assert "docs/audit/MAPA_FASES_PARA_AUDITOR.md" in names

    # Exclusions
    assert "docs/audit/FASE_19_APPROVED.md" not in names
    assert "docs/audit/FASE_32_APPROVED.md" not in names
    assert "docs/audit/AUTO_AUDIT_2026-07-26_F18.md" not in names
    assert ".env" not in names
    assert "data/secret.bin" not in names
    assert not any("__pycache__" in n for n in names)


def test_build_bundle_zip_manifest_and_sha(tmp_path: Path) -> None:
    root = _seed_project(tmp_path)
    result = build_bundle(root, from_phase=19, to_phase=32)

    assert result.version == "0.24.0"
    assert result.zip_path.exists()
    assert result.sha256_path.exists()
    assert result.manifest_path.exists()
    assert result.zip_path.name == "QuantLab_Internal_Review_F19_F32_v0.24.0.zip"

    digest_line = result.sha256_path.read_text(encoding="utf-8").strip()
    assert digest_line.endswith(result.zip_path.name)
    hex_part = digest_line.split()[0]
    assert len(hex_part) == 64

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["bundle_kind"] == "INTERNAL_REVIEW"
    assert manifest["quantlab_version"] == "0.24.0"
    assert "git_tip_sha" in manifest
    assert manifest["from_phase"] == 19
    assert manifest["to_phase"] == 32
    assert isinstance(manifest["files"], list)
    assert all("APPROVED" not in Path(f).name for f in manifest["files"])

    with zipfile.ZipFile(result.zip_path, "r") as zf:
        members = zf.namelist()
    assert "docs/FASE_19_OPERATING_MODES.md" in members
    assert "docs/FASE_31_FEATURES_UI.md" in members
    assert "docs/FASE_32_VALIDATION_UI.md" in members
    assert "docs/ops/LIVE_FLIP_CHECKLIST.md" in members
    assert any(m.endswith("_MANIFEST.json") for m in members)
    assert not any("APPROVED" in m for m in members)
    assert not any(m.endswith(".env") for m in members)
    assert not any(m.startswith("data/") for m in members)


def test_build_bundle_rejects_inverted_range(tmp_path: Path) -> None:
    root = _seed_project(tmp_path)
    with pytest.raises(InternalBundleError, match="from-phase"):
        build_bundle(root, from_phase=32, to_phase=19)
