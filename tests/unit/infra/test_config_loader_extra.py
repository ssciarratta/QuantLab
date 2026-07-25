"""Cobertura extra: bordes de infra/config/loader.py."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from quantlab.core.exceptions import ConfigError
from quantlab.infra.config.loader import (
    _deep_merge,
    _read_yaml,
    load_yaml_files,
    resolve_config,
    validate_config,
)
from quantlab.infra.config.models import AppConfig


def _write_yaml(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


def test_read_yaml_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="no encontrado"):
        _read_yaml(tmp_path / "nope.yaml")


def test_read_yaml_empty_file_returns_empty_dict(tmp_path: Path) -> None:
    path = tmp_path / "empty.yaml"
    path.write_text("", encoding="utf-8")
    assert _read_yaml(path) == {}


def test_read_yaml_rejects_non_mapping(tmp_path: Path) -> None:
    path = tmp_path / "list.yaml"
    path.write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="se esperaba mapping"):
        _read_yaml(path)


def test_deep_merge_nested_dicts() -> None:
    base = {"a": {"x": 1, "y": 2}, "b": 1}
    override = {"a": {"y": 9, "z": 3}, "c": 4}
    assert _deep_merge(base, override) == {"a": {"x": 1, "y": 9, "z": 3}, "b": 1, "c": 4}


def test_deep_merge_replaces_non_dict_values() -> None:
    base = {"a": {"x": 1}, "b": {"k": 1}}
    override = {"a": 99, "b": {"k": 2}}
    assert _deep_merge(base, override) == {"a": 99, "b": {"k": 2}}


def test_deep_merge_does_not_mutate_base() -> None:
    base: dict[str, Any] = {"a": {"x": 1}}
    override = {"a": {"y": 2}}
    merged = _deep_merge(base, override)
    assert base == {"a": {"x": 1}}
    assert merged == {"a": {"x": 1, "y": 2}}


def test_load_yaml_files_merges_in_order(tmp_path: Path) -> None:
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    _write_yaml(a, {"quantlab": {"project_name": "A", "environment": "dev"}, "x": 1})
    _write_yaml(b, {"quantlab": {"project_name": "B"}, "y": 2})
    merged = load_yaml_files(a, b)
    assert merged["quantlab"]["project_name"] == "B"
    assert merged["quantlab"]["environment"] == "dev"
    assert merged["x"] == 1
    assert merged["y"] == 2


def test_load_yaml_files_no_paths_returns_empty() -> None:
    assert load_yaml_files() == {}


def test_resolve_config_without_environment_uses_defaults_env(
    config_dir: Path,
) -> None:
    config = resolve_config(config_dir, environment=None)
    assert config.quantlab.environment == "dev"
    assert config.quantlab.project_name == "QuantLab"


def test_resolve_config_skips_missing_default_env_file(tmp_path: Path) -> None:
    base = tmp_path / "base"
    env = tmp_path / "environments"
    base.mkdir()
    env.mkdir()
    _write_yaml(
        base / "defaults.yaml",
        {
            "quantlab": {
                "environment": "ghost",
                "project_name": "SoloBase",
            }
        },
    )
    config = resolve_config(tmp_path, environment=None)
    assert config.quantlab.project_name == "SoloBase"
    assert config.quantlab.environment == "ghost"


def test_resolve_config_invalid_schema_raises(tmp_path: Path) -> None:
    base = tmp_path / "base"
    env = tmp_path / "environments"
    base.mkdir()
    env.mkdir()
    _write_yaml(
        base / "defaults.yaml",
        {"quantlab": {"project_name": "X"}, "unknown_section": {"a": 1}},
    )
    with pytest.raises(ConfigError, match="Configuración inválida"):
        resolve_config(tmp_path, environment=None)


def test_validate_config_rejects_negative_seed(config_dir: Path) -> None:
    config = resolve_config(config_dir, environment="dev")
    bad = config.model_copy(
        update={
            "experiment": config.experiment.model_copy(update={"default_seed": -1}),
        }
    )
    with pytest.raises(ConfigError, match="default_seed"):
        validate_config(bad)


def test_validate_config_accepts_valid(config_dir: Path) -> None:
    config = resolve_config(config_dir, environment="dev")
    validate_config(config)  # no raise


def test_validate_config_rejects_empty_project_name_on_plain_model() -> None:
    config = AppConfig()
    bad = config.model_copy(
        update={
            "quantlab": config.quantlab.model_copy(update={"project_name": ""}),
        }
    )
    with pytest.raises(ConfigError, match="project_name"):
        validate_config(bad)
