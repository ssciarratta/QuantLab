"""Red-team Workbench Hardening (F43) — ataques → 400/403/ValidationError.

Cubre: path traversal (docs, zip_path, ids), LIVE reject, unbound host,
oversized body. LIVE_BLOCKED permanece True; sin flip.
"""

from __future__ import annotations

import contextlib
import http.client
import json
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import (
    ApiError,
    WorkbenchState,
    handle_get_docs_content,
    handle_get_lab_report,
    handle_post_broker_connect,
    handle_post_lab_backtest,
    handle_post_mode,
    handle_post_session_import,
)
from quantlab.workbench.docs_browser import normalize_docs_relpath, read_docs_content
from quantlab.workbench.hb_exports import validate_export_stem
from quantlab.workbench.lab_services import validate_experiment_id
from quantlab.workbench.launch import is_loopback_host, main
from quantlab.workbench.montecarlo_runs import validate_run_id as validate_mc_run_id
from quantlab.workbench.reports import validate_report_id
from quantlab.workbench.server import (
    DEFAULT_MAX_BODY_BYTES,
    create_server,
)
from quantlab.workbench.session import WorkbenchSession, validate_session_id
from quantlab.workbench.session_zip import resolve_upload_archive


def test_live_blocked_invariant() -> None:
    assert LIVE_BLOCKED is True


# --- Path traversal / charset ids -------------------------------------------------


@pytest.mark.parametrize(
    "bad",
    [
        "../etc/passwd",
        "..",
        "a/b",
        "a\\b",
        "",
        "evil..id",
        "../../x",
        "with spaces",
        "id/../other",
    ],
)
def test_session_id_traversal_rejected(bad: str) -> None:
    with pytest.raises(ValidationError):
        validate_session_id(bad)


@pytest.mark.parametrize(
    "bad",
    [
        "../x",
        "a/b",
        "..",
        "evil..rpt",
        "",
        "has space",
        "../../report",
    ],
)
def test_report_id_traversal_rejected(bad: str) -> None:
    with pytest.raises(ValidationError):
        validate_report_id(bad)


@pytest.mark.parametrize(
    "bad",
    [
        "../exp",
        "a/b",
        "exp..id",
        "",
        "has space",
        "id;rm",
    ],
)
def test_experiment_id_traversal_rejected(bad: str) -> None:
    with pytest.raises(ValidationError):
        validate_experiment_id(bad)


@pytest.mark.parametrize(
    "bad",
    ["../run", "a/b", "..", "", "bad id", "run..x"],
)
def test_run_id_and_export_stem_rejected(bad: str) -> None:
    with pytest.raises(ValidationError):
        validate_mc_run_id(bad)
    with pytest.raises(ValidationError):
        validate_export_stem(bad)


@pytest.mark.parametrize(
    "bad",
    [
        "../../../etc/passwd",
        "/etc/passwd",
        "ops/../SECRET.md",
        "..\\HELLO.md",
        "audit/NESTED.md",
    ],
)
def test_docs_path_traversal_rejected(bad: str) -> None:
    with pytest.raises(ValidationError):
        normalize_docs_relpath(bad)


def test_docs_api_traversal_http(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str) and isinstance(port, int)
    conn = http.client.HTTPConnection(host, port, timeout=5)
    conn.request("GET", "/api/docs/content?path=../../../etc/passwd")
    resp = conn.getresponse()
    body = json.loads(resp.read().decode("utf-8"))
    conn.close()
    assert resp.status == 400
    assert body["ok"] is False
    assert "traversal" in body["error"].lower() or "path" in body["error"].lower()


def test_report_id_traversal_http(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str) and isinstance(port, int)
    with pytest.raises(ApiError) as excinfo:
        handle_get_lab_report(state, "../etc/passwd")
    assert excinfo.value.status == 400

    conn = http.client.HTTPConnection(host, port, timeout=5)
    conn.request("GET", "/api/lab/reports/..%2F..%2Fetc%2Fpasswd")
    resp = conn.getresponse()
    body = json.loads(resp.read().decode("utf-8"))
    conn.close()
    assert resp.status == 400
    assert body["ok"] is False


