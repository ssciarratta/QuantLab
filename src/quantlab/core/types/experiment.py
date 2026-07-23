"""Experiment manifest with deep immutability and validated invariants."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType

from quantlab.core.types.json_types import JsonValue, freeze_json
from quantlab.core.types.market import _require_non_empty, _require_tz_aware


@dataclass(frozen=True)
class ExperimentManifest:
    """Manifest describing an experiment for reproducibility.

    All mutable-looking fields are deeply frozen on construction.
    """

    experiment_id: str
    version: str
    timestamp: datetime
    checksum: str
    instruments: tuple[str, ...]
    seed: int
    commit: str
    lockfile_hash: str
    resolved_config: MappingProxyType[str, JsonValue] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        _require_non_empty(self.experiment_id, "experiment_id")
        _require_non_empty(self.version, "version")
        _require_tz_aware(self.timestamp, "timestamp")
        _require_non_empty(self.checksum, "checksum")
        if not self.instruments:
            raise ValueError("instruments must not be empty")
        for inst in self.instruments:
            _require_non_empty(inst, "instrument")
        _require_non_empty(self.commit, "commit")
        _require_non_empty(self.lockfile_hash, "lockfile_hash")
        if not isinstance(self.resolved_config, MappingProxyType):
            object.__setattr__(
                self,
                "resolved_config",
                freeze_json(self.resolved_config),
            )
        if not isinstance(self.instruments, tuple):
            object.__setattr__(self, "instruments", tuple(self.instruments))

    @classmethod
    def create(
        cls,
        *,
        experiment_id: str,
        version: str,
        timestamp: datetime,
        checksum: str,
        instruments: list[str] | tuple[str, ...],
        seed: int,
        commit: str,
        lockfile_hash: str,
        resolved_config: dict[str, object] | None = None,
    ) -> ExperimentManifest:
        frozen_config: MappingProxyType[str, JsonValue] = (
            MappingProxyType({str(k): freeze_json(v) for k, v in resolved_config.items()})
            if resolved_config
            else MappingProxyType({})
        )
        return cls(
            experiment_id=experiment_id,
            version=version,
            timestamp=timestamp,
            checksum=checksum,
            instruments=tuple(instruments),
            seed=seed,
            commit=commit,
            lockfile_hash=lockfile_hash,
            resolved_config=frozen_config,
        )
