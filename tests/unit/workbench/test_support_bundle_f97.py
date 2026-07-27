"""Tests Support Bundle ZIP (F97) — paquete read-only para soporte."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import WorkbenchState, handle_get_support_bundle
from quantlab.workbench.api_catalog import API_ROUTES
from quantlab.workbench.session import WorkbenchSession


def _static_root() -> Path:
    return Path(__file__).resolve().parents[3] / "src" / "quantlab" / "workbench" / "static"


def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.97.0"
    assert PHASES_SUMMARY == "F19–F105 INTERNAL"
    assert not Path("docs/audit/FASE_97_APPROVED.md").exists()


def test_support_bundle_zip_members(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "bundle")
    state = WorkbenchState(session=session, session_parent=tmp_path)

    body, filename = handle_get_support_bundle(state)

    assert filename == "quantlab-support-bundle.zip"
    assert body[:2] == b"PK"
    with zipfile.ZipFile(io.BytesIO(body), "r") as zf:
        names = set(zf.namelist())
        assert names == {
            "README.txt",
            "diagnostics.json",
            "about.json",
            "openapi.json",
            "venues.json",
            "reconciliation.json",
        }
        diag = json.loads(zf.read("diagnostics.json"))
        assert diag["kind"] == "diagnostics"
        assert diag["live_blocked"] is True
        assert diag["version"] == __version__
        about = json.loads(zf.read("about.json"))
        assert about["version"] == __version__
        assert about["live_blocked"] is True
        readme = zf.read("README.txt").decode("utf-8")
        assert "live_blocked=True" in readme
        assert "journal" not in readme.lower() or "No incluye journal" in readme


def test_support_bundle_filename_sanitized(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "s3ss-01")
    state = WorkbenchState(session=session, session_parent=tmp_path)

    _, filename = handle_get_support_bundle(state)

    assert filename.startswith("quantlab-support-")
    assert filename.endswith(".zip")
    stem = filename[len("quantlab-support-") : -len(".zip")]
    assert all(ch.isalnum() or ch in "-_" for ch in stem)


def test_route_declared_in_catalog() -> None:
    paths = {(r.path, r.method) for r in API_ROUTES}
    assert ("/api/support-bundle.zip", "GET") in paths


def test_pane_has_bundle_button() -> None:
    js = (_static_root() / "js" / "panes" / "diagnostics.js").read_text(encoding="utf-8")
    assert "/api/support-bundle.zip" in js
    assert "diag-bundle" in js
    api_text = (_static_root() / "js" / "api.js").read_text(encoding="utf-8")
    assert "supportBundleUrl" in api_text


def test_bundle_does_not_include_journal_or_book(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "safe")
    # crear journal/book no vacíos
    session.journal_path.write_text('{"fill_id":"x"}\n', encoding="utf-8")
    state = WorkbenchState(session=session, session_parent=tmp_path)

    body, _ = handle_get_support_bundle(state)
    with zipfile.ZipFile(io.BytesIO(body), "r") as zf:
        for name in zf.namelist():
            assert "journal" not in name.lower()
            assert "book" not in name.lower()
            assert not name.endswith(".jsonl")
