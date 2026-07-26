"""Fixtures: servidor workbench en thread con puerto efímero."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.server import create_server
from quantlab.workbench.session import WorkbenchSession


@pytest.fixture
def workbench_server(tmp_path: Path) -> Iterator[tuple[ThreadingHTTPServer, WorkbenchState]]:
    """Arranca ThreadingHTTPServer en thread daemon; port=0 → efímero."""
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "test-session")
    app_state = WorkbenchState(session=session)
    app_state.ensure_session()
    server = create_server(host="127.0.0.1", port=0, state=app_state)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server, app_state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)
