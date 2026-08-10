"""Hashes y normalización de payloads Monte Carlo (trazabilidad + compat v1)."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from quantlab.core.types.market import Bar
from quantlab.montecarlo.models import (
    METHOD_DISCLAIMER,
    MONTECARLO_CONTRACT_VERSION,
    MonteCarloConfig,
    MonteCarloExperimentContext,
    MonteCarloMethod,
    unavailable_label,
)

# Persistidos nuevos = 2; lectura acepta 1 (legacy F34) y 2.
MONTECARLO_SCHEMA_VERSION_CURRENT = 2
MONTECARLO_SCHEMA_VERSION_LEGACY = 1


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def sha256_hex(payload: str | bytes) -> str:
    data = payload.encode("utf-8") if isinstance(payload, str) else payload
    return hashlib.sha256(data).hexdigest()


def hash_mapping(raw: Mapping[str, Any]) -> str:
    return sha256_hex(stable_json(dict(raw)))


def hash_bars(bars: Sequence[Bar]) -> str:
    rows = [
        {
            "instrument_id": b.instrument_id,
            "close": str(b.close),
            "volume": str(b.volume),
            "ts": b.timestamp_close.isoformat(),
            "tf": b.timeframe,
        }
        for b in bars
    ]
    return sha256_hex(stable_json(rows))


def try_code_commit() -> str | None:
    """Best-effort HEAD corto; None si no hay git (nunca inventar)."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2,
        )
        commit = out.strip()
        return commit or None
    except (OSError, subprocess.SubprocessError):
        return None


def display_value(value: Any) -> str:
    """UI: None → 'No disponible'; nunca convertir ausencia en 0."""
    if value is None:
        return unavailable_label()
    if isinstance(value, float) and value != value:  # NaN
        return unavailable_label()
    return str(value)


