"""Tests hardening non-loopback (F25 M2)."""

from __future__ import annotations

import io
from contextlib import redirect_stderr
from pathlib import Path

import pytest

from quantlab.workbench.launch import build_parser, is_loopback_host, main


@pytest.mark.parametrize(
    ("host", "expected"),
    [
        ("127.0.0.1", True),
        ("localhost", True),
        ("LOCALHOST", True),
        ("::1", True),
        ("[::1]", True),
        ("0.0.0.0", False),
        ("192.168.1.10", False),
        ("example.com", False),
    ],
)
def test_is_loopback_host(host: str, expected: bool) -> None:
    assert is_loopback_host(host) is expected


def test_parser_has_allow_non_loopback() -> None:
    parser = build_parser()
    args = parser.parse_args(["--host", "0.0.0.0", "--allow-non-loopback"])
    assert args.host == "0.0.0.0"
    assert args.allow_non_loopback is True
    default = parser.parse_args([])
    assert default.allow_non_loopback is False


def test_main_aborts_non_loopback_without_flag() -> None:
    err = io.StringIO()
    with redirect_stderr(err):
        code = main(["--host", "0.0.0.0", "--no-browser"])
    assert code == 2
    assert "no es loopback" in err.getvalue()
    assert "--allow-non-loopback" in err.getvalue()


def test_main_allows_loopback_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Smoke: parse + gate pass; stop before serve_forever."""

    class _FakeServer:
        server_address = ("127.0.0.1", 8765)

        def serve_forever(self) -> None:
            raise KeyboardInterrupt

        def shutdown(self) -> None:
            return None

        def server_close(self) -> None:
            return None

    monkeypatch.setattr(
        "quantlab.workbench.launch.create_server",
        lambda **_kwargs: _FakeServer(),
    )
    code = main(["--no-browser", "--session-root", str(tmp_path / "ql-wb-test-loopback")])
    assert code == 0


def test_main_allows_non_loopback_with_flag_and_warns(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """DoD F25: --allow-non-loopback permite bind + WARNING stderr."""

    class _FakeServer:
        server_address = ("0.0.0.0", 8765)

        def serve_forever(self) -> None:
            raise KeyboardInterrupt

        def shutdown(self) -> None:
            return None

        def server_close(self) -> None:
            return None

    monkeypatch.setattr(
        "quantlab.workbench.launch.create_server",
        lambda **_kwargs: _FakeServer(),
    )
    err = io.StringIO()
    with redirect_stderr(err):
        code = main(
            [
                "--host",
                "0.0.0.0",
                "--allow-non-loopback",
                "--no-browser",
                "--session-root",
                str(tmp_path / "ql-wb-test-non-loopback"),
            ]
        )
    assert code == 0
    stderr = err.getvalue()
    assert "WARNING" in stderr
    assert "non-loopback" in stderr
    assert "0.0.0.0" in stderr
