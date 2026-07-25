"""Cobertura extra: DuckDBCatalogBackend + DataCatalog (filtros, find_latest, verify)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import duckdb

from quantlab.core.types.manifests import DatasetManifest, TimeRange
from quantlab.data.catalog import DataCatalog, DuckDBCatalogBackend


def _manifest(
    *,
    dataset_id: str,
    instrument: str,
    granularity: str,
    storage_path: str,
    created_at: datetime,
    checksum: str = "a" * 64,
) -> DatasetManifest:
    return DatasetManifest(
        dataset_id=dataset_id,
        version="v1",
        source="test",
        instruments=(instrument,),
        time_range=TimeRange(
            start=created_at - timedelta(hours=1),
            end=created_at,
        ),
        granularity=granularity,
        schema_version="1.0",
        checksum=checksum,
        row_count=1,
        storage_path=storage_path,
        created_at=created_at,
    )


def test_list_datasets_filters(tmp_path: Path) -> None:
    backend = DuckDBCatalogBackend(tmp_path / "cat.duckdb")
    cat = DataCatalog(tmp_path / "unused.sqlite", backend=backend)
    t0 = datetime(2024, 1, 1, tzinfo=UTC)
    t1 = datetime(2024, 1, 2, tzinfo=UTC)
    cat.register_dataset(
        _manifest(
            dataset_id="ds-a",
            instrument="SYM_A",
            granularity="1m",
            storage_path=str(tmp_path / "a.bin"),
            created_at=t0,
        ),
        kind="bars",
        provider="prov_a",
    )
    cat.register_dataset(
        _manifest(
            dataset_id="ds-b",
            instrument="SYM_B",
            granularity="5m",
            storage_path=str(tmp_path / "b.bin"),
            created_at=t1,
        ),
        kind="trades",
        provider="prov_b",
    )

    assert len(cat.list_datasets()) == 2
    by_provider = cat.list_datasets(provider="prov_a")
    assert len(by_provider) == 1
    assert by_provider[0].dataset_id == "ds-a"

    by_kind = cat.list_datasets(kind="trades")
    assert len(by_kind) == 1
    assert by_kind[0].dataset_id == "ds-b"

    by_symbol = cat.list_datasets(symbol="SYM_A")
    assert len(by_symbol) == 1
    assert by_symbol[0].dataset_id == "ds-a"

    combined = cat.list_datasets(provider="prov_b", kind="trades", symbol="SYM_B")
    assert len(combined) == 1
    assert combined[0].dataset_id == "ds-b"

    assert cat.list_datasets(provider="missing") == []


def test_find_latest(tmp_path: Path) -> None:
    backend = DuckDBCatalogBackend(tmp_path / "cat.duckdb")
    cat = DataCatalog(tmp_path / "unused.sqlite", backend=backend)
    older = datetime(2024, 6, 1, tzinfo=UTC)
    newer = datetime(2024, 6, 2, tzinfo=UTC)
    cat.register_dataset(
        _manifest(
            dataset_id="ds-old",
            instrument="X",
            granularity="1m",
            storage_path=str(tmp_path / "old.bin"),
            created_at=older,
        ),
        kind="bars",
        provider="csv",
    )
    cat.register_dataset(
        _manifest(
            dataset_id="ds-new",
            instrument="X",
            granularity="1m",
            storage_path=str(tmp_path / "new.bin"),
            created_at=newer,
        ),
        kind="bars",
        provider="csv",
    )

    latest = cat.find_latest(provider="csv", symbol="X", timeframe="1m")
    assert latest is not None
    assert latest.dataset_id == "ds-new"
    assert cat.find_latest(provider="csv", symbol="Y", timeframe="1m") is None


def test_verify_missing_file(tmp_path: Path) -> None:
    backend = DuckDBCatalogBackend(tmp_path / "cat.duckdb")
    cat = DataCatalog(tmp_path / "unused.sqlite", backend=backend)
    missing = tmp_path / "does_not_exist.bin"
    cat.register_dataset(
        _manifest(
            dataset_id="ds-miss",
            instrument="X",
            granularity="1m",
            storage_path=str(missing),
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
        ),
        kind="bars",
        provider="p",
    )
    assert missing.exists() is False
    assert cat.verify_dataset("ds-miss") is False
    assert cat.verify_dataset("no-such-id") is False


def test_verify_bad_checksum_format(tmp_path: Path) -> None:
    db_path = tmp_path / "cat.duckdb"
    backend = DuckDBCatalogBackend(db_path)
    cat = DataCatalog(tmp_path / "unused.sqlite", backend=backend)
    data = tmp_path / "ok.bin"
    data.write_bytes(b"payload")
    cat.register_dataset(
        _manifest(
            dataset_id="ds-bad-ck",
            instrument="X",
            granularity="1m",
            storage_path=str(data),
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
        ),
        kind="bars",
        provider="p",
    )
    entry = cat.get_dataset("ds-bad-ck")
    assert entry is not None
    corrupted = dict(entry.manifest)
    corrupted["checksum"] = "not-a-valid-sha256"
    con = duckdb.connect(database=str(db_path))
    try:
        con.execute(
            "UPDATE datasets SET manifest_json = ? WHERE dataset_id = ?",
            [json.dumps(corrupted, ensure_ascii=False, sort_keys=True), "ds-bad-ck"],
        )
    finally:
        con.close()

    assert cat.verify_dataset("ds-bad-ck") is False
