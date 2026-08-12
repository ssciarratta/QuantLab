"""Tests Docs / Help Browser (F38) — list + content + path traversal fail-closed."""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import quote

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import (
    ApiError,
    WorkbenchState,
    handle_get_docs,
    handle_get_docs_content,
)
from quantlab.workbench.chat.tools import ToolRegistry
from quantlab.workbench.docs_browser import (
    list_docs,
    markdown_to_simple_html,
    normalize_docs_relpath,
    read_docs_content,
    resolve_docs_file,
    search_docs_files,
)
from quantlab.workbench.server import create_server
from quantlab.workbench.session import WorkbenchSession


def _addr(server: ThreadingHTTPServer) -> tuple[str, int]:
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    return host, port


def _get(server: ThreadingHTTPServer, path: str) -> tuple[int, dict[str, Any] | str]:
    host, port = _addr(server)
    conn = http.client.HTTPConnection(host, port, timeout=30)
    conn.request("GET", path)
    resp = conn.getresponse()
    raw = resp.read().decode("utf-8")
    conn.close()
    ctype = resp.getheader("Content-Type") or ""
    if "json" in ctype or raw.startswith("{"):
        return resp.status, json.loads(raw)
    return resp.status, raw


@pytest.fixture
def docs_tree(tmp_path: Path) -> Path:
    root = tmp_path / "docs"
    root.mkdir()
    (root / "HELLO.md").write_text("# Hello\n\nLIVE_BLOCKED workbench\n", encoding="utf-8")
    ops = root / "ops"
    ops.mkdir()
    (ops / "RUN.md").write_text("# Runbook\n\n- step one\n", encoding="utf-8")
    manuals = root / "manuales"
    manuals.mkdir()
    (manuals / "00-INDICE.md").write_text("# Indice\n\nmanuales\n", encoding="utf-8")
    mc = root / "montecarlo"
    mc.mkdir()
    (mc / "montecarlo-guide.md").write_text("# MC\n\nguide\n", encoding="utf-8")
    scanner = root / "scanner"
    scanner.mkdir()
    (scanner / "alpha-scanner-guide.md").write_text("# Scanner\n\nguide\n", encoding="utf-8")
    (root / "secret.txt").write_text("nope", encoding="utf-8")
    nested = root / "audit"
    nested.mkdir()
    (nested / "NESTED.md").write_text("# Nested should not list\n", encoding="utf-8")
    return root


def test_live_blocked_still_true() -> None:
    assert LIVE_BLOCKED is True


def test_list_docs_allowlisted_subdirs(docs_tree: Path) -> None:
    payload = list_docs(docs_root=docs_tree)
    assert payload["ok"] is True
    assert payload["live_blocked"] is True
    assert payload["live_routing"] is False
    assert set(payload["allowed_subdirs"]) == {
        "manuales",
        "montecarlo",
        "ops",
        "scanner",
    }
    paths = {d["path"] for d in payload["docs"]}
    assert paths == {
        "HELLO.md",
        "ops/RUN.md",
        "manuales/00-INDICE.md",
        "montecarlo/montecarlo-guide.md",
        "scanner/alpha-scanner-guide.md",
    }
    assert "secret.txt" not in paths
    assert "audit/NESTED.md" not in paths


def test_read_content_ok(docs_tree: Path) -> None:
    body = read_docs_content("HELLO.md", docs_root=docs_tree)
    assert body["ok"] is True
    assert body["path"] == "HELLO.md"
    assert "LIVE_BLOCKED" in body["content"]
    assert "<h1>" in body["html"]
    assert "&lt;" not in body["html"] or "Hello" in body["html"]

    ops = read_docs_content("ops/RUN.md", docs_root=docs_tree)
    assert ops["path"] == "ops/RUN.md"
    assert ops["subdir"] == "ops"


@pytest.mark.parametrize(
    "bad",
    [
        "../HELLO.md",
        "../../etc/passwd",
        "/etc/passwd",
        "ops/../HELLO.md",
        "ops/../../HELLO.md",
        "audit/NESTED.md",
        "secret.txt",
        "..\\HELLO.md",
        "ops/../../docs_browser.py",
        "",
        "ops/",
        ".env",
        "ops/.hidden.md",
    ],
)
def test_path_traversal_fail_closed(docs_tree: Path, bad: str) -> None:
    with pytest.raises(ValidationError):
        normalize_docs_relpath(bad)
    with pytest.raises(ValidationError):
        resolve_docs_file(bad, docs_root=docs_tree)
    with pytest.raises(ValidationError):
        read_docs_content(bad, docs_root=docs_tree)


