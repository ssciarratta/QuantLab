"""Adapters thin del laboratorio para el workbench (research-safe, sin LIVE).

Usa datos sintéticos en memoria / registry temporal. Nunca envía órdenes live.
"""

from __future__ import annotations

import re
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from quantlab.backtester import BarBacktestConfig, BarBacktester
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import ExperimentStatus
from quantlab.core.types.manifests import ExecutionModelVersions, ExperimentManifest
from quantlab.core.types.market import Bar
from quantlab.core.types.results import SimulationResult
from quantlab.core.types.serialization import dataclass_to_dict, to_jsonable
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.execution_export.hummingbot import HummingbotExporter
from quantlab.experiments.registry import ExperimentRegistry
from quantlab.features.pipeline import build_pipeline
from quantlab.features.serialization import feature_frame_to_dict
from quantlab.features.transformers import ClosePriceTransformer, SimpleReturnTransformer
from quantlab.montecarlo.simulator import MonteCarloSimulator
from quantlab.optimizer.grid import GridSearchOptimizer
from quantlab.research.alpha import AlphaScanner
from quantlab.research.strategies.buy_once import BuyOnceStrategy
from quantlab.research.strategies.simple_momentum import SimpleMomentumStrategy
from quantlab.validation.splits import train_val_oos_split, walk_forward
from quantlab.workbench.strategy_catalog import (
    CANONICAL_STRATEGY_IDS,
    build_strategy,
    list_strategy_catalog,
    list_strategy_ids,
    maybe_wrap_for_bar_backtest,
    merge_default_params,
    normalize_strategy_id,
)

STRATEGY_IDS: tuple[str, ...] = CANONICAL_STRATEGY_IDS

# Fail-closed path segment / export filename (F25 M1).
_EXPERIMENT_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def validate_experiment_id(experiment_id: str) -> str:
    """Valida ``experiment_id`` charset ``^[A-Za-z0-9_-]+$`` (sin path separators)."""
    if not isinstance(experiment_id, str):
        raise ValidationError(f"experiment_id inválido (tipo): {type(experiment_id).__name__}")
    eid = experiment_id.strip()
    if not eid or not _EXPERIMENT_ID_RE.fullmatch(eid):
        raise ValidationError(
            f"experiment_id inválido (charset ^[A-Za-z0-9_-]+$): {experiment_id!r}"
        )
    return eid


CAPABILITIES: tuple[dict[str, str], ...] = (
    {
        "id": "backtest",
        "label": "Backtest bar-based",
        "method": "POST",
        "path": "/api/lab/backtest",
    },
    {"id": "scanner", "label": "Alpha Scanner", "method": "POST", "path": "/api/lab/scanner"},
    {
        "id": "metrics",
        "label": "Último resultado / metrics",
        "method": "GET",
        "path": "/api/lab/metrics",
    },
    {
        "id": "experiments",
        "label": "Experiment Registry",
        "method": "GET",
        "path": "/api/lab/experiments",
    },
    {
        "id": "optimize",
        "label": "Optimizer grid (mini)",
        "method": "POST",
        "path": "/api/lab/optimize",
    },
    {
        "id": "montecarlo",
        "label": "Monte Carlo (mini)",
        "method": "POST",
        "path": "/api/lab/montecarlo",
    },
    {
        "id": "features",
        "label": "Features pipeline demo",
        "method": "POST",
        "path": "/api/lab/features",
    },
    {
        "id": "export_hb",
        "label": "Hummingbot export",
        "method": "POST",
        "path": "/api/lab/export-hb",
    },
    {
        "id": "validation",
        "label": "Validation splits",
        "method": "GET",
        "path": "/api/lab/validation",
    },
    {
        "id": "strategies",
        "label": "Strategy catalog",
        "method": "GET",
        "path": "/api/lab/strategies",
    },
    {"id": "health", "label": "Health / Mode", "method": "GET", "path": "/api/health"},
    {"id": "market", "label": "Market Data", "method": "GET", "path": "/api/broker/snapshot"},
    {"id": "blotter", "label": "Paper Blotter", "method": "POST", "path": "/api/paper/submit"},
)


