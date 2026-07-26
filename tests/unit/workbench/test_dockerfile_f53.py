"""F53 — Dockerfile.workbench opt-in (parse file; no docker build required)."""

from __future__ import annotations

import re
from pathlib import Path

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY

ROOT = Path(__file__).resolve().parents[3]
DOCKERFILE = ROOT / "Dockerfile.workbench"
DOCKERIGNORE = ROOT / ".dockerignore"
OPS_DOC = ROOT / "docs" / "ops" / "DOCKER_WORKBENCH.md"


def _cmd_tokens(text: str) -> list[str]:
    """Extract tokens from a Dockerfile CMD exec-form line."""
    match = re.search(r"^CMD\s+\[(.+)\]\s*$", text, flags=re.MULTILINE)
    assert match is not None, "Dockerfile.workbench must declare an exec-form CMD"
    raw = match.group(1)
    return [tok.strip().strip('"').strip("'") for tok in raw.split(",")]


def test_live_blocked_and_version_f53() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.86.0"
    assert PHASES_SUMMARY == "F19–F94 INTERNAL"


def test_dockerfile_workbench_exists() -> None:
    assert DOCKERFILE.is_file(), f"missing {DOCKERFILE}"


def test_dockerfile_base_python312_slim() -> None:
    text = DOCKERFILE.read_text(encoding="utf-8")
    assert "FROM python:3.12-slim" in text
    assert "uv sync" in text
    assert "EXPOSE 8765" in text


def test_dockerfile_cmd_allow_non_loopback_no_browser() -> None:
    text = DOCKERFILE.read_text(encoding="utf-8")
    tokens = _cmd_tokens(text)
    assert "quantlab-workbench" in tokens
    assert "--host" in tokens
    assert "0.0.0.0" in tokens
    assert "--allow-non-loopback" in tokens
    assert "--no-browser" in tokens
    # Risk must be documented in the Dockerfile itself.
    assert "RISK" in text or "riesgo" in text.lower()
    assert "allow-non-loopback" in text
    assert "no-browser" in text


def test_dockerignore_excludes_secrets() -> None:
    assert DOCKERIGNORE.is_file()
    text = DOCKERIGNORE.read_text(encoding="utf-8")
    assert ".env" in text
    assert "data/" in text or "data" in text
    assert "*.secret" in text or ".secret" in text


def test_ops_doc_loopback_publish() -> None:
    assert OPS_DOC.is_file()
    text = OPS_DOC.read_text(encoding="utf-8")
    assert "127.0.0.1:8765:8765" in text
    assert "allow-non-loopback" in text
    assert "Dockerfile.workbench" in text