def test_symlink_escape_rejected(docs_tree: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside.md"
    outside.write_text("# Outside\n", encoding="utf-8")
    link = docs_tree / "LINK.md"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlink no soportado")
    # Si el symlink resuelve fuera de docs/, fail-closed.
    with pytest.raises(ValidationError):
        resolve_docs_file("LINK.md", docs_root=docs_tree)


def test_markdown_escape_html() -> None:
    html = markdown_to_simple_html("# Title\n\n<script>alert(1)</script>\n")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "<h1>Title</h1>" in html


def test_search_docs_includes_ops(docs_tree: Path) -> None:
    out = search_docs_files("runbook", docs_root=docs_tree)
    assert out["query"] == "runbook"
    assert any(m["path"] == "ops/RUN.md" for m in out["matches"])


def test_chat_search_docs_uses_browser(docs_tree: Path) -> None:
    reg = ToolRegistry(WorkbenchState(), docs_root=docs_tree)
    out = reg.call("search_docs", {"query": "LIVE_BLOCKED"})
    assert any(m["file"] == "HELLO.md" for m in out["matches"])


def test_api_handlers(tmp_path: Path, docs_tree: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "quantlab.workbench.api.list_docs",
        lambda: list_docs(docs_root=docs_tree),
    )
    monkeypatch.setattr(
        "quantlab.workbench.api.read_docs_content",
        lambda path: read_docs_content(path, docs_root=docs_tree),
    )
    session = WorkbenchSession.create_or_load(tmp_path, "docs38")
    state = WorkbenchState(session=session)
    listed = handle_get_docs(state)
    assert listed["ok"] is True
    assert listed["count"] >= 2
    assert listed["live_blocked"] is True

    content = handle_get_docs_content(state, "path=HELLO.md")
    assert content["path"] == "HELLO.md"

    with pytest.raises(ApiError) as exc:
        handle_get_docs_content(state, "path=../etc/passwd")
    assert exc.value.status == 400

    with pytest.raises(ApiError) as exc2:
        handle_get_docs_content(state, "")
    assert exc2.value.status == 400


def test_http_docs_endpoints(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "http38")
    state = WorkbenchState(session=session)
    server = create_server(host="127.0.0.1", port=0, state=state)
    thread_server = server
    try:
        import threading

        t = threading.Thread(target=thread_server.serve_forever, daemon=True)
        t.start()
        status, body = _get(thread_server, "/api/docs")
        assert status == 200
        assert isinstance(body, dict)
        assert body["ok"] is True
        assert body["live_blocked"] is True
        assert body["count"] >= 1
        paths = {d["path"] for d in body["docs"]}
        assert any(p.endswith(".md") for p in paths)
        # al menos algún ops/
        sample = next(iter(paths))
        st2, body2 = _get(thread_server, "/api/docs/content?path=" + quote(sample))
        assert st2 == 200
        assert isinstance(body2, dict)
        assert body2["ok"] is True
        assert "content" in body2

        st3, body3 = _get(thread_server, "/api/docs/content?path=" + quote("../pyproject.toml"))
        assert st3 == 400
        assert isinstance(body3, dict)
        assert body3["ok"] is False

        st4, body4 = _get(
            thread_server, "/api/docs/content?path=" + quote("audit/INTERNAL_AUDIT_F37.md")
        )
        assert st4 == 400
        assert isinstance(body4, dict)
        assert body4["ok"] is False
    finally:
        thread_server.shutdown()
        thread_server.server_close()


def test_static_docs_pane_present() -> None:
    root = Path(__file__).resolve().parents[3]
    index = root / "src/quantlab/workbench/static/index.html"
    docs_js = root / "src/quantlab/workbench/static/js/panes/docs.js"
    assert index.is_file()
    text = index.read_text(encoding="utf-8")
    from static_test_helpers import assert_panel_registered

    assert_panel_registered("docs")
    assert "panes/docs.js" in text
    assert docs_js.is_file()
    js = docs_js.read_text(encoding="utf-8")
    assert "QLApi.docsList" in js
    assert "QLApi.docsContent" in js