def make_synthetic_bars(
    n: int = 24,
    *,
    instrument_id: str = "WB:SYN",
    start_price: int = 100,
    drift: int = 1,
) -> list[Bar]:
    """Barras 1m sintéticas deterministas (sin red / credenciales)."""
    if n < 1:
        raise ValidationError("n_bars >= 1")
    out: list[Bar] = []
    base = datetime(2024, 6, 1, tzinfo=UTC)
    for i in range(n):
        c = Decimal(start_price + drift * i)
        t0 = base + timedelta(minutes=i)
        out.append(
            Bar(
                instrument_id=instrument_id,
                open=c,
                high=c + Decimal("1"),
                low=c - Decimal("1"),
                close=c,
                volume=Decimal("100") + Decimal(i),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(minutes=1),
                timeframe="1m",
            )
        )
    return out


def make_scanner_universe() -> dict[str, list[Bar]]:
    """Universo mínimo multi-instrumento para Alpha Scanner."""
    return {
        "WB:A": make_synthetic_bars(16, instrument_id="WB:A", start_price=100, drift=1),
        "WB:B": make_synthetic_bars(16, instrument_id="WB:B", start_price=50, drift=2),
        "WB:C": make_synthetic_bars(16, instrument_id="WB:C", start_price=200, drift=0),
    }


def _build_strategy(strategy_id: str, params: dict[str, Any]) -> Any:
    return build_strategy(strategy_id, params)


def run_lab_backtest(
    *,
    strategy_id: str = "momentum",
    params: dict[str, Any] | None = None,
    n_bars: int = 24,
    experiment_id: str = "wb-lab-backtest",
) -> dict[str, Any]:
    """Corre BarBacktester 5A sobre barras sintéticas."""
    experiment_id = validate_experiment_id(experiment_id)
    if n_bars < 4 or n_bars > 120:
        raise ValidationError("n_bars debe estar entre 4 y 120")
    sid = normalize_strategy_id(strategy_id)
    # Lab backtest: momentum default lookback=2 (histórico F21) si no viene en params.
    caller = dict(params or {})
    if sid == "momentum" and "lookback" not in caller:
        caller["lookback"] = 2
    strategy_params = merge_default_params(sid, caller)

    bars = make_synthetic_bars(n_bars)
    strategy = maybe_wrap_for_bar_backtest(sid, _build_strategy(sid, strategy_params))
    bt = BarBacktester(
        BarBacktestConfig(experiment_id=experiment_id, initial_cash=Decimal("100000"))
    )
    result = bt.run(strategy, bars)
    summary: dict[str, Any] = {
        "ok": True,
        "kind": "backtest",
        "strategy_id": sid,
        "params": strategy_params,
        "n_bars": n_bars,
        "n_fills": len(result.simulation.fills),
        "n_orders": len(result.simulation.orders),
        "accounting_ok": result.accounting.ok,
        "final_equity": str(
            result.simulation.equity_curve[-1].equity
            if result.simulation.equity_curve
            else Decimal("0")
        ),
        "metrics": dict(result.metrics.metrics),
        "metrics_version": result.metrics.metrics_version,
        "experiment_id": result.metrics.experiment_id,
        "live_routing": False,
        "live_blocked": LIVE_BLOCKED is True,
    }
    converted = to_jsonable(summary)
    if not isinstance(converted, dict):
        raise ValidationError("serialización backtest inválida")
    return converted


def run_lab_scanner(*, top_n: int = 3) -> dict[str, Any]:
    if top_n < 1 or top_n > 10:
        raise ValidationError("top_n debe estar entre 1 y 10")
    universe = make_scanner_universe()
    result = AlphaScanner().scan(universe, top_n=top_n, min_bars=3)
    return {
        "ok": True,
        "kind": "scanner",
        "top_n": top_n,
        "selected": list(result.selected),
        "scores": [dataclass_to_dict(s) for s in result.scores],
        "gap_events": list(result.gap_events),
        "schema_version": result.schema_version,
        "live_routing": False,
    }


def list_lab_experiments(registry_path: Path) -> dict[str, Any]:
    """Lista ExperimentRegistry (crea DB vacía si no existe)."""
    registry = ExperimentRegistry(registry_path)
    rows = registry.list()
    experiments = [
        {
            "experiment_id": r.experiment_id,
            "status": r.status.value,
            "dataset_id": r.dataset_id,
            "strategy_version": r.strategy_version,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat(),
            "artifact_paths": list(r.artifact_paths),
            "metadata": dict(r.metadata),
        }
        for r in rows
    ]
    return {
        "ok": True,
        "kind": "experiments",
        "path": str(registry_path),
        "count": len(experiments),
        "experiments": experiments,
        "live_routing": False,
    }


