"""Tests for configuration loading and validation."""

from __future__ import annotations

import pytest
import yaml

from quantlab.core.exceptions import ConfigurationError
from quantlab.infra.config import (
    Environment,
    LogFormat,
    LogLevel,
    load_config,
)


class TestLoadConfigDefaults:
    def test_default_config(self):
        config = load_config()
        assert config.environment == Environment.DEV
        assert config.logging.level == LogLevel.INFO
        assert config.logging.format == LogFormat.CONSOLE

    def test_override_environment(self):
        config = load_config(environment="research")
        assert config.environment == Environment.RESEARCH


class TestLoadConfigFromYaml:
    def test_load_from_yaml(self, tmp_path):
        base_dir = tmp_path / "base"
        base_dir.mkdir()
        (base_dir / "defaults.yaml").write_text(
            "environment: research\nlogging:\n  level: WARNING\n  format: json\n"
        )
        config = load_config(config_dir=tmp_path)
        assert config.environment == Environment.RESEARCH
        assert config.logging.level == LogLevel.WARNING

    def test_empty_yaml(self, tmp_path):
        base_dir = tmp_path / "base"
        base_dir.mkdir()
        (base_dir / "defaults.yaml").write_text("")
        config = load_config(config_dir=tmp_path)
        assert config.environment == Environment.DEV

    def test_yaml_with_only_comments(self, tmp_path):
        base_dir = tmp_path / "base"
        base_dir.mkdir()
        (base_dir / "defaults.yaml").write_text("# just a comment\n")
        config = load_config(config_dir=tmp_path)
        assert config.environment == Environment.DEV

    def test_malformed_yaml(self, tmp_path):
        base_dir = tmp_path / "base"
        base_dir.mkdir()
        (base_dir / "defaults.yaml").write_text("[invalid: yaml: {broken")
        with pytest.raises((yaml.YAMLError, ConfigurationError)):
            load_config(config_dir=tmp_path)


class TestLoadConfigEnvironmentOverride:
    def test_env_override(self, tmp_path):
        base_dir = tmp_path / "base"
        base_dir.mkdir()
        (base_dir / "defaults.yaml").write_text(
            "environment: dev\nlogging:\n  level: INFO\n  format: console\n"
        )
        env_dir = tmp_path / "environments"
        env_dir.mkdir()
        (env_dir / "research.yaml").write_text("logging:\n  level: DEBUG\n")
        config = load_config(config_dir=tmp_path, environment="research")
        assert config.logging.level == LogLevel.DEBUG
        assert config.logging.format == LogFormat.CONSOLE


class TestDeepMerge:
    def test_deep_merge_preserves_base(self, tmp_path):
        base_dir = tmp_path / "base"
        base_dir.mkdir()
        (base_dir / "defaults.yaml").write_text(
            "environment: dev\nlogging:\n  level: INFO\n  format: json\n"
        )
        env_dir = tmp_path / "environments"
        env_dir.mkdir()
        (env_dir / "dev.yaml").write_text("logging:\n  level: DEBUG\n")
        config = load_config(config_dir=tmp_path, environment="dev")
        assert config.logging.level == LogLevel.DEBUG
        assert config.logging.format == LogFormat.JSON


class TestConfigValidation:
    def test_unknown_environment_rejected(self):
        with pytest.raises(ConfigurationError, match="Invalid"):
            load_config(environment="staging")

    def test_invalid_log_level(self, tmp_path):
        base_dir = tmp_path / "base"
        base_dir.mkdir()
        (base_dir / "defaults.yaml").write_text("logging:\n  level: TRACE\n")
        with pytest.raises(ConfigurationError, match="Invalid"):
            load_config(config_dir=tmp_path)

    def test_invalid_log_format(self, tmp_path):
        base_dir = tmp_path / "base"
        base_dir.mkdir()
        (base_dir / "defaults.yaml").write_text("logging:\n  format: xml\n")
        with pytest.raises(ConfigurationError, match="Invalid"):
            load_config(config_dir=tmp_path)

    def test_extra_fields_rejected(self, tmp_path):
        base_dir = tmp_path / "base"
        base_dir.mkdir()
        (base_dir / "defaults.yaml").write_text("unknown_field: value\n")
        with pytest.raises(ConfigurationError, match="Invalid"):
            load_config(config_dir=tmp_path)


class TestLoggingYamlIntegration:
    def test_logging_yaml_merged(self, tmp_path):
        base_dir = tmp_path / "base"
        base_dir.mkdir()
        (base_dir / "defaults.yaml").write_text("logging:\n  level: INFO\n  format: console\n")
        (base_dir / "logging.yaml").write_text("logging:\n  format: json\n")
        config = load_config(config_dir=tmp_path)
        assert config.logging.format == LogFormat.JSON
        assert config.logging.level == LogLevel.INFO
