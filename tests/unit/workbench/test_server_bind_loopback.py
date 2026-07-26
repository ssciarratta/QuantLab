"""Servidor bind loopback por defecto."""

from __future__ import annotations

from http.server import ThreadingHTTPServer

from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.launch import DEFAULT_HOST
from quantlab.workbench.server import create_server


def test_default_host_is_loopback() -> None:
    assert DEFAULT_HOST == "127.0.0.1"


def test_server_bind_loopback_ephemeral(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    host, port = server.server_address[:2]
    assert host in ("127.0.0.1", "localhost")
    assert isinstance(port, int)
    assert port > 0


def test_create_server_default_host() -> None:
    server = create_server(port=0)
    try:
        host, _port = server.server_address[:2]
        assert host == "127.0.0.1"
    finally:
        server.server_close()
