"""Enriquece el resultado del Alpha Scanner con Kronos (sin panel nuevo).

Invariantes:
- Solo usa barras del tramo de ranking (anti-leakage).
- Métricas ausentes = None (nunca 0 fingido).
- Fallos → ranking tradicional intacto + meta tipada.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from quantlab.core.types.market import Bar
from quantlab.research.alpha.kronos.adapter_ohlcv import build_forecast_request
from quantlab.research.alpha.kronos.cache import (
    KronosDiskCache,
    forecast_cache_key,
    hash_closes,
)
from quantlab.research.alpha.kronos.config import KronosConfig
from quantlab.research.alpha.kronos.errors import KronosError, KronosSkipReason, KronosStatus
from quantlab.research.alpha.kronos.loader import deps_health, get_forecast_engine
from quantlab.research.alpha.kronos.metrics import KronosMetrics, compute_kronos_metrics
from quantlab.research.alpha.kronos.protocol import (
    ForecastEngine,
    ForecastResult,
    TrajectoryBatch,
)
from quantlab.research.alpha.kronos.scoring_bridge import brief_explanation, build_score_fields

logger = logging.getLogger(__name__)


def _traditional_from_row(row: Mapping[str, Any]) -> float:
    for key in ("composite", "base_score", "final_score", "traditional_score"):
        v = row.get(key)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                continue
    return 0.0


def _range_from_bars(bars: Sequence[Bar]) -> tuple[float, float]:
    highs = [float(b.high) for b in bars]
    lows = [float(b.low) for b in bars]
    return max(highs), min(lows)


def _trajectories_from_cache(payload: dict[str, Any]) -> TrajectoryBatch | None:
    try:
        closes = payload["closes"]
        highs = payload["highs"]
        lows = payload["lows"]
        opens = payload["opens"]
        return TrajectoryBatch(
            opens=tuple(tuple(float(x) for x in row) for row in opens),
            highs=tuple(tuple(float(x) for x in row) for row in highs),
            lows=tuple(tuple(float(x) for x in row) for row in lows),
            closes=tuple(tuple(float(x) for x in row) for row in closes),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _cache_payload(batch: TrajectoryBatch, meta: dict[str, Any]) -> dict[str, Any]:
    return {
        "opens": [list(r) for r in batch.opens],
        "highs": [list(r) for r in batch.highs],
        "lows": [list(r) for r in batch.lows],
        "closes": [list(r) for r in batch.closes],
        "meta": meta,
    }


def apply_kronos_to_scan(
    scan_out: dict[str, Any],
    bars_by_instrument: Mapping[str, Sequence[Bar]],
    *,
    config: KronosConfig,
    profile: str,
    interval: str = "1h",
    cache_dir: Path | None = None,
    engine: ForecastEngine | None = None,
) -> dict[str, Any]:
    """Mutación controlada del dict de scanner: scores + kronos meta.

    ``bars_by_instrument`` DEBE ser solo el tramo de ranking (nunca OOS).
    """
    t0 = time.perf_counter()
    weight = config.weight_for_profile(profile)
    skip = config.skip_reason_for_weight(profile, weight)

    meta: dict[str, Any] = {
        "status": KronosStatus.DISABLED.value,
        "enabled": config.enabled,
        "profile": profile,
        "weight": weight,
        "config": config.to_dict(),
        "deps": deps_health(config),
        "timestamp": datetime.now(UTC).isoformat(),
        "model": config.model,
        "tokenizer": config.tokenizer,
        "device": config.device,
        "lookback": config.resolved_lookback(),
        "pred_len": config.resolved_pred_len(interval),
        "sample_count": config.sample_count,
        "seed": config.seed,
        "inference_ms_total": 0.0,
        "popups": [],
        "note": (
            "Kronos estima contexto futuro OHLCV; no garantiza rentabilidad, "
            "no reemplaza backtest ni Monte Carlo, no conoce el order book."
        ),
    }

    scores = scan_out.get("scores")
    if not isinstance(scores, list):
        meta["status"] = KronosStatus.ERROR.value
        scan_out["kronos"] = meta
        return scan_out

    # Popup legacy
    if skip == KronosSkipReason.LEGACY_WEIGHT_ZERO:
        meta["popups"].append(
            {
                "id": "kronos_legacy_weight_zero",
                "level": "info",
                "title": "Kronos no altera legacy_v1",
                "body": (
                    "Kronos está disponible, pero en legacy_v1 el peso es 0 para "
                    "conservar compatibilidad histórica del score. "
                    "Usá Market Making / Avellaneda / Balanced para forecast de horizonte, "
                    "o activá 'Aplicar Kronos también en legacy' (rompe comparabilidad)."
                ),
            }
        )

    if skip is not None:
        meta["status"] = (
            KronosStatus.SKIPPED_PROFILE.value
            if skip
            in (KronosSkipReason.LEGACY_WEIGHT_ZERO, KronosSkipReason.FUNDING_WEIGHT_ZERO)
            else KronosStatus.DISABLED.value
        )
        meta["skip_reason"] = skip.value
        for row in scores:
            if not isinstance(row, dict):
                continue
            trad = _traditional_from_row(row)
            fields = build_score_fields(
                traditional_score=trad,
                metrics=None,
                profile=profile,
                weight=0.0,
                applied=False,
                skip_reason=skip.value,
            )
            row.update(fields)
            row["kronos_explanation"] = brief_explanation(
                symbol=str(row.get("symbol") or row.get("instrument_id") or "?"),
                profile=profile,
                traditional_score=trad,
                kronos_score=None,
                final_score=trad,
                metrics=None,
            )
        # Orden por final (= traditional)
        scores.sort(
            key=lambda r: (
                -float(r.get("final_score") or r.get("composite") or 0.0)
                if isinstance(r, dict)
                else 0.0,
                str(r.get("instrument_id") if isinstance(r, dict) else ""),
            )
        )
        scan_out["scores"] = scores
        scan_out["kronos"] = meta
        _refresh_selected(scan_out)
        return scan_out

    eng = engine or get_forecast_engine(config)
    health = eng.health()
    meta["engine_health"] = health
    if not health.get("ok"):
        reason = health.get("reason") or KronosSkipReason.DEPS_MISSING.value
        meta["status"] = KronosStatus.UNAVAILABLE.value
        meta["skip_reason"] = reason
        meta["popups"].append(
            {
                "id": "kronos_unavailable",
                "level": "warn",
                "title": "Kronos no aplicado",
                "body": (
                    "Dependencias o modelo no disponibles "
                    f"({reason}). Ranking tradicional intacto. "
                    "Instalá el extra: uv sync --extra kronos"
                ),
            }
        )
        for row in scores:
            if not isinstance(row, dict):
                continue
            trad = _traditional_from_row(row)
            row.update(
                build_score_fields(
                    traditional_score=trad,
                    metrics=None,
                    profile=profile,
                    weight=0.0,
                    applied=False,
                    skip_reason=str(reason),
                )
            )
            row["kronos_explanation"] = brief_explanation(
                symbol=str(row.get("symbol") or row.get("instrument_id") or "?"),
                profile=profile,
                traditional_score=trad,
                kronos_score=None,
                final_score=trad,
                metrics=None,
            )
        scan_out["kronos"] = meta
        return scan_out

    # Preselección top N por score tradicional
    ranked_idx = sorted(
        range(len(scores)),
        key=lambda i: (
            -_traditional_from_row(scores[i]) if isinstance(scores[i], dict) else 0.0,
            str(scores[i].get("instrument_id") if isinstance(scores[i], dict) else ""),
        ),
    )
    top_n = config.resolved_top_n()
    selected_idx = set(ranked_idx[:top_n])
    lookback = config.resolved_lookback()
    pred_len = config.resolved_pred_len(interval)
    cache = (
        KronosDiskCache(cache_dir)
        if config.cache_enabled and cache_dir is not None
        else None
    )

    applied = 0
    failed = 0
    device_used = str(health.get("device") or config.device)
    revision = str(health.get("revision") or "")

    for i, row in enumerate(scores):
        if not isinstance(row, dict):
            continue
        trad = _traditional_from_row(row)
        iid = str(row.get("instrument_id") or "")
        if i not in selected_idx:
            row.update(
                build_score_fields(
                    traditional_score=trad,
                    metrics=None,
                    profile=profile,
                    weight=0.0,
                    applied=False,
                    skip_reason=KronosSkipReason.NOT_IN_TOP_N.value,
                )
            )
            row["kronos_explanation"] = brief_explanation(
                symbol=str(row.get("symbol") or iid),
                profile=profile,
                traditional_score=trad,
                kronos_score=None,
                final_score=trad,
                metrics=None,
            )
            continue

        bars = bars_by_instrument.get(iid)
        if not bars:
            # fallback: buscar por symbol
            sym = str(row.get("symbol") or "")
            bars = bars_by_instrument.get(sym)
        if not bars:
            row.update(
                build_score_fields(
                    traditional_score=trad,
                    metrics=None,
                    profile=profile,
                    weight=0.0,
                    applied=False,
                    skip_reason=KronosSkipReason.INSUFFICIENT_BARS.value,
                )
            )
            failed += 1
            continue

        metrics: KronosMetrics | None = None
        skip_reason: str | None = None
        try:
            req = build_forecast_request(
                iid,
                bars,
                lookback=lookback,
                pred_len=pred_len,
                sample_count=config.sample_count,
                temperature=config.temperature,
                top_p=config.top_p,
                seed=config.seed,
            )
            data_hash = hash_closes(req.lookback_closes)
            ckey = forecast_cache_key(
                symbol=iid,
                interval=interval,
                model=config.model,
                lookback=lookback,
                pred_len=pred_len,
                sample_count=config.sample_count,
                temperature=config.temperature,
                top_p=config.top_p,
                seed=config.seed,
                data_hash=data_hash,
            )
            batch: TrajectoryBatch | None = None
            if cache is not None:
                cached = cache.get(ckey)
                if cached:
                    batch = _trajectories_from_cache(cached)
                    if batch is None:
                        skip_reason = KronosSkipReason.CACHE_CORRUPT.value

            if batch is None:
                result = _forecast_with_timeout(eng, req, config.timeout_seconds)
                if not result.ok or result.trajectories is None:
                    skip_reason = (
                        result.reason.value
                        if result.reason
                        else KronosSkipReason.INFERENCE_FAILED.value
                    )
                    failed += 1
                else:
                    batch = result.trajectories
                    device_used = result.device or device_used
                    revision = result.model_revision or revision
                    if cache is not None:
                        cache.set(
                            ckey,
                            _cache_payload(
                                batch,
                                {
                                    "data_hash": data_hash,
                                    "inference_ms": result.inference_ms,
                                },
                            ),
                        )

            if batch is not None:
                rh, rl = _range_from_bars(list(bars)[-lookback:])
                metrics = compute_kronos_metrics(batch, range_high=rh, range_low=rl)
                applied += 1
                row["kronos_data_hash"] = data_hash
        except KronosError as exc:
            skip_reason = exc.reason.value
            failed += 1
        except Exception as exc:  # noqa: BLE001
            logger.warning("kronos_row_failed %s: %s", iid, exc)
            skip_reason = KronosSkipReason.INFERENCE_FAILED.value
            failed += 1

        fields = build_score_fields(
            traditional_score=trad,
            metrics=metrics,
            profile=profile,
            weight=weight if metrics is not None else 0.0,
            applied=metrics is not None,
            skip_reason=skip_reason,
        )
        row.update(fields)
        row["kronos_explanation"] = brief_explanation(
            symbol=str(row.get("symbol") or iid),
            profile=profile,
            traditional_score=trad,
            kronos_score=fields.get("kronos_score"),  # type: ignore[arg-type]
            final_score=float(fields["final_score"]),
            metrics=metrics,
            rank_improved=None
            if metrics is None
            else float(fields["final_score"]) >= trad,
        )
        row["compatible_strategy"] = profile
        row["kronos_horizon"] = pred_len

    # Re-rank por final_score
    scores.sort(
        key=lambda r: (
            -float(r.get("final_score") or 0.0) if isinstance(r, dict) else 0.0,
            str(r.get("instrument_id") if isinstance(r, dict) else ""),
        )
    )
    scan_out["scores"] = scores
    _refresh_selected(scan_out)

    meta["status"] = (
        KronosStatus.APPLIED.value
        if applied and not failed
        else (KronosStatus.PARTIAL.value if applied else KronosStatus.ERROR.value)
    )
    meta["applied_count"] = applied
    meta["failed_count"] = failed
    meta["device_resolved"] = device_used
    meta["model_revision"] = revision
    meta["inference_ms_total"] = (time.perf_counter() - t0) * 1000.0
    meta["top_n_preselect"] = top_n
    scan_out["kronos"] = meta
    return scan_out


def _forecast_with_timeout(
    eng: ForecastEngine,
    req: Any,
    timeout_seconds: float,
) -> ForecastResult:
    if timeout_seconds <= 0:
        return eng.forecast(req)
    with ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(eng.forecast, req)
        try:
            return fut.result(timeout=timeout_seconds)
        except FuturesTimeout:
            return ForecastResult(
                ok=False,
                trajectories=None,
                reason=KronosSkipReason.TIMEOUT,
                detail=f"timeout>{timeout_seconds}s",
            )


def _refresh_selected(scan_out: dict[str, Any]) -> None:
    scores = scan_out.get("scores")
    top_n = int(scan_out.get("top_n") or 5)
    if not isinstance(scores, list):
        return
    selected = [
        str(r.get("instrument_id"))
        for r in scores[:top_n]
        if isinstance(r, dict) and r.get("instrument_id")
    ]
    scan_out["selected"] = selected
    if "selected_symbols" in scan_out:
        scan_out["selected_symbols"] = [
            str(r.get("symbol") or r.get("instrument_id"))
            for r in scores[:top_n]
            if isinstance(r, dict)
        ]


__all__ = ["apply_kronos_to_scan"]
