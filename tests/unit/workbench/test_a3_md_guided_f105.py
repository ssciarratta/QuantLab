"""Tests A3 MD capability + Guided Lab env opt-in (F105)."""

from __future__ import annotations

from pathlib import Path

import pytest

from quantlab import __version__
from quantlab.brokers.a3.md_backend import a3_md_capability_status
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import WorkbenchState, handle_get_a3_md_status
from quantlab.workbench.session import WorkbenchSession


def test_version_f105() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.99.0"
    assert PHASES_SUMMARY == "F19–F107 INTERNAL"
    assert not Path("docs/audit/FASE_105_APPROVED.md").exists()


def test_a3_md_status_default_not_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("QUANTLAB_A3_MD_READONLY", raising=False)
    monkeypatch.delenv("QUANTLAB_A3_USER", raising=False)
    st = a3_md_capability_status()
    assert st["ok"] is True
    assert st["env_ready"] is False
    assert st["md_readonly_flag"] is False
    assert st["live_routing"] is False
    # No secret values in payload (keys de env sí pueden nombrarse).
    blob = repr(st)
    assert "secret_value" not in blob


def test_a3_md_status_ready_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QUANTLAB_A3_MD_READONLY", "1")
    monkeypatch.setenv("QUANTLAB_A3_USER", "u")
    monkeypatch.setenv("QUANTLAB_A3_PASSWORD", "super-secret-pass")
    monkeypatch.setenv("QUANTLAB_A3_ACCOUNT", "a")
    st = a3_md_capability_status()
    assert st["env_ready"] is True
    assert st["credentials_configured"] is True
    assert "super-secret-pass" not in repr(st)


def test_api_a3_md_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("QUANTLAB_A3_MD_READONLY", raising=False)
    session = WorkbenchSession.create_or_load(tmp_path, "a3md")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    out = handle_get_a3_md_status(state)
    assert out["kind"] == "a3_md_status"
    assert out["env_ready"] is False


def test_guided_lab_has_a3_md_controls() -> None:
    root = Path(__file__).resolve().parents[3] / "src" / "quantlab" / "workbench" / "static"
    js = (root / "js" / "panes" / "guided_lab.js").read_text(encoding="utf-8")
    assert "gl-a3-md" in js
    assert "a3MdStatus" in js
    assert "transport=" in js
    assert "a3MdStatus" in (root / "js" / "api.js").read_text(encoding="utf-8")