def normalize_montecarlo_payload(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Lectura no destructiva schema v1/v2 → dict enriquecido con fallbacks None."""
    body = dict(raw)
    schema = body.get("schema_version", MONTECARLO_SCHEMA_VERSION_LEGACY)
    try:
        schema_i = int(schema)
    except (TypeError, ValueError):
        schema_i = MONTECARLO_SCHEMA_VERSION_LEGACY

    ctx_raw = body.get("context")
    if isinstance(ctx_raw, dict):
        ctx = MonteCarloExperimentContext.from_dict(ctx_raw)
    else:
        # Compat v1: armar contexto mínimo desde campos planos si existen.
        orphan = schema_i <= MONTECARLO_SCHEMA_VERSION_LEGACY
        ctx = MonteCarloExperimentContext(
            run_id=_opt(body.get("run_id")),
            session_id=_opt(body.get("session_id")),
            strategy_id=_opt(body.get("strategy_id")),
            timeframe=_opt(body.get("timeframe")),
            dataset_source=_opt(body.get("dataset_source")),
            initial_equity=_opt_float(body.get("initial_equity")),
            created_at=_opt_dt(body.get("created_at")),
            orphan_technical_mode=orphan,
            orphan_warning=(
                "Corrida legacy (schema v1) o sin vínculo Scan/Backtest: "
                "modo técnico huérfano. Campos ausentes = No disponible."
                if orphan
                else None
            ),
        )

    cfg_raw = body.get("config")
    if isinstance(cfg_raw, dict):
        try:
            cfg = MonteCarloConfig.from_dict(cfg_raw)
            cfg_dict = cfg.to_dict()
        except Exception:
            cfg_dict = _legacy_config_dict(body)
    else:
        cfg_dict = _legacy_config_dict(body)

    metrics = body.get("metrics")
    if not isinstance(metrics, dict):
        metrics = {
            "mean_equity": body.get("mean_equity"),
            "std_equity": body.get("std_equity"),
            "ci_low": body.get("ci_low"),
            "ci_high": body.get("ci_high"),
            "ci_level": body.get("ci_level", 0.95),
            "ci_kind": "wald_mean",
            "median_equity": None,
            "p05_equity": None,
            "p95_equity": None,
            "mean_return_pct": None,
            "prob_profit": None,
            "prob_loss": None,
            "prob_above_initial": None,
            "max_drawdown_mean": None,
            "max_drawdown_p95": None,
            "paths_available": False,
            "finals_only": True,
            "notes": ["payload legacy o sin métricas enriquecidas"],
        }
    else:
        metrics = dict(metrics)

    # Completar probs si hay final_equities + initial_equity (corridas viejas).
    finals_raw = body.get("final_equities")
    initial = ctx.initial_equity
    if isinstance(finals_raw, list) and finals_raw and initial is not None:
        try:
            finals = [float(x) for x in finals_raw]
            n = len(finals)
            if metrics.get("prob_profit") is None:
                metrics["prob_profit"] = sum(1 for f in finals if f > initial) / n
            if metrics.get("prob_loss") is None:
                metrics["prob_loss"] = sum(1 for f in finals if f < initial) / n
            if metrics.get("prob_above_initial") is None:
                metrics["prob_above_initial"] = (
                    sum(1 for f in finals if f >= initial) / n
                )
        except (TypeError, ValueError):
            pass

    relations = body.get("relations")
    if not isinstance(relations, dict):
        relations = {
            "backtest_id": ctx.backtest_id,
            "scan_id": ctx.scan_id,
            "dataset_id": ctx.dataset_id,
            "strategy_config_id": ctx.strategy_config_id,
            "strategy_params_hash": ctx.strategy_params_hash,
            "dataset_hash": ctx.dataset_hash,
            "config_hash": body.get("config_hash"),
            "code_commit": ctx.code_commit,
        }

    out = dict(body)
    out["schema_version"] = schema_i
    out["contract_version"] = body.get("contract_version", MONTECARLO_CONTRACT_VERSION)
    out["context"] = ctx.to_dict()
    out["config"] = cfg_dict
    out["metrics"] = metrics
    out["relations"] = relations
    out["disclaimer"] = body.get("disclaimer", METHOD_DISCLAIMER)
    out["method"] = cfg_dict.get("method", MonteCarloMethod.PRICE_SHOCK_RERUN.value)
    # Campos planos legacy siempre presentes para UI vieja.
    out.setdefault("n_scenarios", cfg_dict.get("n_scenarios"))
    out.setdefault("n_bars", cfg_dict.get("n_bars"))
    out.setdefault("noise_bps", cfg_dict.get("noise_bps"))
    out.setdefault("seed", cfg_dict.get("seed"))
    out.setdefault("mean_equity", metrics.get("mean_equity"))
    out.setdefault("std_equity", metrics.get("std_equity"))
    out.setdefault("ci_low", metrics.get("ci_low"))
    out.setdefault("ci_high", metrics.get("ci_high"))
    out.setdefault("ci_level", metrics.get("ci_level", 0.95))
    return out


def build_lab_context(
    *,
    session_id: str | None = None,
    scan_id: str | None = None,
    backtest_id: str | None = None,
    strategy_id: str = "buy_once",
    strategy_params: Mapping[str, Any] | None = None,
    symbols: Sequence[str] | None = None,
    timeframe: str = "1m",
    dataset_source: str = "synthetic",
    dataset_id: str | None = "wb-synthetic",
    dataset_hash: str | None = None,
    initial_equity: float = 50000.0,
    fee_model: str = "binance_spot_vip0",
    code_commit: str | None = None,
    orphan: bool = False,
) -> MonteCarloExperimentContext:
    params = dict(strategy_params or {"quantity": "1"})
    warning = None
    src = (dataset_source or "").strip().lower()
    synthetic_demo = src in {"synthetic", "synthetic_lab"} or (
        (dataset_id or "") == "wb-synthetic"
    )
    # Huérfano = demo técnico sin Scan/Backtest.
    # NO forzar huérfano si el caller ya dijo orphan=False (p.ej. Simulador → MC).
    if orphan:
        warning = (
            "Modo técnico huérfano: sin scan_id/backtest_id. "
            "La corrida no está vinculada al flujo Scan → Backtest → MC."
        )
    elif scan_id is None and backtest_id is None and synthetic_demo:
        orphan = True
        warning = (
            "Modo técnico huérfano: sin scan_id/backtest_id. "
            "La corrida no está vinculada al flujo Scan → Backtest → MC. "
            "Si venís del Simulador, usá el botón «Monte Carlo» (misma selección)."
        )
    return MonteCarloExperimentContext(
        session_id=session_id,
        scan_id=scan_id,
        backtest_id=backtest_id,
        strategy_id=strategy_id,
        strategy_name=strategy_id,
        strategy_params_hash=hash_mapping(params),
        strategy_config_id=f"{strategy_id}:{hash_mapping(params)[:12]}",
        venue="lab",
        network="local",
        symbols=tuple(symbols) if symbols is not None else ("WB:SYN",),
        market_type="synthetic" if dataset_source == "synthetic" else None,
        timeframe=timeframe,
        dataset_id=dataset_id,
        dataset_hash=dataset_hash,
        dataset_source=dataset_source,
        initial_equity=float(initial_equity),
        fee_model=fee_model,
        slippage_model=None,
        funding_model=None,
        code_commit=code_commit if code_commit is not None else try_code_commit(),
        created_at=datetime.now(tz=UTC),
        orphan_technical_mode=orphan,
        orphan_warning=warning,
    )


def _legacy_config_dict(body: Mapping[str, Any]) -> dict[str, Any]:
    n_bars = int(body["n_bars"]) if body.get("n_bars") is not None else 16
    cfg = MonteCarloConfig(
        n_scenarios=int(body.get("n_scenarios", 5)),
        n_bars=n_bars,
        seed=int(body.get("seed", 42)),
        ci_level=float(body.get("ci_level", 0.95)),
        noise_bps=float(body.get("noise_bps", 10.0)),
        persist_result=bool(body.get("persisted", True)),
    )
    return cfg.to_dict()


def _opt(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        return s or None
    return str(value)


def _opt_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def _opt_dt(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value.strip():
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return None
