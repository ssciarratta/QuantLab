"""Cobertura extra: bordes de ParquetProcessedStore."""

from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.data.storage.parquet_store import ParquetProcessedStore


def test_write_rows_empty_raises(tmp_path: Path) -> None:
    store = ParquetProcessedStore(tmp_path / "processed")
    with pytest.raises(ValidationError, match="rows vacío"):
        store.write_rows(
            dataset_id="ds",
            schema_version="1.0",
            symbol="X",
            timeframe="1m",
            rows=[],
        )


def test_write_rows_inconsistent_columns_raises(tmp_path: Path) -> None:
    store = ParquetProcessedStore(tmp_path / "processed")
    with pytest.raises(ValidationError, match="columnas inconsistentes"):
        store.write_rows(
            dataset_id="ds",
            schema_version="1.0",
            symbol="X",
            timeframe="1m",
            rows=[
                {"a": "1", "b": "2"},
                {"a": "3", "c": "4"},
            ],
        )


def test_write_rows_already_exists_raises(tmp_path: Path) -> None:
    store = ParquetProcessedStore(tmp_path / "processed")
    kwargs = {
        "dataset_id": "ds",
        "schema_version": "1.0",
        "symbol": "X",
        "timeframe": "1m",
        "rows": [{"ts": "1", "close": "100"}],
    }
    first = store.write_rows(**kwargs)
    assert Path(first.path).is_file()
    with pytest.raises(ValidationError, match="ya existe"):
        store.write_rows(**kwargs)


def test_read_rows_missing_file_raises(tmp_path: Path) -> None:
    store = ParquetProcessedStore(tmp_path / "processed")
    missing = tmp_path / "nope.parquet"
    with pytest.raises(ValidationError, match="inexistente"):
        store.read_rows(missing)


def test_write_rows_timeframe_none_uses_none_dir(tmp_path: Path) -> None:
    store = ParquetProcessedStore(tmp_path / "processed")
    result = store.write_rows(
        dataset_id="ds",
        schema_version="1.0",
        symbol="Y",
        timeframe=None,
        rows=[{"x": "1"}],
    )
    assert Path(result.path).parts[-2] == "none"
    assert result.rows == 1
    loaded = store.read_rows(Path(result.path))
    assert loaded == [{"x": "1"}]
