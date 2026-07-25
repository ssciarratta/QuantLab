"""Residuales post-hardening: zip-slip, ops metrics."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import assert_live_routing_blocked
from quantlab.infra.ops_metrics import get_ops_metrics
from quantlab.scale.backup import restore_backup
from quantlab.scale.batch import ParallelBatchRunner


def test_restore_blocks_zip_slip(tmp_path: Path) -> None:
    evil = tmp_path / "evil.zip"
    with zipfile.ZipFile(evil, "w") as zf:
        zf.writestr("../escape.txt", "pwned")
    dest = tmp_path / "out"
    with pytest.raises(ValidationError, match="zip-slip"):
        restore_backup(evil, dest)
    assert not (tmp_path / "escape.txt").exists()


def test_ops_metrics_live_gate_and_batch() -> None:
    metrics = get_ops_metrics()
    metrics.reset()
    before = metrics.get("live_gate.blocked")
    with pytest.raises(ValidationError, match="BLOQUEADO"):
        assert_live_routing_blocked()
    assert metrics.get("live_gate.blocked") == before + 1

    runner = ParallelBatchRunner(max_workers=2, chunk_size=2, strict=False)

    def boom(i: int) -> int:
        if i == 0:
            raise RuntimeError("x")
        return i

    report = runner.map_indexed(2, boom)
    assert report.failed == 1
    assert metrics.get("batch.failed_jobs") >= 1
