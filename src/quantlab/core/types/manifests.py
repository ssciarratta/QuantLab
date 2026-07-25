"""Manifests de dataset y experimento."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from quantlab.core.exceptions import ManifestError, ValidationError
from quantlab.core.types.enums import ExperimentStatus
from quantlab.core.types.serialization import dataclass_to_dict
from quantlab.core.types.validation import (
    freeze_mapping,
    require_aware,
    require_checksum,
    require_non_empty_str,
    require_schema_version,
)


@dataclass(frozen=True, slots=True)
class TimeRange:
    """Rango temporal de un dataset."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        require_aware(self.start, "start")
        require_aware(self.end, "end")
        if self.end <= self.start:
            raise ValidationError("time_range.end debe ser posterior a start")


@dataclass(frozen=True, slots=True)
class DatasetManifest:
    """Dataset versionado e inmutable."""

    dataset_id: str
    version: str
    source: str
    instruments: tuple[str, ...]
    time_range: TimeRange
    granularity: str
    schema_version: str
    checksum: str
    row_count: int
    storage_path: str
    created_at: datetime

    def __post_init__(self) -> None:
        require_non_empty_str(self.dataset_id, "dataset_id", error_cls=ManifestError)
        require_non_empty_str(self.version, "version", error_cls=ManifestError)
        require_non_empty_str(self.source, "source", error_cls=ManifestError)
        require_non_empty_str(self.granularity, "granularity", error_cls=ManifestError)
        require_non_empty_str(self.storage_path, "storage_path", error_cls=ManifestError)
        require_schema_version(self.schema_version)
        require_checksum(self.checksum)
        require_aware(self.created_at, "created_at")
        if self.row_count < 0:
            raise ManifestError("row_count no puede ser negativo")
        if not self.instruments:
            raise ManifestError("instruments no puede estar vacío")

    def to_dict(self) -> dict[str, Any]:
        return dataclass_to_dict(self)


@dataclass(frozen=True, slots=True)
class ExecutionModelVersions:
    """Versiones de políticas de ejecución registradas en el experimento."""

    fee_model: str
    slippage_model: str
    latency_model: str
    fill_model: str

    def __post_init__(self) -> None:
        for name in ("fee_model", "slippage_model", "latency_model", "fill_model"):
            require_non_empty_str(getattr(self, name), name, error_cls=ManifestError)


@dataclass(frozen=True, slots=True)
class ExperimentManifest:
    """Registro completo para reproducibilidad."""

    experiment_id: str
    dataset_id: str
    dataset_version: str
    resolved_config: Mapping[str, Any]
    seed: int
    git_commit: str
    python_version: str
    dependency_versions_or_hash: str
    platform: str
    strategy_version: str
    execution_model_versions: ExecutionModelVersions
    artifacts_produced: tuple[str, ...]
    created_at: datetime
    checksum: str
    status: ExperimentStatus = ExperimentStatus.DRAFT

    def __post_init__(self) -> None:
        require_non_empty_str(self.experiment_id, "experiment_id", error_cls=ManifestError)
        require_non_empty_str(self.dataset_id, "dataset_id", error_cls=ManifestError)
        require_non_empty_str(self.dataset_version, "dataset_version", error_cls=ManifestError)
        require_non_empty_str(self.git_commit, "git_commit", error_cls=ManifestError)
        require_non_empty_str(self.python_version, "python_version", error_cls=ManifestError)
        require_non_empty_str(
            self.dependency_versions_or_hash,
            "dependency_versions_or_hash",
            error_cls=ManifestError,
        )
        require_non_empty_str(self.platform, "platform", error_cls=ManifestError)
        require_non_empty_str(self.strategy_version, "strategy_version", error_cls=ManifestError)
        require_checksum(self.checksum)
        if self.seed < 0:
            raise ManifestError("seed no puede ser negativa")
        require_aware(self.created_at, "created_at")
        object.__setattr__(self, "resolved_config", freeze_mapping(self.resolved_config))

    def to_dict(self) -> dict[str, Any]:
        return dataclass_to_dict(self)
