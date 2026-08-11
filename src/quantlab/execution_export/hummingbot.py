"""Export de configuración hacia Hummingbot (Fase 16) — sin order routing LIVE."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.manifests import ExperimentManifest
from quantlab.core.types.validation import require_non_empty_str
from quantlab.data.atomic_io import atomic_write_text


@dataclass(frozen=True, slots=True)
class ValidationResult:
    ok: bool
    issues: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExecutionPackage:
    experiment_id: str
    strategy_version: str
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ExportResult:
    path: str
    checksum_note: str


class HummingbotExporter:
    """validate → build → export. LIVE routing permanece bloqueado."""

    LIVE_BLOCKED = True

    def validate_export(self, manifest: ExperimentManifest) -> ValidationResult:
        issues: list[str] = []
        try:
            require_non_empty_str(manifest.experiment_id, "experiment_id")
            require_non_empty_str(manifest.strategy_version, "strategy_version")
        except Exception as exc:  # noqa: BLE001
            issues.append(str(exc))
        if self.LIVE_BLOCKED:
            # No es error: documenta el gate
            pass
        return ValidationResult(ok=not issues, issues=tuple(issues))

    def build_execution_package(self, manifest: ExperimentManifest) -> ExecutionPackage:
        vr = self.validate_export(manifest)
        if not vr.ok:
            raise ValidationError("manifest inválido para export: " + "; ".join(vr.issues))
        payload = {
            "target": "hummingbot",
            "live_routing": False,
            "blocked": True,
            "environment": "testnet_spot_quantlab",
            "recommended_hb_connectors": {
                "spot_paper": "binance_paper_trade",
                "perp_testnet": "binance_perpetual_testnet",
                "quantlab_native_testnet": "binance_spot_testnet_via_quantlab_f102",
            },
            "experiment_id": manifest.experiment_id,
            "strategy_version": manifest.strategy_version,
            "dataset_id": manifest.dataset_id,
            "execution_models": {
                "fee": manifest.execution_model_versions.fee_model,
                "slippage": manifest.execution_model_versions.slippage_model,
                "latency": manifest.execution_model_versions.latency_model,
                "fill": manifest.execution_model_versions.fill_model,
            },
            "resolved_config": dict(manifest.resolved_config),
        }
        return ExecutionPackage(
            experiment_id=manifest.experiment_id,
            strategy_version=manifest.strategy_version,
            payload=payload,
        )

    def export_configuration(self, package: ExecutionPackage, target_path: Path) -> ExportResult:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        body = json.dumps(package.payload, indent=2, sort_keys=True) + "\n"
        atomic_write_text(target_path, body)
        return ExportResult(
            path=str(target_path),
            checksum_note="LIVE routing blocked by design (DEC gate)",
        )
