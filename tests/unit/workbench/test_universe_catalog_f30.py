"""Tests Universe Watchlist + Data Catalog browser (F30)."""

from __future__ import annotations

import http.client
import json
from datetime import UTC, datetime, timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.manifests import DatasetManifest, TimeRange
from quantlab.data.catalog import DataCatalog
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import (
    WorkbenchState,
    handle_get_catalog,
    handle_get_universe,
    handle_get_watchlist,
    handle_put_watchlist,
)
from quantlab.workbench.catalog_browser import list_catalog_datasets, resolve_catalog_path
from quantlab.workbench.session import WorkbenchSession
from quantlab.workbench.watchlist import (
    WATCHLIST_VERSION,
    add_symbols,
    empty_watchlist,
    load_watchlist,
    normalize_watchlist,
    remove_symbols,
    save_watchlist,
    validate_symbol,
)


def _manifest(*, dataset_id: str, instrument: str, storage_path: str) -> DatasetManifest:
    created = datetime.now(tz=UTC)
    return DatasetManifest(
        dataset_id=dataset_id,
        version="v1",
        source="test",
        instruments=(instrument,),
        time_range=TimeRange(start=created - timedelta(days=1), end=created),
        granularity="1d",
        schema_version="1.0",
        checksum="a" * 64,
        row_count=1,
        storage_path=storage_path,
        created_at=created,
    )


def test_live_blocked_still_true() -> None:
    assert LIVE_BLOCKED is True


def test_empty_watchlist_canonical() -> None:
    assert empty_watchlist() == {"version": WATCHLIST_VERSION, "symbols": []}


def test_validate_symbol_upper_and_reject() -> None:
    assert validate_symbol("ggal") == "GGAL"
    with pytest.raises(ValidationError, match="inválido"):
        validate_symbol("../x")
    with pytest.raises(ValidationError, match="inválido"):
        validate_symbol("bad sym")


def test_save_load_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "watchlist.json"
    saved = save_watchlist(path, {"version": 1, "symbols": ["ggal", "YPFD", "ggal"]})
    assert path.is_file()
    assert saved["symbols"] == ["GGAL", "YPFD"]
    assert load_watchlist(path) == saved


def test_load_missing_returns_empty(tmp_path: Path) -> None:
    assert load_watchlist(tmp_path / "nope.json") == empty_watchlist()


def test_add_remove_symbols() -> None:
    base = empty_watchlist()
    added = add_symbols(base, ["AAA", "bbb"])
    assert added["symbols"] == ["AAA", "BBB"]
    removed = remove_symbols(added, ["aaa"])
    assert removed["symbols"] == ["BBB"]


def test_normalize_rejects_bad_version() -> None:
    with pytest.raises(ValidationError, match="version"):
        normalize_watchlist({"version": 99, "symbols": []})


def test_session_watchlist_path(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "wl1")
    assert session.watchlist_path == session.root / "watchlist.json"
    assert "watchlist" in session.to_dict()


def test_api_handlers_put_get(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "api-wl")
    state = WorkbenchState(session=session)
    state.ensure_session()
    put = handle_put_watchlist(state, {"symbols": ["GGAL", "ALUA"]})
    assert put["ok"] is True
    assert put["live_blocked"] is True
    assert put["symbols"] == ["GGAL", "ALUA"]
    assert session.watchlist_path.is_file()

    got = handle_get_watchlist(state)
    assert got["symbols"] == ["GGAL", "ALUA"]

    add = handle_put_watchlist(state, {"add": ["YPFD"]})
    assert "YPFD" in add["symbols"]
    rem = handle_put_watchlist(state, {"remove": ["ALUA"]})
    assert rem["symbols"] == ["GGAL", "YPFD"]


def test_api_universe_without_broker(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "uni1")
    state = WorkbenchState(session=session)
    state.ensure_session()
    handle_put_watchlist(state, {"symbols": ["DEMO"]})
    uni = handle_get_universe(state)
    assert uni["ok"] is True
    assert uni["broker_connected"] is False
    assert uni["live_blocked"] is True
    assert any(s["symbol"] == "DEMO" and s["source"] == "watchlist" for s in uni["symbols"])