def ensure_demo_experiment(registry_path: Path) -> None:
    """Si el registry está vacío, inserta un draft demo (idempotente)."""
    registry = ExperimentRegistry(registry_path)
    if registry.list():
        return
    registry.create(
        experiment_id="wb-demo-exp",
        dataset_id="wb-synthetic",
        strategy_version="momentum-demo-1",
        metadata={"source": "workbench-lab", "live_routing": False},
    )


def run_lab_optimize(
    *,
    lookbacks: tuple[int, ...] = (2, 3),
    quantities: tuple[str, ...] = ("1",),
    n_bars: int = 20,
) -> dict[str, Any]:
    """Grid mini: lookback × quantity → sharpe (o 0 si no hay métrica)."""
    if len(lookbacks) * len(quantities) > 12:
        raise ValidationError("grid demasiado grande (máx 12 trials)")
    if n_bars < 8 or n_bars > 60:
        raise ValidationError("n_bars debe estar entre 8 y 60")
    bars = make_synthetic_bars(n_bars)

    def objective(params: dict[str, Any]) -> float:
        strategy = SimpleMomentumStrategy(
            {"lookback": int(params["lookback"]), "quantity": str(params["quantity"])}
        )
        bt = BarBacktester(BarBacktestConfig(experiment_id="wb-opt", initial_cash=Decimal("50000")))
        result = bt.run(strategy, bars)
        sharpe = result.metrics.metrics.get("sharpe", 0.0)
        return float(sharpe) if isinstance(sharpe, (int, float)) else 0.0

    space: dict[str, list[Any]] = {
        "lookback": list(lookbacks),
        "quantity": list(quantities),
    }
    opt = GridSearchOptimizer(seed=42)
    result = opt.grid(space, objective, maximize=True)
    return {
        "ok": True,
        "kind": "optimize",
        "method": result.method,
        "n_trials": len(result.history),
        "best": {
            "params": result.best.params,
            "score": result.best.score,
            "trial_id": result.best.trial_id,
        },
        "history": [
            {"params": t.params, "score": t.score, "trial_id": t.trial_id} for t in result.history
        ],
        "live_routing": False,
    }


def run_lab_montecarlo(
    *,
    n_scenarios: int = 5,
    n_bars: int = 16,
    noise_bps: float = 10.0,
) -> dict[str, Any]:
    if n_scenarios < 2 or n_scenarios > 20:
        raise ValidationError("n_scenarios debe estar entre 2 y 20 (mini)")
    if n_bars < 8 or n_bars > 60:
        raise ValidationError("n_bars debe estar entre 8 y 60")
    bars = make_synthetic_bars(n_bars)

    def runner(noisy: Any) -> SimulationResult:
        bt = BarBacktester(BarBacktestConfig(experiment_id="wb-mc", initial_cash=Decimal("50000")))
        return bt.run(BuyOnceStrategy({"quantity": "1"}), noisy).simulation

    mc = MonteCarloSimulator(seed=42)
    result = mc.run(bars, runner, n_scenarios=n_scenarios, noise_bps=noise_bps)
    return {
        "ok": True,
        "kind": "montecarlo",
        "n_scenarios": result.n_scenarios,
        "seed": result.seed,
        "mean_equity": result.mean_equity,
        "std_equity": result.std_equity,
        "ci_low": result.ci_low,
        "ci_high": result.ci_high,
        "final_equities": list(result.final_equities),
        "live_routing": False,
        "live_blocked": LIVE_BLOCKED is True,
    }


def run_lab_features(*, n_bars: int = 20) -> dict[str, Any]:
    if n_bars < 4 or n_bars > 120:
        raise ValidationError("n_bars debe estar entre 4 y 120")
    bars = make_synthetic_bars(n_bars)
    pipeline = build_pipeline(
        ClosePriceTransformer(),
        SimpleReturnTransformer(),
        name="wb_demo_pipeline",
    )
    frame = pipeline.run(bars)
    payload = feature_frame_to_dict(frame)
    # Resumen liviano para UI (sin todos los points si son muchos)
    series_summary = {
        name: {
            "min_lookback": s["min_lookback"],
            "n_points": len(s["points"]),
            "tail": s["points"][-3:] if s["points"] else [],
        }
        for name, s in payload["series"].items()
    }
    return {
        "ok": True,
        "kind": "features",
        "pipeline_name": frame.pipeline_name,
        "instrument_id": frame.instrument_id,
        "bar_count": frame.bar_count,
        "min_lookback": frame.min_lookback,
        "schema_version": frame.schema_version,
        "series_summary": series_summary,
        "live_routing": False,
    }


