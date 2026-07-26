"""Tests experiment_id charset (F25 M1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.workbench import lab_services
from quantlab.workbench.lab_services import validate_experiment_id


@pytest.mark.parametrize(
    "eid",
    ["wb-lab-backtest", "a", "A1_b-2", "exp_01"],
)
def test_validate_experiment_id_ok(eid: str) -> None:
    assert validate_experiment_id(eid) == eid


@pytest.mark.parametrize(
    "eid",
    [
        "",
        "  ",
        "../escape",
        "a/b",
        "a\\b",
        "has.dot",
        "has space",
        "id!",
        "üñicode",
    ],
)
def test_validate_experiment_id_reject(eid: str) -> None:
    with pytest.raises(ValidationError, match="experiment_id inválido"):
        validate_experiment_id(eid)


def test_run_lab_backtest_rejects_bad_id() -> None:
    with pytest.raises(ValidationError, match="charset"):
        lab_services.run_lab_backtest(experiment_id="../evil")


def test_run_lab_export_hb_rejects_bad_id(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="charset"):
        lab_services.run_lab_export_hb(tmp_path, experiment_id="bad.id")


def test_run_lab_export_hb_accepts_safe_id(tmp_path: Path) -> None:
    result = lab_services.run_lab_export_hb(tmp_path, experiment_id="wb-hb-export")
    assert result["ok"] is True
    assert result["experiment_id"] == "wb-hb-export"
    assert (tmp_path / "wb-hb-export.json").is_file()