def test_lab_run_id_dotdot_http(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str) and isinstance(port, int)
    for path in (
        "/api/lab/validation/..",
        "/api/lab/optimize/history/..%2Fevil",
        "/api/lab/montecarlo/history/%2e%2e",
        "/api/lab/exports/..%2Fsecret",
    ):
        conn = http.client.HTTPConnection(host, port, timeout=5)
        conn.request("GET", path)
        resp = conn.getresponse()
        body = json.loads(resp.read().decode("utf-8"))
        conn.close()
        assert resp.status == 400, path
        assert body["ok"] is False


# --- zip_path sandbox -------------------------------------------------------------


def test_zip_path_outside_sandbox_rejected(tmp_path: Path) -> None:
    parent = tmp_path / "sessions"
    session = WorkbenchSession.create_or_load(parent, "rt43")
    state = WorkbenchState(session=session)
    state.ensure_session()

    outside = tmp_path / "evil.zip"
    outside.write_bytes(b"PK\x05\x06" + b"\x00" * 18)

    with pytest.raises(ValidationError, match="sandbox|allowed_roots"):
        resolve_upload_archive(
            zip_path=str(outside),
            zip_base64=None,
            work_dir=tmp_path / "work",
            allowed_roots=(parent.resolve(),),
        )

    with pytest.raises(ApiError) as excinfo:
        handle_post_session_import(
            state,
            {"mode": "new", "session_id": "rt43b", "zip_path": str(outside)},
        )
    assert excinfo.value.status == 400
    assert "sandbox" in excinfo.value.message.lower() or "zip_path" in excinfo.value.message


def test_zip_path_requires_allowed_roots(tmp_path: Path) -> None:
    z = tmp_path / "x.zip"
    z.write_bytes(b"PK\x05\x06" + b"\x00" * 18)
    with pytest.raises(ValidationError, match="allowed_roots"):
        resolve_upload_archive(
            zip_path=str(z),
            zip_base64=None,
            work_dir=tmp_path / "w",
            allowed_roots=None,
        )


def test_zip_path_under_session_parent_ok(tmp_path: Path) -> None:
    parent = tmp_path / "sessions"
    parent.mkdir(parents=True)
    zips = parent / "_session_zips"
    zips.mkdir()
    archive = zips / "ok.zip"
    archive.write_bytes(b"PK\x05\x06" + b"\x00" * 18)
    resolved = resolve_upload_archive(
        zip_path=str(archive),
        zip_base64=None,
        work_dir=tmp_path / "w",
        allowed_roots=(parent.resolve(),),
    )
    assert resolved == archive.resolve()


# --- LIVE mode --------------------------------------------------------------------


def test_post_mode_live_rejected(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "s", "live43")
    state = WorkbenchState(session=session)
    with pytest.raises(ApiError) as excinfo:
        handle_post_mode(state, {"mode": "live"})
    assert excinfo.value.status == 400
    assert "LIVE" in excinfo.value.message or "live" in excinfo.value.message.lower()


def test_post_mode_live_http(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str) and isinstance(port, int)
    payload = json.dumps({"mode": "LIVE"}).encode("utf-8")
    conn = http.client.HTTPConnection(host, port, timeout=5)
    conn.request(
        "POST",
        "/api/mode",
        body=payload,
        headers={"Content-Type": "application/json", "Content-Length": str(len(payload))},
    )
    resp = conn.getresponse()
    body = json.loads(resp.read().decode("utf-8"))
    conn.close()
    assert resp.status == 400
    assert body["ok"] is False
    assert state.mode.value != "live"


def test_cli_mode_live_aborts() -> None:
    import io
    from contextlib import redirect_stderr

    err = io.StringIO()
    with redirect_stderr(err):
        code = main(["--mode", "live", "--no-browser"])
    assert code == 2
    assert "LIVE" in err.getvalue()


# --- Unbound host -----------------------------------------------------------------


def test_create_server_rejects_unbound_without_flag() -> None:
    with pytest.raises(ValidationError, match="loopback"):
        create_server(host="0.0.0.0", port=0, allow_non_loopback=False)


