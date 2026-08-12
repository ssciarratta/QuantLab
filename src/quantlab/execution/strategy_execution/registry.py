"""Registro de capacidades de ejecución por estrategia (catálogo workbench)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from quantlab.execution.strategy_execution.destinations import CertificationStatus
from quantlab.workbench.strategy_catalog import (
    RUNNABLE_STRATEGY_IDS,
    STRATEGY_CATALOG,
    StrategyMeta,
    normalize_strategy_id,
)
from quantlab.workbench.strategy_guides import FAMILY_LABELS_ES


# Testnet: todas las estrategias runnable del catálogo (motor paper + espejo testnet).
def _spot_testnet_supported(meta: StrategyMeta) -> bool:
    return meta.runnable


def _futures_testnet_supported(meta: StrategyMeta) -> bool:
    return meta.runnable


def is_paper_run_certified(strategy_id: str) -> bool:
    """Toda estrategia runnable del catálogo puede correr en paper session."""
    sid = normalize_strategy_id(strategy_id)
    meta = next((m for m in STRATEGY_CATALOG if m.id == sid), None)
    return meta is not None and meta.runnable


@dataclass(frozen=True, slots=True)
class StrategyExecutionCapabilities:
    strategy_id: str
    strategy_name: str
    strategy_version: str
    description: str
    family: str
    family_label_es: str
    runnable: bool
    parameter_schema: dict[str, Any]
    default_parameters: dict[str, Any]
    paper_supported: bool
    spot_testnet_supported: bool
    futures_testnet_supported: bool
    certification_status: CertificationStatus
    requires_adapter: bool
    research_only: bool
    hummingbot_adapter: str | None
    runtime_adjustable_parameters: tuple[str, ...]
    restart_required_parameters: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "strategy_version": self.strategy_version,
            "description": self.description,
            "family": self.family,
            "family_label_es": self.family_label_es,
            "runnable": self.runnable,
            "parameter_schema": self.parameter_schema,
            "default_parameters": self.default_parameters,
            "paper_supported": self.paper_supported,
            "spot_testnet_supported": self.spot_testnet_supported,
            "futures_testnet_supported": self.futures_testnet_supported,
            "certification_status": self.certification_status.value,
            "requires_adapter": self.requires_adapter,
            "research_only": self.research_only,
            "hummingbot_adapter": self.hummingbot_adapter,
            "runtime_adjustable_parameters": list(self.runtime_adjustable_parameters),
            "restart_required_parameters": list(self.restart_required_parameters),
            "ui_badge": _ui_badge(self.certification_status),
            "paper_run_certified": is_paper_run_certified(self.strategy_id),
        }


def _ui_badge(status: CertificationStatus) -> str:
    if status in {
        CertificationStatus.PAPER_READY,
        CertificationStatus.SPOT_TESTNET_READY,
        CertificationStatus.FUTURES_TESTNET_READY,
        CertificationStatus.CERTIFIED,
    }:
        return "ready"
    if status == CertificationStatus.ADAPTER_REQUIRED:
        return "adapter"
    return "research"


def _certification_for(meta: StrategyMeta) -> CertificationStatus:
    if not meta.runnable:
        return CertificationStatus.RESEARCH_ONLY
    return CertificationStatus.PAPER_READY


def _parameter_schema(meta: StrategyMeta) -> dict[str, Any]:
    props: dict[str, Any] = {}
    for key, val in meta.default_params.items():
        t = "string"
        if isinstance(val, bool):
            t = "boolean"
        elif isinstance(val, int):
            t = "integer"
        elif isinstance(val, float):
            t = "number"
        props[key] = {"type": t, "default": val}
    return {"type": "object", "properties": props}


def capabilities_for(meta: StrategyMeta) -> StrategyExecutionCapabilities:
    cert = _certification_for(meta)
    paper = meta.runnable and cert != CertificationStatus.RESEARCH_ONLY
    spot = _spot_testnet_supported(meta)
    futures = _futures_testnet_supported(meta)
    hb_adapter: str | None = None
    if futures:
        hb_adapter = "binance_perpetual_testnet"
    elif spot:
        hb_adapter = "quantlab_native_spot_testnet"
    return StrategyExecutionCapabilities(
        strategy_id=meta.id,
        strategy_name=meta.name,
        strategy_version="1.0.0",
        description=meta.description,
        family=meta.family,
        family_label_es=FAMILY_LABELS_ES.get(meta.family, meta.family),
        runnable=meta.runnable,
        parameter_schema=_parameter_schema(meta),
        default_parameters=dict(meta.default_params),
        paper_supported=paper,
        spot_testnet_supported=spot,
        futures_testnet_supported=futures,
        certification_status=cert,
        requires_adapter=meta.runnable
        and meta.factory in {"mm", "classic"},
        research_only=not meta.runnable,
        hummingbot_adapter=hb_adapter,
        runtime_adjustable_parameters=("quantity",) if meta.factory == "legacy" else (),
        restart_required_parameters=(
            "strategy_id",
            "symbol",
            "execution_destination",
            "market_type",
        ),
    )


class StrategyExecutionRegistry:
    """Descubre estrategias del catálogo workbench con capacidades de ejecución."""

    def list_strategies(self) -> list[StrategyExecutionCapabilities]:
        out = [capabilities_for(m) for m in STRATEGY_CATALOG]
        return sorted(out, key=lambda c: (c.family, c.strategy_name.lower()))

    def get(self, strategy_id: str) -> StrategyExecutionCapabilities:
        sid = normalize_strategy_id(strategy_id)
        for meta in STRATEGY_CATALOG:
            if meta.id == sid:
                return capabilities_for(meta)
        raise KeyError(f"strategy_id desconocido: {strategy_id}")

    def runnable_ids(self) -> tuple[str, ...]:
        return RUNNABLE_STRATEGY_IDS


def get_registry() -> StrategyExecutionRegistry:
    return StrategyExecutionRegistry()
