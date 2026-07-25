"""Cobertura extra: bordes de ExperimentRegistry."""

from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import ExperimentStatus
from quantlab.experiments.registry import ExperimentRegistry


def test_create_rejects_duplicate(tmp_path: Path) -> None:
    reg = ExperimentRegistry(tmp_path / "exp.sqlite")
    reg.create(experiment_id="e1", dataset_id="ds", strategy_version="v1")
    with pytest.raises(ValidationError, match="ya existe"):
        reg.create(experiment_id="e1", dataset_id="ds", strategy_version="v1")


def test_create_rejects_empty_ids(tmp_path: Path) -> None:
    reg = ExperimentRegistry(tmp_path / "exp.sqlite")
    with pytest.raises(ValidationError, match="experiment_id"):
        reg.create(experiment_id="  ", dataset_id="ds", strategy_version="v1")
    with pytest.raises(ValidationError, match="dataset_id"):
        reg.create(experiment_id="e1", dataset_id="", strategy_version="v1")
    with pytest.raises(ValidationError, match="strategy_version"):
        reg.create(experiment_id="e1", dataset_id="ds", strategy_version=" ")


def test_get_missing_returns_none(tmp_path: Path) -> None:
    reg = ExperimentRegistry(tmp_path / "exp.sqlite")
    assert reg.get("missing") is None


def test_list_filters_by_status(tmp_path: Path) -> None:
    reg = ExperimentRegistry(tmp_path / "exp.sqlite")
    reg.create(experiment_id="draft-1", dataset_id="ds", strategy_version="v1")
    reg.create(experiment_id="run-1", dataset_id="ds", strategy_version="v1")
    reg.set_status("run-1", ExperimentStatus.RUNNING)
    drafts = reg.list(status=ExperimentStatus.DRAFT)
    running = reg.list(status=ExperimentStatus.RUNNING)
    assert [r.experiment_id for r in drafts] == ["draft-1"]
    assert [r.experiment_id for r in running] == ["run-1"]
    assert len(reg.list()) == 2


def test_set_status_missing_raises(tmp_path: Path) -> None:
    reg = ExperimentRegistry(tmp_path / "exp.sqlite")
    with pytest.raises(ValidationError, match="no encontrado"):
        reg.set_status("ghost", ExperimentStatus.RUNNING)


def test_link_artifact_missing_and_empty_path(tmp_path: Path) -> None:
    reg = ExperimentRegistry(tmp_path / "exp.sqlite")
    with pytest.raises(ValidationError, match="no encontrado"):
        reg.link_artifact("ghost", "/tmp/a.json")
    reg.create(experiment_id="e1", dataset_id="ds", strategy_version="v1")
    with pytest.raises(ValidationError, match="path"):
        reg.link_artifact("e1", "  ")


def test_link_artifact_dedupes_paths(tmp_path: Path) -> None:
    reg = ExperimentRegistry(tmp_path / "exp.sqlite")
    reg.create(experiment_id="e1", dataset_id="ds", strategy_version="v1")
    reg.link_artifact("e1", "/a.json")
    updated = reg.link_artifact("e1", "/a.json")
    assert updated.artifact_paths == ("/a.json",)
    updated2 = reg.link_artifact("e1", "/b.json")
    assert updated2.artifact_paths == ("/a.json", "/b.json")


def test_create_batch_empty_returns_empty(tmp_path: Path) -> None:
    reg = ExperimentRegistry(tmp_path / "exp.sqlite")
    assert reg.create_batch([]) == []


def test_create_batch_rejects_duplicate_in_batch(tmp_path: Path) -> None:
    reg = ExperimentRegistry(tmp_path / "exp.sqlite")
    with pytest.raises(ValidationError, match="duplicado en batch"):
        reg.create_batch(
            [
                {"experiment_id": "same", "dataset_id": "d", "strategy_version": "v1"},
                {"experiment_id": "same", "dataset_id": "d", "strategy_version": "v1"},
            ]
        )


def test_create_batch_rejects_non_dict_metadata(tmp_path: Path) -> None:
    reg = ExperimentRegistry(tmp_path / "exp.sqlite")
    with pytest.raises(ValidationError, match="metadata debe ser dict"):
        reg.create_batch(
            [
                {
                    "experiment_id": "e1",
                    "dataset_id": "d",
                    "strategy_version": "v1",
                    "metadata": ["not", "a", "dict"],
                }
            ]
        )


def test_create_writes_sidecar(tmp_path: Path) -> None:
    reg = ExperimentRegistry(tmp_path / "exp.sqlite")
    reg.create(
        experiment_id="sidecar-1",
        dataset_id="ds",
        strategy_version="v1",
        metadata={"k": 1},
    )
    sidecar = tmp_path / "exp_records" / "sidecar-1.json"
    assert sidecar.is_file()
    text = sidecar.read_text(encoding="utf-8")
    assert "sidecar-1" in text
    assert '"k": 1' in text
