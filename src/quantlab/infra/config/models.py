"""Modelos de configuración validados."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class LoggingConfig(BaseModel):
    """Configuración de logging."""

    level: str = "INFO"
    format: str = "console"
    json_output: bool = False

    @field_validator("level")
    @classmethod
    def level_upper(cls, value: str) -> str:
        return value.upper()


class ExperimentConfig(BaseModel):
    """Defaults de experimentos."""

    default_seed: int = 42
    strategy_version: str = "0.0.0-dummy"


class QuantLabConfig(BaseModel):
    """Sección principal quantlab."""

    environment: str = "dev"
    project_name: str = "QuantLab"
    data_root: str = "data"
    reports_root: str = "reports"


class AppConfig(BaseModel):
    """Configuración raíz resuelta de QuantLab."""

    quantlab: QuantLabConfig = Field(default_factory=QuantLabConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    experiment: ExperimentConfig = Field(default_factory=ExperimentConfig)

    model_config = {"extra": "forbid"}
