"""Tests de configuración."""

from pathlib import Path

import pytest

from quantlab.core.exceptions import ConfigError
from quantlab.infra.config import resolve_config, validate_config


def test_resolve_config_dev(config_dir: Path) -> None:
    config = resolve_config(config_dir, environment="dev")
    assert config.quantlab.environment == "dev"
    assert config.logging.level == "DEBUG"


def test_resolve_config_unknown_env(config_dir: Path) -> None:
    with pytest.raises(ConfigError):
        resolve_config(config_dir, environment="nonexistent")


def test_validate_config_rejects_empty_project_name(config_dir: Path) -> None:
    config = resolve_config(config_dir, environment="dev")
    bad = config.model_copy(
        update={
            "quantlab": config.quantlab.model_copy(update={"project_name": "  "}),
        }
    )
    with pytest.raises(ConfigError):
        validate_config(bad)
