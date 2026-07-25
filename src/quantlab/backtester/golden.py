"""Golden runs reproducibles — fingerprint canónico (Fase 6 / 5A)."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.results import MetricsResult, SimulationResult


def simulation_fingerprint(result: SimulationResult) -> dict[str, Any]:
    """Payload determinista (sin IDs aleatorios ni timestamps de cómputo)."""
    sides = {o.order_id: o.side.value for o in result.orders}
    return {
        "experiment_id": result.experiment_id,
        "equity_curve": [
            {"ts": p.timestamp.isoformat(), "equity": str(p.equity)} for p in result.equity_curve
        ],
        "fills": [
            {
                "instrument_id": f.instrument_id,
                "side": sides.get(f.order_id, ""),
                "price": str(f.price),
                "quantity": str(f.quantity),
                "fee": str(f.fee.amount),
                "ts": f.timestamp.isoformat(),
            }
            for f in result.fills
        ],
        "n_orders": len(result.orders),
        "n_fills": len(result.fills),
        "final_equity": str(result.equity_curve[-1].equity) if result.equity_curve else "0",
        "policy": {
            k: result.metadata[k]
            for k in (
                "fill_model",
                "slippage_model",
                "latency_model",
                "fee_model",
                "schema_version",
                "initial_cash",
            )
            if k in result.metadata
        },
    }


def metrics_fingerprint(metrics: MetricsResult) -> dict[str, Any]:
    """Métricas canónicas (sin computed_at)."""
    keys = sorted(metrics.metrics.keys())
    return {
        "experiment_id": metrics.experiment_id,
        "metrics_version": metrics.metrics_version,
        "metrics": {k: metrics.metrics[k] for k in keys},
    }


def fingerprint_hash(payload: Mapping[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class GoldenRunSpec:
    """Especificación inmutable de un golden run."""

    name: str
    simulation_hash: str
    metrics_hash: str
    simulation: dict[str, Any]
    metrics: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "simulation_hash": self.simulation_hash,
            "metrics_hash": self.metrics_hash,
            "simulation": self.simulation,
            "metrics": self.metrics,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> GoldenRunSpec:
        return cls(
            name=str(data["name"]),
            simulation_hash=str(data["simulation_hash"]),
            metrics_hash=str(data["metrics_hash"]),
            simulation=dict(data["simulation"]),
            metrics=dict(data["metrics"]),
        )


def build_golden(
    *,
    name: str,
    simulation: SimulationResult,
    metrics: MetricsResult,
) -> GoldenRunSpec:
    sim_fp = simulation_fingerprint(simulation)
    met_fp = metrics_fingerprint(metrics)
    return GoldenRunSpec(
        name=name,
        simulation_hash=fingerprint_hash(sim_fp),
        metrics_hash=fingerprint_hash(met_fp),
        simulation=sim_fp,
        metrics=met_fp,
    )


def save_golden(path: Path, spec: GoldenRunSpec) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(spec.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def load_golden(path: Path) -> GoldenRunSpec:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValidationError("golden inválido")
    return GoldenRunSpec.from_dict(data)


def assert_matches_golden(
    *,
    simulation: SimulationResult,
    metrics: MetricsResult,
    golden: GoldenRunSpec,
) -> None:
    """Falla si el run actual diverge del golden (reproducibilidad)."""
    current = build_golden(name=golden.name, simulation=simulation, metrics=metrics)
    if current.simulation_hash != golden.simulation_hash:
        raise ValidationError(
            f"golden simulation drift: expected={golden.simulation_hash} "
            f"got={current.simulation_hash}"
        )
    if current.metrics_hash != golden.metrics_hash:
        raise ValidationError(
            f"golden metrics drift: expected={golden.metrics_hash} got={current.metrics_hash}"
        )