def test_create_server_allows_unbound_with_flag() -> None:
    server = create_server(host="0.0.0.0", port=0, allow_non_loopback=True)
    try:
        host, _port = server.server_address[:2]
        assert host in ("0.0.0.0", "::")
    finally:
        server.server_close()


def test_cli_unbound_without_flag_aborts() -> None:
    import io
    from contextlib import redirect_stderr

    err = io.StringIO()
    with redirect_stderr(err):
        code = main(["--host", "0.0.0.0", "--no-browser"])
    assert code == 2
    assert "loopback" in err.getvalue().lower() or "allow-non-loopback" in err.getvalue()


def test_is_loopback_host_matrix() -> None:
    assert is_loopback_host("127.0.0.1") is True
    assert is_loopback_host("0.0.0.0") is False
    assert is_loopback_host("192.168.0.1") is False


# --- Oversized body ---------------------------------------------------------------


def test_default_max_body_is_2mb() -> None:
    assert DEFAULT_MAX_BODY_BYTES == 2_000_000


def test_oversized_body_rejected_http(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str) and isinstance(port, int)
    # Content-Length over limit — server must reject before reading forever.
    too_big = DEFAULT_MAX_BODY_BYTES + 1
    conn = http.client.HTTPConnection(host, port, timeout=5)
    conn.putrequest("POST", "/api/mode")
    conn.putheader("Content-Type", "application/json")
    conn.putheader("Content-Length", str(too_big))
    conn.endheaders()
    # Send a tiny stub; handler should fail on length check.
    with contextlib.suppress(OSError):
        conn.send(b"{}")
    resp = conn.getresponse()
    body = json.loads(resp.read().decode("utf-8"))
    conn.close()
    assert resp.status == 400
    assert body["ok"] is False
    assert "grande" in body["error"].lower() or "body" in body["error"].lower()


# --- csv_path / experiment_id API -------------------------------------------------


def test_csv_path_traversal_rejected(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "s", "csv43")
    state = WorkbenchState(session=session)
    with pytest.raises(ApiError) as excinfo:
        handle_post_broker_connect(
            state,
            {"venue": "generic_csv", "csv_path": "../../../etc/passwd"},
        )
    assert excinfo.value.status == 400
    assert "traversal" in excinfo.value.message.lower()


def test_experiment_id_api_rejected(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "s", "exp43")
    state = WorkbenchState(session=session)
    with pytest.raises(ApiError) as excinfo:
        handle_post_lab_backtest(
            state,
            {"strategy_id": "momentum", "experiment_id": "../evil", "n_bars": 8},
        )
    assert excinfo.value.status == 400


def test_docs_content_handler_traversal(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "OK.md").write_text("# ok\n", encoding="utf-8")
    # Monkey via direct read with bad path (handler uses query).
    with pytest.raises(ValidationError):
        read_docs_content("../OK.md", docs_root=docs)
    # API wrapper
    session = WorkbenchSession.create_or_load(tmp_path / "sess", "doc43")
    state = WorkbenchState(session=session)
    # handle_get_docs_content uses real docs root; force via query only.
    with pytest.raises(ApiError) as excinfo:
        handle_get_docs_content(state, "path=../../pyproject.toml")
    assert excinfo.value.status == 400


def test_static_path_traversal_http(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str) and isinstance(port, int)
    conn = http.client.HTTPConnection(host, port, timeout=5)
    conn.request("GET", "/static/../../../etc/passwd")
    resp = conn.getresponse()
    raw = resp.read().decode("utf-8")
    conn.close()
    # 404 JSON error — no file leak
    assert resp.status in (400, 404)
    if resp.status == 404:
        body = json.loads(raw)
        assert body["ok"] is False


def test_lab_path_override_rejected(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "s", "path43")
    state = WorkbenchState(session=session)
    from quantlab.workbench.api import handle_post_lab_validation_run

    with pytest.raises(ApiError) as excinfo:
        handle_post_lab_validation_run(
            state,
            {"n_bars": 20, "path": "/etc/passwd"},
        )
    assert excinfo.value.status == 400
    assert "path" in excinfo.value.message.lower() or "sandbox" in excinfo.value.message.lower()
