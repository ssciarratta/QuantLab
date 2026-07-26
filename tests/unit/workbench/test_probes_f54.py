"""F54 — Readiness / Liveness probes (/api/livez, /api/readyz)."""

from __future__ import annotations

import contextlib
import http.client
import json
import os
import stat
import threading
from pathlib import Path
from unittest.mock import patch

import pytest

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import WorkbenchState, handle_get_livez, handle_get_readyz
from quantlab.workbench.probes import is_session_root_writable, livez_payload, readyz_payload
from quantlab.workbench.server import create_server
from quantlab.workbench.session import WorkbenchSession


def test_live_blocked_and_version_f54() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.52.0"
    assert PHASES_SUMMARY == "F19–F60 INTERNAL"


def test_livez_payload_always_alive() -> None:
    payload = livez_payload()
    assert payload["ok"] is True
    assert payload["alive"] is True
    assert payload["status"] == "alive"
    assert payload["kind"] == "livez"
    assert payload["version"] == "0.52.0"
    assert payload["live_blocked"] is True
    assert payload["live_routing"] is False


def test_handle_get_livez(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "livez")
    state = WorkbenchState(session=session)
    payload = handle_get_livez(state)
    assert payload["ok"] is True
    assert payload["alive"] is True


def test_readyz_ready_when_live_blocked_and_writable(tmp_path: Path) -> None:
    root = tmp_path / "sess"
    root.mkdir()
    payload = readyz_payload(session_root=root)
    assert payload["ready"] is True
    assert payload["ok"] is True
    assert payload["status"] == "ready"
    assert payload["checks"]["live_blocked"] is True
    assert payload["checks"]["session_root_writable"] is True


def test_readyz_503_when_live_blocked_false(tmp_path: Path) -> None:
    root = tmp_path / "sess"
    root.mkdir()
    payload = readyz_payload(session_root=root, live_blocked=False)
    assert payload["ready"] is False
    assert payload["ok"] is False
    assert payload["status"] == "not_ready"
    assert payload["checks"]["live_blocked"] is False
    assert "LIVE_BLOCKED" in str(payload.get("error", ""))


def test_readyz_not_writable_missing_root(tmp_path: Path) -> None:
    missing = tmp_path / "nope"
    assert is_session_root_writable(missing) is False
    payload = readyz_payload(session_root=missing)
    assert payload["ready"] is False
    assert payload["checks"]["session_root_writable"] is False


def test_readyz_not_writable_readonly_dir(tmp_path: Path) -> None:
    root = tmp_path / "ro"
    root.mkdir()
    # Best-effort: chmod u-w; skip if we cannot make it non-writable (e.g. root).
    mode = root.stat().st_mode
    os.chmod(root, mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)
    try:
        if os.access(root, os.W_OK):
            pytest.skip("filesystem still writable after chmod")
        assert is_session_root_writable(root) is False
        payload = readyz_payload(session_root=root)
        assert payload["ready"] is False
        assert payload["checks"]["session_root_writable"] is False
    finally:
        os.chmod(root, mode)


def test_handle_get_readyz_ok(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "ready")
    state = WorkbenchState(session=session)
    state.ensure_session()
    payload = handle_get_readyz(state)
    assert payload["ready"] is True
    assert payload["checks"]["live_blocked"] is True
    assert payload["checks"]["session_root_writable"] is True


def test_handle_get_readyz_mocked_gate(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "gate")
    state = WorkbenchState(session=session)
    state.ensure_session()
    with patch("quantlab.workbench.probes.LIVE_BLOCKED", False):
        payload = handle_get_readyz(state)
    assert payload["ready"] is False
    assert payload["checks"]["live_blocked"] is False


def test_http_livez_and_readyz(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "http-probe")
    state = WorkbenchState(session=session)
    state.ensure_session()
    server = create_server(host="127.0.0.1", port=0, state=state)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    try:
        conn = http.client.HTTPConnection(host, port, timeout=5.0)
        try:
            conn.request("GET", "/api/livez")
            resp = conn.getresponse()
            raw = resp.read()
            assert resp.status == 200, raw
            live = json.loads(raw.decode("utf-8"))
            assert live["alive"] is True
            assert live["ok"] is True

            conn.request("GET", "/api/readyz")
            resp = conn.getresponse()
            raw = resp.read()
            assert resp.status == 200, raw
            ready = json.loads(raw.decode("utf-8"))
            assert ready["ready"] is True
            assert ready["ok"] is True
        finally:
            conn.close()
    finally:
        with contextlib.suppress(Exception):
            server.shutdown()
        server.server_close()


def test_http_readyz_503_when_not_ready(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "http-503")
    state = WorkbenchState(session=session)
    state.ensure_session()
    server = create_server(host="127.0.0.1", port=0, state=state)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    try:
        with patch("quantlab.workbench.probes.LIVE_BLOCKED", False):
            conn = http.client.HTTPConnection(host, port, timeout=5.0)
            try:
                conn.request("GET", "/api/readyz")
                resp = conn.getresponse()
                raw = resp.read()
                assert resp.status == 503, raw
                body = json.loads(raw.decode("utf-8"))
                assert body["ready"] is False
                assert body["ok"] is False
            finally:
                conn.close()
    finally:
        with contextlib.suppress(Exception):
            server.shutdown()
        server.server_close()


def test_ops_doc_mentions_probes() -> None:
    ops = Path(__file__).resolve().parents[3] / "docs" / "ops" / "DOCKER_WORKBENCH.md"
    text = ops.read_text(encoding="utf-8")
    assert "/api/livez" in text
    assert "/api/readyz" in text
    assert "HEALTHCHECK" in text or "healthcheck" in text.lower()
