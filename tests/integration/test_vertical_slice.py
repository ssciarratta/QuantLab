"""Vertical slice end-to-end."""

from pathlib import Path

from quantlab.core.types.enums import IntentType
from quantlab.vertical_slice.runner import run_vertical_slice


def test_vertical_slice_runs(project_root: Path) -> None:
    result = run_vertical_slice(project_root=project_root, environment="dev")
    assert result.instrument.instrument_id == "BTC-USDT-binance"
    assert result.dataset_manifest.dataset_id == "demo-btcusdt-1m"
    assert result.experiment_manifest.dataset_id == result.dataset_manifest.dataset_id
    assert result.experiment_manifest.seed == result.config.experiment.default_seed
    assert len(result.intents) == 1
    assert result.intents[0].intent_type is IntentType.PLACE_ORDER


def test_experiment_manifest_has_reproducibility_fields(project_root: Path) -> None:
    result = run_vertical_slice(project_root=project_root, environment="dev")
    manifest = result.experiment_manifest
    assert manifest.git_commit
    assert manifest.python_version
    assert manifest.dependency_versions_or_hash
    assert manifest.platform
    assert manifest.resolved_config["quantlab"]["environment"] == "dev"
