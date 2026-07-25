"""Cobertura extra: bordes de data/atomic_io.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from quantlab.data.atomic_io import atomic_write_bytes, atomic_write_text


def test_atomic_write_bytes_creates_parent_dirs(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "dir" / "out.bin"
    atomic_write_bytes(target, b"abc")
    assert target.read_bytes() == b"abc"


def test_atomic_write_bytes_overwrites_existing(tmp_path: Path) -> None:
    target = tmp_path / "file.bin"
    target.write_bytes(b"old")
    atomic_write_bytes(target, b"new-content")
    assert target.read_bytes() == b"new-content"


def test_atomic_write_bytes_empty_payload(tmp_path: Path) -> None:
    target = tmp_path / "empty.bin"
    atomic_write_bytes(target, b"")
    assert target.read_bytes() == b""
    assert target.exists()


def test_atomic_write_bytes_leaves_no_tmp_on_success(tmp_path: Path) -> None:
    target = tmp_path / "clean.bin"
    atomic_write_bytes(target, b"ok")
    leftovers = list(tmp_path.glob(".clean.bin.*.tmp"))
    assert leftovers == []


def test_atomic_write_bytes_cleans_tmp_on_failure(tmp_path: Path) -> None:
    target = tmp_path / "fail.bin"

    def boom(*_args: object, **_kwargs: object) -> None:
        raise OSError("disk full")

    with (
        patch("quantlab.data.atomic_io.os.fsync", side_effect=boom),
        pytest.raises(OSError, match="disk full"),
    ):
        atomic_write_bytes(target, b"partial")

    assert not target.exists()
    leftovers = list(tmp_path.glob(".fail.bin.*.tmp"))
    assert leftovers == []


def test_atomic_write_text_utf8_default(tmp_path: Path) -> None:
    target = tmp_path / "t.txt"
    atomic_write_text(target, "café — ñ")
    assert target.read_text(encoding="utf-8") == "café — ñ"


def test_atomic_write_text_custom_encoding(tmp_path: Path) -> None:
    target = tmp_path / "latin.txt"
    atomic_write_text(target, "áéí", encoding="latin-1")
    assert target.read_bytes() == "áéí".encode("latin-1")


def test_atomic_write_text_overwrites(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"
    atomic_write_text(target, "v1")
    atomic_write_text(target, "v2")
    assert target.read_text(encoding="utf-8") == "v2"
