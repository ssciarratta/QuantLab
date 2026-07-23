"""Configuration loader with Pydantic validation.

Single source of truth for all configuration.
Captures pydantic.ValidationError specifically, never bare Exception.
"""

from __future__ import annotations

import enum
from collections.abc import Mapping
from pathlib import Path

import yaml
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from quantlab.core.exceptions import ConfigurationError


class Environment(enum.StrEnum):
    DEV = "dev"
    RESEARCH = "research"
    PRODUCTION = "production"
    TEST = "test"


class LogLevel(enum.StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(enum.StrEnum):
    CONSOLE = "console"
    JSON = "json"


class LoggingConfig(BaseModel):
    """Logging configuration — single source of truth."""

    level: LogLevel = LogLevel.INFO
    format: LogFormat = LogFormat.CONSOLE


class QuantLabConfig(BaseModel):
    """Root configuration model with strict validation."""

    environment: Environment = Environment.DEV
    logging: LoggingConfig = LoggingConfig()
    project_root: str = "."

    model_config = {"extra": "forbid"}


def _deep_merge(base: dict[str, object], override: dict[str, object]) -> dict[str, object]:
    """Recursively merge override into base dict."""
    result: dict[str, object] = dict(base)
    for key, value in override.items():
        existing = result.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            result[key] = _deep_merge(existing, value)
        else:
            result[key] = value
    return result


def _load_yaml(path: Path) -> dict[str, object]:
    """Load a YAML file, returning empty dict for empty files."""
    if not path.exists():
        raise ConfigurationError(f"Configuration file not found: {path}")
    content = path.read_text(encoding="utf-8")
    if not content.strip():
        return {}
    parsed = yaml.safe_load(content)
    if parsed is None:
        return {}
    if not isinstance(parsed, dict):
        raise ConfigurationError(f"YAML root must be a mapping in {path}")
    return parsed


def load_config(
    config_dir: Path | str | None = None,
    environment: str | None = None,
    overrides: Mapping[str, object] | None = None,
) -> QuantLabConfig:
    """Load and validate QuantLab configuration.

    Merges base config with environment-specific overrides.
    Captures pydantic.ValidationError specifically.
    """
    base_data: dict[str, object] = {}

    if config_dir is not None:
        config_path = Path(config_dir)
        base_path = config_path / "base" / "defaults.yaml"
        if base_path.exists():
            base_data = _load_yaml(base_path)

        env_name = environment or base_data.get("environment", "dev")
        env_path = config_path / "environments" / f"{env_name}.yaml"
        if env_path.exists():
            env_data = _load_yaml(env_path)
            base_data = _deep_merge(base_data, env_data)

        logging_path = config_path / "base" / "logging.yaml"
        if logging_path.exists():
            logging_data = _load_yaml(logging_path)
            if "logging" in logging_data:
                existing_logging = base_data.get("logging", {})
                if isinstance(existing_logging, dict) and isinstance(
                    logging_data["logging"], dict
                ):
                    base_data["logging"] = _deep_merge(
                        existing_logging,
                        logging_data["logging"],
                    )
                else:
                    base_data["logging"] = logging_data["logging"]

    if environment is not None:
        base_data["environment"] = environment

    if overrides:
        base_data = _deep_merge(base_data, dict(overrides))

    try:
        return QuantLabConfig.model_validate(base_data)
    except PydanticValidationError as exc:
        raise ConfigurationError(f"Invalid configuration: {exc}") from exc
