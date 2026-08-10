"""Manifiesto versionado de promoción estrategia → ejecución."""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.execution.strategy_execution.destinations import (
    ExecutionDestination,
    MarketDataSource,
)
from quantlab.workbench.strategy_catalog import normalize_strategy_id


def _canonical_json(data: Mapping[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def _hash_payload(data: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(data).encode("utf-8")).hexdigest()


@dataclass
class StrategyPromotionManifest:
    promotion_id: str
    created_at: str
    source_module: str
    strategy_id: str
    strategy_name: str
    strategy_version: str
    strategy_parameters: dict[str, Any]
    parameter_schema_version: str
    symbol: str
    market_type: str
    execution_destination: ExecutionDestination
    market_data_source: MarketDataSource
    testnet_only: bool = True
    production_blocked: bool = True
    scan_id: str | None = None
    simulation_id: str | None = None
    monte_carlo_id: str | None = None
    experiment_id: str | None = None
    session_id: str | None = None
    capital: str | None = None
    leverage: str | None = None
    historical_metrics: dict[str, Any] = field(default_factory=dict)
    monte_carlo_metrics: dict[str, Any] = field(default_factory=dict)
    source_hash: str = ""
    configuration_hash: str = ""

    def __post_init__(self) -> None:
        self.strategy_id = normalize_strategy_id(self.strategy_id)
        if not self.symbol.strip():
            raise ValidationError("symbol requerido en manifiesto")
        if not self.testnet_only or not self.production_blocked:
            raise ValidationError("manifiesto debe ser testnet_only y production_blocked")
        if self.execution_destination not in ExecutionDestination:
            raise ValidationError(f"execution_destination inválido: {self.execution_destination}")
        body = self._body_for_hash()
        if not self.source_hash:
            self.source_hash = _hash_payload(
                {k: v for k, v in body.items() if k not in {"configuration_hash", "source_hash"}}
            )
        if not self.configuration_hash:
            self.configuration_hash = _hash_payload(body)

    def _body_for_hash(self) -> dict[str, Any]:
        return {
            "promotion_id": self.promotion_id,
            "source_module": self.source_module,
            "strategy_id": self.strategy_id,
            "strategy_parameters": self.strategy_parameters,
            "symbol": self.symbol,
            "market_type": self.market_type,
            "execution_destination": self.execution_destination.value,
            "market_data_source": self.market_data_source.value,
            "scan_id": self.scan_id,
            "simulation_id": self.simulation_id,
            "monte_carlo_id": self.monte_carlo_id,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "promotion_id": self.promotion_id,
            "created_at": self.created_at,
            "source_module": self.source_module,
            "scan_id": self.scan_id,
            "simulation_id": self.simulation_id,
            "monte_carlo_id": self.monte_carlo_id,
            "experiment_id": self.experiment_id,
            "session_id": self.session_id,
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "strategy_version": self.strategy_version,
            "strategy_parameters": self.strategy_parameters,
            "parameter_schema_version": self.parameter_schema_version,
            "symbol": self.symbol,
            "market_type": self.market_type,
            "execution_destination": self.execution_destination.value,
            "market_data_source": self.market_data_source.value,
            "capital": self.capital,
            "leverage": self.leverage,
            "historical_metrics": self.historical_metrics,
            "monte_carlo_metrics": self.monte_carlo_metrics,
            "source_hash": self.source_hash,
            "configuration_hash": self.configuration_hash,
            "testnet_only": self.testnet_only,
            "production_blocked": self.production_blocked,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> StrategyPromotionManifest:
        dest = ExecutionDestination(str(data.get("execution_destination", "PAPER")))
        md = MarketDataSource(str(data.get("market_data_source", "BINANCE_PUBLIC_MD")))
        return cls(
            promotion_id=str(data.get("promotion_id") or uuid.uuid4().hex[:16]),
            created_at=str(data.get("created_at") or datetime.now(UTC).isoformat()),
            source_module=str(data.get("source_module") or "manual"),
            strategy_id=str(data["strategy_id"]),
            strategy_name=str(data.get("strategy_name") or data["strategy_id"]),
            strategy_version=str(data.get("strategy_version") or "1.0.0"),
            strategy_parameters=dict(data.get("strategy_parameters") or {}),
            parameter_schema_version=str(data.get("parameter_schema_version") or "1"),
            symbol=str(data["symbol"]).upper(),
            market_type=str(data.get("market_type") or "spot"),
            execution_destination=dest,
            market_data_source=md,
            testnet_only=bool(data.get("testnet_only", True)),
            production_blocked=bool(data.get("production_blocked", True)),
            scan_id=data.get("scan_id") if data.get("scan_id") else None,
            simulation_id=data.get("simulation_id") if data.get("simulation_id") else None,
            monte_carlo_id=data.get("monte_carlo_id") if data.get("monte_carlo_id") else None,
            experiment_id=data.get("experiment_id") if data.get("experiment_id") else None,
            session_id=data.get("session_id") if data.get("session_id") else None,
            capital=str(data["capital"]) if data.get("capital") is not None else None,
            leverage=str(data["leverage"]) if data.get("leverage") is not None else None,
            historical_metrics=dict(data.get("historical_metrics") or {}),
            monte_carlo_metrics=dict(data.get("monte_carlo_metrics") or {}),
            source_hash=str(data.get("source_hash") or ""),
            configuration_hash=str(data.get("configuration_hash") or ""),
        )


def build_manifest_from_body(body: Mapping[str, Any]) -> StrategyPromotionManifest:
    if "strategy_id" not in body or "symbol" not in body:
        raise ValidationError("strategy_id y symbol requeridos")
    return StrategyPromotionManifest.from_dict(body)