def test_catalog_missing_empty_ok(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("QUANTLAB_CATALOG_PATH", raising=False)
    assert resolve_catalog_path() is None
    payload = list_catalog_datasets()
    assert payload["available"] is False
    assert payload["datasets"] == []
    assert payload["ok"] is True
    assert payload["live_blocked"] is True
    assert payload["message"]


def test_catalog_lists_sqlite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("QUANTLAB_CATALOG_PATH", raising=False)
    db = tmp_path / "data" / "catalog" / "quantlab_catalog.sqlite"
    cat = DataCatalog(db)
    cat.register_dataset(
        _manifest(
            dataset_id="ds-demo-1",
            instrument="GGAL",
            storage_path=str(tmp_path / "bars.parquet"),
        ),
        kind="bars",
        provider="test",
    )

    resolved = resolve_catalog_path()
    assert resolved == db.resolve()
    payload = list_catalog_datasets()
    assert payload["available"] is True
    assert payload["backend"] == "sqlite"
    assert payload["count"] == 1
    assert payload["datasets"][0]["dataset_id"] == "ds-demo-1"
    assert payload["datasets"][0]["symbol"] == "GGAL"


def test_catalog_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "custom.sqlite"
    DataCatalog(db)  # creates empty catalog file
    monkeypatch.setenv("QUANTLAB_CATALOG_PATH", str(db))
    assert resolve_catalog_path() == db.resolve()
    payload = list_catalog_datasets()
    assert payload["available"] is True
    assert payload["catalog_path"] == str(db.resolve())


def test_api_catalog_handler(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("QUANTLAB_CATALOG_PATH", raising=False)
    session = WorkbenchSession.create_or_load(tmp_path, "cat-api")
    state = WorkbenchState(session=session)
    state.ensure_session()
    got = handle_get_catalog(state)
    assert got["ok"] is True
    assert got["available"] is False
    assert got["datasets"] == []
    assert got["session_id"] == "cat-api"


def test_http_watchlist_universe_catalog(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server, _state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("QUANTLAB_CATALOG_PATH", raising=False)

    body = json.dumps({"symbols": ["HTTP1", "HTTP2"]}).encode("utf-8")
    conn = http.client.HTTPConnection(host, port, timeout=5)
    try:
        conn.request(
            "PUT",
            "/api/watchlist",
            body=body,
            headers={"Content-Type": "application/json"},
        )
        resp = conn.getresponse()
        raw = resp.read()
        assert resp.status == 200
        put = json.loads(raw.decode("utf-8"))
        assert put["symbols"] == ["HTTP1", "HTTP2"]

        conn.request("GET", "/api/watchlist")
        resp = conn.getresponse()
        got = json.loads(resp.read().decode("utf-8"))
        assert resp.status == 200
        assert got["symbols"] == ["HTTP1", "HTTP2"]

        conn.request("GET", "/api/universe")
        resp = conn.getresponse()
        uni = json.loads(resp.read().decode("utf-8"))
        assert resp.status == 200
        assert uni["ok"] is True
        assert "HTTP1" in uni["watchlist"]

        conn.request("GET", "/api/catalog")
        resp = conn.getresponse()
        cat = json.loads(resp.read().decode("utf-8"))
        assert resp.status == 200
        assert cat["ok"] is True
        assert isinstance(cat["datasets"], list)
    finally:
        conn.close()


def test_static_panes_exist() -> None:
    root = Path(__file__).resolve().parents[3] / "src" / "quantlab" / "workbench" / "static"
    assert (root / "js" / "panes" / "universe.js").is_file()
    assert (root / "js" / "panes" / "catalog.js").is_file()
    index = (root / "index.html").read_text(encoding="utf-8")
    from static_test_helpers import assert_panel_registered

    assert_panel_registered("universe")
    assert_panel_registered("catalog")
