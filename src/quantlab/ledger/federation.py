"""Federación de índices de paper ledger (TD-03 research).

Compara mapas experiment_id → sha256 entre nodos/shards.
No implementa consenso distribuido ni HA; solo reconciliación offline.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DigestConflict:
    experiment_id: str
    local_sha256: str
    remote_sha256: str


@dataclass(frozen=True, slots=True)
class ReconcileReport:
    matched: tuple[str, ...]
    only_local: tuple[str, ...]
    only_remote: tuple[str, ...]
    conflicts: tuple[DigestConflict, ...]

    @property
    def ok(self) -> bool:
        return len(self.conflicts) == 0


def reconcile_indexes(
    local: Mapping[str, str],
    remote: Mapping[str, str],
) -> ReconcileReport:
    """Diff de índices de experimentos entre dos nodos."""
    matched: list[str] = []
    only_local: list[str] = []
    only_remote: list[str] = []
    conflicts: list[DigestConflict] = []

    local_ids = set(local)
    remote_ids = set(remote)

    for exp_id in sorted(local_ids & remote_ids):
        if local[exp_id] == remote[exp_id]:
            matched.append(exp_id)
        else:
            conflicts.append(
                DigestConflict(
                    experiment_id=exp_id,
                    local_sha256=local[exp_id],
                    remote_sha256=remote[exp_id],
                )
            )

    only_local.extend(sorted(local_ids - remote_ids))
    only_remote.extend(sorted(remote_ids - local_ids))

    return ReconcileReport(
        matched=tuple(matched),
        only_local=tuple(only_local),
        only_remote=tuple(only_remote),
        conflicts=tuple(conflicts),
    )
