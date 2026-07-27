"""Tests watchlist import/export JSON (F79)."""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from quantlab import __version__
from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import (
    WorkbenchState,
    handle_get_watchlist_export,
    handle_post_watchlist_import,
    handle_put_watchlist,
)
from quantlab.workbench.server import make_handler
from quantlab.workbench.session import WorkbenchSession
from quantlab.workbench.watchlist import (
    export_watchlist_json,
    import_symbols,
    load_watchlist,
    parse_import_mode,
)


def _static_root() -> Path:
    return Path(__file__).resolve().parents[3] / "src" / "quantlab" / "workbench" / "static"


def test_live_blocked_and_version() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "1.00.0"
    assert PHASES_SUMMARY == "F19–F110 INTERNAL"
    assert not Path("docs/audit/FASE_79_APPROVED.md").exists()


def test_parse_import_mode_default_and_reject() -> None:
    assert parse_import_mode(None) == "merge"
    assert parse_import_mode("REPLACE") == "replace"
    with pytest.raises(ValidationError, match="merge"):
        parse_import_mode("upsert")


def test_import_symbols_merge_and_replace() -> None:
    base = {"version": 1, "symbols": ["GGAL"]}
    merged = import_symbols(base, ["ypfd", "GGAL"], mode="merge")
    assert merged["symbols"] == ["GGAL", "YPFD"]
    replaced = import_symbols(base, ["ALUA"], mode="replace")
    assert replaced["symbols"] == ["ALUA"]


def test_export_watchlist_json_canonical() -> None:
    text = export_watchlist_json({"version": 1, "symbols": ["ggal", "YPFD"]})
    data = json.loads(text)
    assert data == {"version": 1, "symbols": ["GGAL", "YPFD"]}
    assert text.endswith("\n")


def test_handle_export_and_import(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "wl79")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    state.ensure_session()
    handle_put_watchlist(state, {"symbols": ["GGAL"]})

    body, filename = handle_get_watchlist_export(state)
    assert filename.endswith(".json")
    assert "wl79" in filename
    payload = json.loads(body.decode("utf-8"))
    assert payload["symbols"] == ["GGAL"]

    merged = handle_post_watchlist_import(
        state, {"symbols": ["YPFD", "GGAL"], "mode": "merge"}
    )
    assert merged["ok"] is True
    assert merged["mode"] == "merge"
    assert merged["symbols"] == ["GGAL", "YPFD"]
    assert merged["live_blocked"] is True
    assert merged["before_count"] == 1
    assert merged["after_count"] == 2

    replaced = handle_post_watchlist_import(
        state, {"symbols": ["ALUA"], "mode": "replace"}
    )
    assert replaced["symbols"] == ["ALUA"]
    assert load_watchlist(session.watchlist_path)["symbols"] == ["ALUA"]


def test_import_via_watchlist_key(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "wl79b")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    state.ensure_session()
    handle_put_watchlist(state, {"symbols": ["AAA"]})
    out = handle_post_watchlist_import(
        state,
        {"watchlist": {"version": 1, "symbols": ["BBB"]}, "mode": "merge"},
    )
    assert out["symbols"] == ["AAA", "BBB"]


def test_import_rejects_bad_body(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "wl79bad")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    state.ensure_session()
    from quantlab.workbench.api import ApiError

    with pytest.raises(ApiError) as exc:
        handle_post_watchlist_import(state, {"mode": "merge"})
    assert exc.value.status == 400


def test_http_export_download(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "http79")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    state.ensure_session()
    handle_put_watchlist(state, {"symbols": ["DEMO"]})

    handler = make_handler(state)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = __import__("threading").Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        conn = http.client.HTTPConnection(str(host), int(port), timeout=30)
        conn.request("GET", "/api/watchlist/export")
        resp = conn.getresponse()
        raw = resp.read()
        headers = {k.lower(): v for k, v in resp.getheaders()}
        conn.close()
        assert resp.status == 200
        assert "application/json" in headers.get("content-type", "")
        assert "attachment" in headers.get("content-disposition", "")
        assert ".json" in headers.get("content-disposition", "")
        data = json.loads(raw.decode("utf-8"))
        assert data["symbols"] == ["DEMO"]

        conn2 = http.client.HTTPConnection(str(host), int(port), timeout=30)
        body = json.dumps({"symbols": ["X"], "mode": "replace"}).encode("utf-8")
        conn2.request(
            "POST",
            "/api/watchlist/import",
            body=body,
            headers={"Content-Type": "application/json"},
        )
        resp2 = conn2.getresponse()
        out = json.loads(resp2.read().decode("utf-8"))
        conn2.close()
        assert resp2.status == 200
        assert out["ok"] is True
        assert out["symbols"] == ["X"]
    finally:
        server.shutdown()


def test_static_universe_io_hooks() -> None:
    root = _static_root()
    universe = (root / "js" / "panes" / "universe.js").read_text(encoding="utf-8")
    api = (root / "js" / "api.js").read_text(encoding="utf-8")

    assert "watchlistExportUrl" in api
    assert "/api/watchlist/export" in api
    assert "/api/watchlist/import" in api
    assert "importWatchlist" in api
    assert "un-export" in universe
    assert "un-import" in universe
    assert "QLApi.watchlistExportUrl" in universe
    assert "QLApi.importWatchlist" in universe
    assert "merge" in universe
    assert "replace" in universe
