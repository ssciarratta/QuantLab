"""Carga y merge de archivos YAML de configuración."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from quantlab.core.exceptions import ConfigError
from quantlab.infra.config.models import AppConfig


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Archivo de configuración no encontrado: {path}")
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(f"YAML inválido (se esperaba mapping): {path}")
    return data


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_yaml_files(*paths: Path) -> dict[str, Any]:
    """Carga y fusiona múltiples YAML en orden."""
    merged: dict[str, Any] = {}
    for path in paths:
        merged = _deep_merge(merged, _read_yaml(path))
    return merged


def resolve_config(config_dir: Path, environment: str | None = None) -> AppConfig:
    """Resuelve configuración base + entorno."""
    base_dir = config_dir / "base"
    env_dir = config_dir / "environments"

    files = [base_dir / "defaults.yaml"]
    if environment:
        env_file = env_dir / f"{environment}.yaml"
        if not env_file.exists():
            raise ConfigError(f"Entorno desconocido: {environment}")
        files.append(env_file)
    else:
        defaults = _read_yaml(base_dir / "defaults.yaml")
        env_name = defaults.get("quantlab", {}).get("environment", "dev")
        env_file = env_dir / f"{env_name}.yaml"
        if env_file.exists():
            files.append(env_file)

    raw = load_yaml_files(*files)
    try:
        return AppConfig.model_validate(raw)
    except Exception as exc:  # pydantic ValidationError
        raise ConfigError(f"Configuración inválida: {exc}") from exc


def validate_config(config: AppConfig) -> None:
    """Validación explícita de reglas de negocio de config."""
    if not config.quantlab.project_name.strip():
        raise ConfigError("quantlab.project_name no puede estar vacío")
    if config.experiment.default_seed < 0:
        raise ConfigError("experiment.default_seed debe ser >= 0")