def run_lab_export_hb(
    export_root: Path,
    *,
    experiment_id: str = "wb-hb-export",
    strategy_version: str = "demo-1",
) -> dict[str, Any]:
    """Validate + build + export a path bajo export_root (path-safe). LIVE routing false."""
    if not LIVE_BLOCKED:
        raise ValidationError("LIVE_BLOCKED debe ser True; abortando export")
    experiment_id = validate_experiment_id(experiment_id)
    export_root = export_root.resolve()
    export_root.mkdir(parents=True, exist_ok=True)
    target = (export_root / f"{experiment_id}.json").resolve()
    try:
        target.relative_to(export_root)
    except ValueError as exc:
        raise ValidationError("path de export fuera de sandbox") from exc

    now = datetime.now(tz=UTC)
    manifest = ExperimentManifest(
        experiment_id=experiment_id,
        dataset_id="wb-synthetic",
        dataset_version="v1",
        resolved_config={"source": "workbench", "live_routing": False},
        seed=42,
        git_commit="workbench-lab",
        python_version="3.11",
        dependency_versions_or_hash="wb-lab",
        platform="workbench",
        strategy_version=strategy_version,
        execution_model_versions=ExecutionModelVersions(
            fee_model="none",
            slippage_model="none",
            latency_model="none",
            fill_model="immediate-bar",
        ),
        artifacts_produced=(),
        created_at=now,
        checksum="a" * 64,
        status=ExperimentStatus.DRAFT,
    )
    exporter = HummingbotExporter()
    validation = exporter.validate_export(manifest)
    if not validation.ok:
        raise ValidationError("manifest inválido: " + "; ".join(validation.issues))
    package = exporter.build_execution_package(manifest)
    if package.payload.get("live_routing") is not False:
        raise ValidationError("export debe tener live_routing=false")
    result = exporter.export_configuration(package, target)
    return {
        "ok": True,
        "kind": "export_hb",
        "path": result.path,
        "checksum_note": result.checksum_note,
        "live_routing": False,
        "blocked": True,
        "live_blocked": LIVE_BLOCKED is True,
        "validation_ok": validation.ok,
        "experiment_id": package.experiment_id,
        "payload_keys": sorted(package.payload.keys()),
    }


def run_lab_validation(*, n_bars: int = 40) -> dict[str, Any]:
    """Info de splits train/val/OOS + walk-forward (sin leakage check fallido)."""
    if n_bars < 20 or n_bars > 200:
        raise ValidationError("n_bars debe estar entre 20 y 200")
    bars = make_synthetic_bars(n_bars)
    split = train_val_oos_split(bars, train_frac=0.6, val_frac=0.2)
    folds = walk_forward(bars, train_size=10, test_size=5, step=5)
    return {
        "ok": True,
        "kind": "validation",
        "n_bars": n_bars,
        "train_val_oos": {
            "train": len(split.train),
            "validation": len(split.validation),
            "oos": len(split.oos),
            "train_end": split.train[-1].timestamp_close.isoformat() if split.train else None,
            "val_start": (
                split.validation[0].timestamp_open.isoformat() if split.validation else None
            ),
            "oos_start": split.oos[0].timestamp_open.isoformat() if split.oos else None,
        },
        "walk_forward": {
            "n_folds": len(folds),
            "folds": [
                {
                    "fold": f.fold,
                    "train": len(f.train),
                    "test": len(f.test),
                    "train_end": f.train[-1].timestamp_close.isoformat(),
                    "test_start": f.test[0].timestamp_open.isoformat(),
                }
                for f in folds
            ],
        },
        "live_routing": False,
    }


def lab_capabilities() -> dict[str, Any]:
    return {
        "ok": True,
        "kind": "capabilities",
        "version_module": "lab",
        "strategies": list_strategy_ids(),
        "strategy_catalog": list_strategy_catalog(),
        "features": [dict(c) for c in CAPABILITIES],
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }


def lab_strategies() -> dict[str, Any]:
    """GET /api/lab/strategies — catálogo con metadata (F27)."""
    return {
        "ok": True,
        "kind": "strategies",
        "strategies": list_strategy_catalog(),
        "ids": list_strategy_ids(),
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
    }


def default_lab_tmpdir(prefix: str) -> Path:
    return Path(tempfile.mkdtemp(prefix=prefix))
