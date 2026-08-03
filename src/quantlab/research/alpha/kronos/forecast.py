"""Motor Kronos (torch) detrás del Protocol — import lazy desde loader."""

from __future__ import annotations

import logging
import math
import time
from pathlib import Path
from typing import Any

from quantlab.research.alpha.kronos.config import KronosConfig
from quantlab.research.alpha.kronos.errors import KronosError, KronosSkipReason
from quantlab.research.alpha.kronos.loader import ensure_vendor_on_path, resolve_device
from quantlab.research.alpha.kronos.protocol import (
    ForecastRequest,
    ForecastResult,
    TrajectoryBatch,
)

logger = logging.getLogger(__name__)


class KronosTorchEngine:
    """Envuelve KronosPredictor del vendor shiyu-coder/Kronos."""

    def __init__(self, config: KronosConfig, *, vendor: Path) -> None:
        self.config = config
        self.vendor = vendor
        self.device = resolve_device(config.device)
        self.model_revision = ""
        self._predictor: Any = None
        self._load()

    def _load(self) -> None:
        ensure_vendor_on_path(self.vendor)
        try:
            import torch  # type: ignore[import-untyped]
            from model import Kronos, KronosPredictor, KronosTokenizer  # type: ignore
        except ImportError as exc:
            raise KronosError(
                KronosSkipReason.DEPS_MISSING,
                f"torch/vendor Kronos no importable: {exc}",
            ) from exc
        try:
            tokenizer = KronosTokenizer.from_pretrained(self.config.tokenizer)
            model = Kronos.from_pretrained(self.config.model)
            self._predictor = KronosPredictor(
                model,
                tokenizer,
                device=self.device,
                max_context=self.config.max_context,
            )
            rev = getattr(model, "config", None)
            self.model_revision = str(getattr(rev, "_name_or_path", self.config.model))
            _ = torch
        except Exception as exc:  # noqa: BLE001
            msg = str(exc).lower()
            if "memory" in msg or "out of memory" in msg:
                raise KronosError(KronosSkipReason.OOM, str(exc)) from exc
            if "connection" in msg or "huggingface" in msg or "hub" in msg:
                raise KronosError(KronosSkipReason.NO_INTERNET, str(exc)) from exc
            raise KronosError(KronosSkipReason.MODEL_LOAD_FAILED, str(exc)) from exc

    def health(self) -> dict[str, Any]:
        return {
            "ok": self._predictor is not None,
            "engine": "kronos_torch",
            "device": self.device,
            "model": self.config.model,
            "tokenizer": self.config.tokenizer,
            "revision": self.model_revision,
        }

    def forecast(self, request: ForecastRequest) -> ForecastResult:
        if self._predictor is None:
            return ForecastResult(
                ok=False,
                trajectories=None,
                reason=KronosSkipReason.MODEL_LOAD_FAILED,
                detail="predictor no cargado",
            )
        t0 = time.perf_counter()
        try:
            batch = self._predict_trajectories(request)
        except KronosError as exc:
            return ForecastResult(
                ok=False,
                trajectories=None,
                reason=exc.reason,
                detail=str(exc),
                inference_ms=(time.perf_counter() - t0) * 1000.0,
                device=self.device,
                model_revision=self.model_revision,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("kronos_inference_failed: %s", exc)
            return ForecastResult(
                ok=False,
                trajectories=None,
                reason=KronosSkipReason.INFERENCE_FAILED,
                detail=str(exc),
                inference_ms=(time.perf_counter() - t0) * 1000.0,
                device=self.device,
                model_revision=self.model_revision,
            )
        return ForecastResult(
            ok=True,
            trajectories=batch,
            inference_ms=(time.perf_counter() - t0) * 1000.0,
            device=self.device,
            model_revision=self.model_revision,
        )

    def _predict_trajectories(self, request: ForecastRequest) -> TrajectoryBatch:
        import pandas as pd  # type: ignore[import-untyped]

        n = len(request.lookback_closes)
        if n < 8:
            raise KronosError(KronosSkipReason.INSUFFICIENT_BARS, f"lookback={n}")

        x_df = pd.DataFrame(
            {
                "open": list(request.lookback_opens),
                "high": list(request.lookback_highs),
                "low": list(request.lookback_lows),
                "close": list(request.lookback_closes),
                "volume": list(request.lookback_volumes),
                "amount": list(request.lookback_amounts),
            }
        )
        # Series (no DatetimeIndex): KronosPredictor usa .dt en timestamps.
        x_ts = pd.Series(pd.to_datetime(list(request.timestamps_ns), unit="ns"))
        # timestamps futuros sintéticos a partir del delta mediano
        if n >= 2:
            deltas = [
                request.timestamps_ns[i] - request.timestamps_ns[i - 1]
                for i in range(1, n)
                if request.timestamps_ns[i] > request.timestamps_ns[i - 1]
            ]
            step = int(sorted(deltas)[len(deltas) // 2]) if deltas else 3_600_000_000_000
        else:
            step = 3_600_000_000_000
        last = request.timestamps_ns[-1]
        y_ns = [last + step * (i + 1) for i in range(request.pred_len)]
        y_ts = pd.Series(pd.to_datetime(y_ns, unit="ns"))

        opens: list[tuple[float, ...]] = []
        highs: list[tuple[float, ...]] = []
        lows: list[tuple[float, ...]] = []
        closes: list[tuple[float, ...]] = []
        volumes: list[tuple[float, ...]] = []

        # sample_count trayectorias independientes (sample_count=1 cada llamada)
        for s in range(max(1, request.sample_count)):
            try:
                import torch  # type: ignore[import-untyped]

                torch.manual_seed(request.seed + s)
            except Exception:  # noqa: BLE001
                pass
            pred = self._predictor.predict(
                df=x_df,
                x_timestamp=x_ts,
                y_timestamp=y_ts,
                pred_len=request.pred_len,
                T=request.temperature,
                top_p=request.top_p,
                sample_count=1,
            )
            opens.append(tuple(float(x) for x in pred["open"].tolist()))
            highs.append(tuple(float(x) for x in pred["high"].tolist()))
            lows.append(tuple(float(x) for x in pred["low"].tolist()))
            closes.append(tuple(float(x) for x in pred["close"].tolist()))
            if "volume" in pred.columns:
                volumes.append(tuple(float(x) for x in pred["volume"].tolist()))

            # Validación rápida NaN
            if any(not math.isfinite(c) for c in closes[-1]):
                raise KronosError(KronosSkipReason.INVALID_OHLCV, "NaN en forecast")

        return TrajectoryBatch(
            opens=tuple(opens),
            highs=tuple(highs),
            lows=tuple(lows),
            closes=tuple(closes),
            volumes=tuple(volumes) if volumes else None,
            meta={"sample_count": len(closes), "pred_len": request.pred_len},
        )


__all__ = ["KronosTorchEngine"]
