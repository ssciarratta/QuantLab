"""Adapters thin del laboratorio para el workbench (research-safe, sin LIVE).

Usa datos sintéticos en memoria / registry temporal. Nunca envía órdenes live.
"""

from __future__ import annotations

import re
import tempfile
from collections.abc import Mapping, Sequence
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
from quantlab.execution_export.hummingbot import ExecutionPackage, HummingbotExporter
from quantlab.experiments.registry import ExperimentRegistry
from quantlab.features.pipeline import build_pipeline
from quantlab.features.serialization import feature_frame_to_dict
from quantlab.features.store import FeatureStore
from quantlab.features.transformers import (
    ClosePriceTransformer,
    LogReturnTransformer,
    SimpleReturnTransformer,
)
from quantlab.montecarlo.simulator import MonteCarloSimulator
from quantlab.optimizer.grid import GridSearchOptimizer
from quantlab.optimizer.pareto import pareto_from_trials
from quantlab.research.alpha import AlphaScanner
from quantlab.research.strategies.buy_once import BuyOnceStrategy
from quantlab.research.strategies.simple_momentum import SimpleMomentumStrategy
from quantlab.validation.leakage import check_temporal_leakage
from quantlab.validation.splits import train_val_oos_split, walk_forward
from quantlab.workbench.montecarlo_runs import persist_montecarlo_run
from quantlab.workbench.optimizer_runs import persist_optimizer_run
from quantlab.workbench.strategy_catalog import (
    CANONICAL_STRATEGY_IDS,
    build_strategy,
    list_strategy_catalog,
    list_strategy_ids,
    maybe_wrap_for_bar_backtest,
    merge_default_params,
    normalize_strategy_id,
)
from quantlab.workbench.validation_runs import persist_validation_run

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
        "label": "Optimizer grid + Pareto (mini)",
        "method": "POST",
        "path": "/api/lab/optimize",
    },
    {
        "id": "optimize_history",
        "label": "Optimizer history (session)",
        "method": "GET",
        "path": "/api/lab/optimize/history",
    },
    {
        "id": "montecarlo",
        "label": "Monte Carlo (mini)",
        "method": "POST",
        "path": "/api/lab/montecarlo",
    },
    {
        "id": "montecarlo_history",
        "label": "Monte Carlo history (session)",
        "method": "GET",
        "path": "/api/lab/montecarlo/history",
    },
    {
        "id": "features",
        "label": "Features pipeline demo",
        "method": "POST",
        "path": "/api/lab/features/run",
    },
    {
        "id": "features_store",
        "label": "Feature Store browser",
        "method": "GET",
        "path": "/api/lab/features/store",
    },
    {
        "id": "export_hb",
        "label": "Hummingbot export",
        "method": "POST",
        "path": "/api/lab/export-hb",
    },
    {
        "id": "exports",
        "label": "Hummingbot exports (session)",
        "method": "GET",
        "path": "/api/lab/exports",
    },
    {
        "id": "validation",
        "label": "Validation / Walk-Forward runner",
        "method": "POST",
        "path": "/api/lab/validation/run",
    },
    {
        "id": "validation_list",
        "label": "Validation runs (session)",
        "method": "GET",
        "path": "/api/lab/validation",
    },
    {
        "id": "strategies",
        "label": "Strategy catalog",
        "method": "GET",
        "path": "/api/lab/strategies",
    },
    {
        "id": "reports",
        "label": "Reports / Metrics history",
        "method": "GET",
        "path": "/api/lab/reports",
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
    bars: list[Bar] | None = None,
    instrument_id: str | None = None,
    data_source: str = "synthetic",
    experiment_id: str = "wb-lab-backtest",
    reports_dir: Path | None = None,
) -> dict[str, Any]:
    """Corre BarBacktester 5A sobre barras sintéticas o ``bars`` provistas.

    Si ``reports_dir`` está set, persiste MetricsResult/summary (+ HTML) en
    sesión (F29 Report Viewer / Metrics History).
    """
    experiment_id = validate_experiment_id(experiment_id)
    sid = normalize_strategy_id(strategy_id)
    # Lab backtest: momentum default lookback=2 (histórico F21) si no viene en params.
    caller = dict(params or {})
    if sid == "momentum" and "lookback" not in caller:
        caller["lookback"] = 2
    strategy_params = merge_default_params(sid, caller)

    if bars is not None:
        if len(bars) < 4:
            raise ValidationError("bars requiere al menos 4 barras")
        run_bars = bars
        src = data_source
        iid = instrument_id or (bars[0].instrument_id if bars else None)
        n_used = len(run_bars)
    else:
        if n_bars < 4 or n_bars > 120:
            raise ValidationError("n_bars debe estar entre 4 y 120")
        run_bars = make_synthetic_bars(n_bars)
        src = "synthetic"
        iid = run_bars[0].instrument_id if run_bars else None
        n_used = n_bars

    strategy = maybe_wrap_for_bar_backtest(sid, _build_strategy(sid, strategy_params))
    bt = BarBacktester(
        BarBacktestConfig(experiment_id=experiment_id, initial_cash=Decimal("100000"))
    )
    result = bt.run(strategy, run_bars)
    summary: dict[str, Any] = {
        "ok": True,
        "kind": "backtest",
        "strategy_id": sid,
        "params": strategy_params,
        "n_bars": n_used,
        "data_source": src,
        "instrument_id": iid,
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
    if reports_dir is not None:
        from quantlab.workbench.reports import persist_backtest_report

        persisted = persist_backtest_report(
            reports_dir,
            metrics=result.metrics,
            simulation=result.simulation,
            summary=summary,
        )
        summary["report_id"] = persisted["report_id"]
        summary["report_path"] = persisted["path"]
        summary["report_has_html"] = persisted["has_html"]
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


def run_binance_lab_scanner(
    *,
    top_n: int = 5,
    symbol_limit: int = 15,
    interval: str = "1h",
    kline_limit: int = 24,
    base_url: str | None = None,
) -> dict[str, Any]:
    """AlphaScanner sobre klines Binance públicas (read-only)."""
    from quantlab.brokers.binance.public_md import (
        DEFAULT_BASE_URL,
        BinancePublicMdClient,
        fetch_universe_bars,
        validate_kline_interval,
    )

    if top_n < 1 or top_n > 10:
        raise ValidationError("top_n debe estar entre 1 y 10")
    if symbol_limit < 5 or symbol_limit > 30:
        raise ValidationError("symbol_limit debe estar entre 5 y 30")
    if kline_limit < 8 or kline_limit > 500:
        raise ValidationError("kline_limit debe estar entre 8 y 500")
    interval = validate_kline_interval(interval)

    url = base_url or DEFAULT_BASE_URL
    client = BinancePublicMdClient(base_url=url)
    symbols = client.list_spot_symbols(quote="USDT", limit=symbol_limit)
    if not symbols:
        raise ValidationError("sin símbolos USDT de Binance")

    bars_by_symbol = fetch_universe_bars(
        symbols,
        interval=interval,
        kline_limit=kline_limit,
        base_url=url,
    )
    if not bars_by_symbol:
        raise ValidationError("no se pudieron descargar klines Binance")

    universe: dict[str, list[Bar]] = {}
    symbol_map: dict[str, str] = {}
    for sym, sym_bars in bars_by_symbol.items():
        iid = f"BN:{sym}"
        universe[iid] = sym_bars
        symbol_map[iid] = sym

    result = AlphaScanner().scan(universe, top_n=top_n, min_bars=3)
    selected_symbols = [symbol_map.get(iid, iid) for iid in result.selected]

    return {
        "ok": True,
        "kind": "binance_scanner",
        "venue": "binance",
        "top_n": top_n,
        "symbol_limit": symbol_limit,
        "interval": interval,
        "kline_limit": kline_limit,
        "n_symbols_fetched": len(bars_by_symbol),
        "selected": list(result.selected),
        "selected_symbols": selected_symbols,
        "scores": [dataclass_to_dict(s) for s in result.scores],
        "gap_events": list(result.gap_events),
        "schema_version": result.schema_version,
        "read_only": True,
        "live_routing": False,
    }


def run_binance_lab_backtest_batch(
    *,
    symbols: Sequence[str],
    strategy_id: str = "momentum",
    params: dict[str, Any] | None = None,
    interval: str = "1h",
    kline_limit: int = 24,
    experiment_id_prefix: str = "wb-bn-bt",
    reports_dir: Path | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Backtest la misma estrategia sobre varios símbolos Binance (MD público)."""
    from quantlab.brokers.binance.public_md import (
        DEFAULT_BASE_URL,
        fetch_universe_bars,
        validate_kline_interval,
    )

    if not symbols:
        raise ValidationError("symbols vacío")
    if len(symbols) > 10:
        raise ValidationError("máximo 10 símbolos por batch")
    if kline_limit < 8 or kline_limit > 500:
        raise ValidationError("kline_limit debe estar entre 8 y 500")
    interval = validate_kline_interval(interval)
    prefix = validate_experiment_id(experiment_id_prefix)

    url = base_url or DEFAULT_BASE_URL
    norm = [s.strip().upper() for s in symbols if s.strip()]
    bars_by_symbol = fetch_universe_bars(
        norm,
        interval=interval,
        kline_limit=kline_limit,
        base_url=url,
    )
    if not bars_by_symbol:
        raise ValidationError("sin klines para backtest batch")

    runs: list[dict[str, Any]] = []
    for sym in norm:
        sym_bars = bars_by_symbol.get(sym)
        if not sym_bars:
            runs.append({"symbol": sym, "ok": False, "error": "sin klines"})
            continue
        eid = f"{prefix}-{sym}"[:120]
        try:
            bt = run_lab_backtest(
                strategy_id=strategy_id,
                params=params,
                bars=sym_bars,
                instrument_id=f"BN:{sym}",
                data_source="binance_klines",
                experiment_id=eid,
                reports_dir=reports_dir,
            )
            runs.append({"symbol": sym, "ok": True, "result": bt})
        except ValidationError as exc:
            runs.append({"symbol": sym, "ok": False, "error": str(exc)})

    ok_runs = [r for r in runs if r.get("ok")]
    return {
        "ok": len(ok_runs) > 0,
        "kind": "binance_backtest_batch",
        "venue": "binance",
        "strategy_id": normalize_strategy_id(strategy_id),
        "interval": interval,
        "kline_limit": kline_limit,
        "n_requested": len(norm),
        "n_ok": len(ok_runs),
        "runs": runs,
        "read_only": True,
        "live_routing": False,
        "live_blocked": LIVE_BLOCKED is True,
    }


def run_binance_lab_pipeline(
    *,
    strategy_id: str = "momentum",
    params: dict[str, Any] | None = None,
    top_n: int = 5,
    symbol_limit: int = 15,
    interval: str = "1h",
    kline_limit: int = 24,
    experiment_id_prefix: str = "wb-bn-pipe",
    reports_dir: Path | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Scan alpha Binance → backtest top-N en un solo paso (F111)."""
    scan = run_binance_lab_scanner(
        top_n=top_n,
        symbol_limit=symbol_limit,
        interval=interval,
        kline_limit=kline_limit,
        base_url=base_url,
    )
    selected_symbols = list(scan.get("selected_symbols") or [])
    if not selected_symbols:
        return {
            "ok": False,
            "kind": "binance_pipeline",
            "error": "scanner sin selección",
            "scanner": scan,
            "live_routing": False,
        }

    batch = run_binance_lab_backtest_batch(
        symbols=selected_symbols,
        strategy_id=strategy_id,
        params=params,
        interval=interval,
        kline_limit=kline_limit,
        experiment_id_prefix=experiment_id_prefix,
        reports_dir=reports_dir,
        base_url=base_url,
    )
    return {
        "ok": batch.get("ok") is True,
        "kind": "binance_pipeline",
        "venue": "binance",
        "strategy_id": batch.get("strategy_id"),
        "scanner": scan,
        "backtests": batch,
        "read_only": True,
        "live_routing": False,
        "live_blocked": LIVE_BLOCKED is True,
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


def _metric_float(metrics: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    raw = metrics.get(key, default)
    return float(raw) if isinstance(raw, (int, float)) else default


def run_lab_optimize(
    *,
    lookbacks: tuple[int, ...] = (2, 3),
    quantities: tuple[str, ...] = ("1",),
    n_bars: int = 20,
    persist: bool = False,
    optimizer_root: Path | None = None,
) -> dict[str, Any]:
    """Grid mini: lookback × quantity → sharpe (+ Pareto sharpe/MDD) — F33.

    Si ``persist`` y ``optimizer_root``: escribe summary en session ``optimizer/``.
    """
    if len(lookbacks) * len(quantities) > 12:
        raise ValidationError("grid demasiado grande (máx 12 trials)")
    if n_bars < 8 or n_bars > 60:
        raise ValidationError("n_bars debe estar entre 8 y 60")
    bars = make_synthetic_bars(n_bars)
    second_objective: list[float] = []
    trial_metrics: list[dict[str, float]] = []

    def objective(params: dict[str, Any]) -> float:
        strategy = SimpleMomentumStrategy(
            {"lookback": int(params["lookback"]), "quantity": str(params["quantity"])}
        )
        bt = BarBacktester(BarBacktestConfig(experiment_id="wb-opt", initial_cash=Decimal("50000")))
        result = bt.run(strategy, bars)
        m = result.metrics.metrics
        sharpe = _metric_float(m, "sharpe")
        mdd = _metric_float(m, "max_drawdown")
        second_objective.append(mdd)
        trial_metrics.append({"sharpe": sharpe, "max_drawdown": mdd})
        return sharpe

    space: dict[str, list[Any]] = {
        "lookback": list(lookbacks),
        "quantity": list(quantities),
    }
    opt = GridSearchOptimizer(seed=42)
    result = opt.grid(space, objective, maximize=True)

    history: list[dict[str, Any]] = []
    for i, t in enumerate(result.history):
        metrics = trial_metrics[i] if i < len(trial_metrics) else {}
        history.append(
            {
                "params": t.params,
                "score": t.score,
                "trial_id": t.trial_id,
                "metrics": metrics,
            }
        )

    pareto_payload: dict[str, Any] | None = None
    if len(result.history) >= 2 and len(second_objective) == len(result.history):
        front = pareto_from_trials(
            result.history,
            second_objective=second_objective,
            maximize=(True, False),
        )
        pareto_payload = {
            "objectives": [
                {"key": "sharpe", "direction": "max"},
                {"key": "max_drawdown", "direction": "min"},
            ],
            "n_front": len(front.front),
            "n_dominated": len(front.dominated),
            "front": [
                {
                    "trial_id": p.trial_id,
                    "params": p.params,
                    "objectives": {
                        "sharpe": p.objectives[0],
                        "max_drawdown": p.objectives[1],
                    },
                }
                for p in front.front
            ],
            "dominated": [
                {
                    "trial_id": p.trial_id,
                    "params": p.params,
                    "objectives": {
                        "sharpe": p.objectives[0],
                        "max_drawdown": p.objectives[1],
                    },
                }
                for p in front.dominated
            ],
        }

    best_metrics: dict[str, float] = {}
    for row in history:
        if row["trial_id"] == result.best.trial_id:
            raw_m = row.get("metrics") or {}
            if isinstance(raw_m, dict):
                best_metrics = {
                    str(k): float(v) for k, v in raw_m.items() if isinstance(v, (int, float))
                }
            break

    payload: dict[str, Any] = {
        "ok": True,
        "kind": "optimize",
        "method": result.method,
        "n_bars": n_bars,
        "params": {
            "lookbacks": list(lookbacks),
            "quantities": list(quantities),
        },
        "n_trials": len(result.history),
        "best": {
            "params": result.best.params,
            "score": result.best.score,
            "trial_id": result.best.trial_id,
            "metrics": best_metrics,
        },
        "history": history,
        "pareto": pareto_payload,
        "persisted": False,
        "run_id": None,
        "path": None,
        "live_routing": False,
        "live_blocked": LIVE_BLOCKED is True,
    }

    if persist:
        if optimizer_root is None:
            raise ValidationError("optimizer_root requerido para persist=True")
        if not LIVE_BLOCKED:
            raise ValidationError("LIVE_BLOCKED debe ser True; abortando optimizer persist")
        payload = persist_optimizer_run(Path(optimizer_root), payload)
    return payload


def run_lab_montecarlo(
    *,
    n_scenarios: int = 5,
    n_bars: int = 16,
    noise_bps: float = 10.0,
    persist: bool = True,
    montecarlo_root: Path | None = None,
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
    payload: dict[str, Any] = {
        "ok": True,
        "kind": "montecarlo",
        "n_scenarios": result.n_scenarios,
        "n_bars": n_bars,
        "noise_bps": float(noise_bps),
        "seed": result.seed,
        "mean_equity": result.mean_equity,
        "std_equity": result.std_equity,
        "ci_low": result.ci_low,
        "ci_high": result.ci_high,
        "ci_level": 0.95,
        "final_equities": list(result.final_equities),
        "persisted": False,
        "run_id": None,
        "path": None,
        "live_routing": False,
        "live_blocked": LIVE_BLOCKED is True,
    }
    if persist:
        if montecarlo_root is None:
            raise ValidationError("montecarlo_root requerido para persist=True")
        if not LIVE_BLOCKED:
            raise ValidationError("LIVE_BLOCKED debe ser True; abortando montecarlo persist")
        payload = persist_montecarlo_run(Path(montecarlo_root), payload)
    return payload


def _demo_feature_version() -> str:
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S%f")[:-3] + "Z"
    return f"wb-demo-{stamp}"


def run_lab_features(
    *,
    n_bars: int = 20,
    store_root: Path | None = None,
    version: str | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    """Pipeline demo (close + simple_return + log_return) → FeatureStore sesión.

    Si ``persist`` y ``store_root``: escribe via ``FeatureStore.put`` (F31).
    """
    if n_bars < 4 or n_bars > 120:
        raise ValidationError("n_bars debe estar entre 4 y 120")
    bars = make_synthetic_bars(n_bars)
    pipeline = build_pipeline(
        ClosePriceTransformer(),
        SimpleReturnTransformer(),
        LogReturnTransformer(),
        name="wb_demo_pipeline",
    )
    frame = pipeline.run(bars)
    payload = feature_frame_to_dict(frame)
    columns = sorted(payload["series"].keys())
    # Resumen liviano para UI (sin todos los points si son muchos)
    series_summary = {
        name: {
            "min_lookback": s["min_lookback"],
            "n_points": len(s["points"]),
            "tail": s["points"][-3:] if s["points"] else [],
        }
        for name, s in payload["series"].items()
    }
    result: dict[str, Any] = {
        "ok": True,
        "kind": "features",
        "pipeline_name": frame.pipeline_name,
        "instrument_id": frame.instrument_id,
        "bar_count": frame.bar_count,
        "min_lookback": frame.min_lookback,
        "schema_version": frame.schema_version,
        "series_summary": series_summary,
        "columns": columns,
        "persisted": False,
        "store_ref": None,
        "store_path": None,
        "live_routing": False,
        "live_blocked": LIVE_BLOCKED is True,
    }
    if persist and store_root is not None:
        if not LIVE_BLOCKED:
            raise ValidationError("LIVE_BLOCKED debe ser True; abortando feature persist")
        ver = (version or _demo_feature_version()).strip()
        if not ver:
            raise ValidationError("version de feature inválida")
        store = FeatureStore(Path(store_root))
        ref = store.put(frame, version=ver)
        result["persisted"] = True
        result["store_path"] = str(Path(store_root).resolve())
        result["store_ref"] = {
            "instrument_id": ref.instrument_id,
            "pipeline_name": ref.pipeline_name,
            "version": ref.version,
            "path": ref.path,
            "checksum": ref.checksum,
            "schema_version": ref.schema_version,
            "created_at": ref.created_at.isoformat(),
            "columns": columns,
        }
    return result


def run_lab_export_hb(
    export_root: Path,
    *,
    experiment_id: str = "wb-hb-export",
    strategy_version: str = "demo-1",
    dataset_id: str = "wb-synthetic",
) -> dict[str, Any]:
    """Validate + build + export a path bajo export_root (path-safe). LIVE routing false.

    Escribe:
    - ``{experiment_id}.json`` — alias latest (compat F21)
    - ``{export_id}.json`` — snapshot histórico único (F34)
    """
    if not LIVE_BLOCKED:
        raise ValidationError("LIVE_BLOCKED debe ser True; abortando export")
    experiment_id = validate_experiment_id(experiment_id)
    dataset_id = validate_experiment_id(dataset_id) if dataset_id else "wb-synthetic"
    export_root = export_root.resolve()
    export_root.mkdir(parents=True, exist_ok=True)

    now = datetime.now(tz=UTC)
    stamp = now.strftime("%Y%m%dT%H%M%S%f")[:-3] + "Z"
    export_id_raw = f"hb-{stamp}-{experiment_id}"
    export_id = export_id_raw[:120]
    # Fail-closed: stems path-safe
    for stem in (experiment_id, export_id):
        if "/" in stem or "\\" in stem or ".." in stem:
            raise ValidationError(f"export stem inválido: {stem!r}")

    latest_target = (export_root / f"{experiment_id}.json").resolve()
    hist_target = (export_root / f"{export_id}.json").resolve()
    for target in (latest_target, hist_target):
        try:
            target.relative_to(export_root)
        except ValueError as exc:
            raise ValidationError("path de export fuera de sandbox") from exc

    manifest = ExperimentManifest(
        experiment_id=experiment_id,
        dataset_id=dataset_id,
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

    # Enrich package payload for listing / wizard.
    enriched = dict(package.payload)
    enriched["export_id"] = export_id
    enriched["created_at"] = now.isoformat()
    enriched["strategy_version"] = strategy_version
    enriched["live_routing"] = False
    enriched["blocked"] = True

    hist_package = ExecutionPackage(
        experiment_id=package.experiment_id,
        strategy_version=package.strategy_version,
        payload=enriched,
    )
    latest_package = ExecutionPackage(
        experiment_id=package.experiment_id,
        strategy_version=package.strategy_version,
        payload={**enriched, "export_id": experiment_id, "is_latest_alias": True},
    )
    hist_result = exporter.export_configuration(hist_package, hist_target)
    latest_result = exporter.export_configuration(latest_package, latest_target)
    return {
        "ok": True,
        "kind": "export_hb",
        "path": hist_result.path,
        "latest_path": latest_result.path,
        "export_id": export_id,
        "checksum_note": hist_result.checksum_note,
        "live_routing": False,
        "blocked": True,
        "live_blocked": LIVE_BLOCKED is True,
        "validation_ok": validation.ok,
        "validation_issues": list(validation.issues),
        "experiment_id": package.experiment_id,
        "strategy_version": strategy_version,
        "created_at": now.isoformat(),
        "payload_keys": sorted(enriched.keys()),
        "banner": "live_routing:false — sin order routing LIVE",
        "steps": {
            "validate": {"ok": validation.ok, "issues": list(validation.issues)},
            "build": {"ok": True, "keys": sorted(enriched.keys())},
            "export": {"ok": True, "path": hist_result.path, "latest_path": latest_result.path},
        },
    }


def _segment_indices(
    bars: Sequence[Bar],
    segment: Sequence[Bar],
    *,
    offset: int = 0,
) -> dict[str, Any]:
    """Índices inclusivos del segmento respecto a ``bars`` (o offset absoluto)."""
    count = len(segment)
    if count == 0:
        return {
            "count": 0,
            "start_idx": None,
            "end_idx": None,
            "start_ts": None,
            "end_ts": None,
        }
    # Match por identidad de timestamps (serie sintética ordenada).
    start_ts = segment[0].timestamp_open
    end_ts = segment[-1].timestamp_close
    start_idx: int | None = None
    for i, bar in enumerate(bars):
        if bar.timestamp_open == start_ts:
            start_idx = offset + i
            break
    if start_idx is None:
        start_idx = offset
    end_idx = start_idx + count - 1
    return {
        "count": count,
        "start_idx": start_idx,
        "end_idx": end_idx,
        "start_ts": start_ts.isoformat(),
        "end_ts": end_ts.isoformat(),
    }


def _leakage_entry(pair: str, left: Sequence[Bar], right: Sequence[Bar]) -> dict[str, Any]:
    report = check_temporal_leakage(left, right)
    return {"pair": pair, "ok": report.ok, "issues": list(report.issues)}


def run_lab_validation(
    *,
    n_bars: int = 40,
    train_frac: float = 0.6,
    val_frac: float = 0.2,
    train_size: int = 10,
    test_size: int = 5,
    step: int | None = None,
    persist: bool = False,
    validation_root: Path | None = None,
) -> dict[str, Any]:
    """Walk-forward + train/val/OOS sobre barras sintéticas + anti-leakage (F32).

    Si ``persist`` y ``validation_root``: escribe summary en session ``validation/``.
    """
    if n_bars < 20 or n_bars > 200:
        raise ValidationError("n_bars debe estar entre 20 y 200")
    if train_size < 1 or test_size < 1:
        raise ValidationError("train_size/test_size inválidos")
    wf_step = step if step is not None else test_size
    if wf_step < 1:
        raise ValidationError("step inválido")

    bars = make_synthetic_bars(n_bars)
    split = train_val_oos_split(bars, train_frac=train_frac, val_frac=val_frac)
    folds = walk_forward(bars, train_size=train_size, test_size=test_size, step=wf_step)

    train_n = len(split.train)
    val_n = len(split.validation)
    train_seg = _segment_indices(bars, split.train)
    val_seg = _segment_indices(bars[train_n:], split.validation, offset=train_n)
    oos_seg = _segment_indices(bars[train_n + val_n :], split.oos, offset=train_n + val_n)

    # Walk-forward: índices absolutos vía start del fold.
    wf_folds: list[dict[str, Any]] = []
    start = 0
    for f in folds:
        tr = _segment_indices(bars[start:], f.train, offset=start)
        te = _segment_indices(bars[start + train_size :], f.test, offset=start + train_size)
        wf_folds.append(
            {
                "fold": f.fold,
                "train": len(f.train),
                "test": len(f.test),
                "train_idx": tr,
                "test_idx": te,
                "train_end": f.train[-1].timestamp_close.isoformat(),
                "test_start": f.test[0].timestamp_open.isoformat(),
            }
        )
        start += wf_step

    leakage_checks = [
        _leakage_entry("train_vs_validation", split.train, split.validation),
        _leakage_entry("validation_vs_oos", split.validation, split.oos),
        _leakage_entry("train_vs_oos", split.train, split.oos),
    ]
    for f in folds:
        leakage_checks.append(_leakage_entry(f"wf_fold_{f.fold}", f.train, f.test))
    n_failed = sum(1 for c in leakage_checks if not c["ok"])
    anti = {
        "ok": n_failed == 0,
        "n_checks": len(leakage_checks),
        "n_failed": n_failed,
        "checks": leakage_checks,
    }

    result: dict[str, Any] = {
        "ok": anti["ok"],
        "kind": "validation",
        "n_bars": n_bars,
        "source": "synthetic",
        "instrument_id": bars[0].instrument_id if bars else None,
        "params": {
            "train_frac": train_frac,
            "val_frac": val_frac,
            "train_size": train_size,
            "test_size": test_size,
            "step": wf_step,
        },
        "train_val_oos": {
            # Compat F21: counts planos
            "train": train_n,
            "validation": val_n,
            "oos": len(split.oos),
            "train_end": split.train[-1].timestamp_close.isoformat() if split.train else None,
            "val_start": (
                split.validation[0].timestamp_open.isoformat() if split.validation else None
            ),
            "oos_start": split.oos[0].timestamp_open.isoformat() if split.oos else None,
            "segments": {
                "train": train_seg,
                "validation": val_seg,
                "oos": oos_seg,
            },
        },
        "walk_forward": {
            "n_folds": len(folds),
            "train_size": train_size,
            "test_size": test_size,
            "step": wf_step,
            "folds": wf_folds,
        },
        "anti_leakage": anti,
        "multiple_testing": {
            "available_methods": ["bonferroni", "holm", "fdr_bh"],
            "note": (
                "APIs quantlab.validation.multiple_testing disponibles; "
                "este runner reporta splits + leakage, no p-values de estrategia"
            ),
        },
        "persisted": False,
        "run_id": None,
        "path": None,
        "live_routing": False,
        "live_blocked": LIVE_BLOCKED is True,
    }

    if persist:
        if validation_root is None:
            raise ValidationError("validation_root requerido para persist=True")
        if not LIVE_BLOCKED:
            raise ValidationError("LIVE_BLOCKED debe ser True; abortando validation persist")
        result = persist_validation_run(Path(validation_root), result)
    return result


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
    """GET /api/lab/strategies — catálogo con metadata (F27/F115)."""
    strategies = list_strategy_catalog()
    runnable = [s["id"] for s in strategies if s.get("runnable")]
    families = sorted({str(s.get("family") or "") for s in strategies if s.get("family")})
    return {
        "ok": True,
        "kind": "strategies",
        "strategies": strategies,
        "ids": list_strategy_ids(),
        "runnable_ids": runnable,
        "families": families,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "note": (
            "runnable=true → backtest/paper/Binance demo post-unlock. "
            "LIVE producción sigue bloqueado (LIVE_BLOCKED)."
        ),
    }


def default_lab_tmpdir(prefix: str) -> Path:
    return Path(tempfile.mkdtemp(prefix=prefix))
