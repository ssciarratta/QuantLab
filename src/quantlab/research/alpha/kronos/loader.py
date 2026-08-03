"""Carga lazy del vendor Kronos + torch (sin import duro al arrancar QuantLab)."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

from quantlab.research.alpha.kronos.config import KronosConfig
from quantlab.research.alpha.kronos.errors import KronosError, KronosSkipReason
from quantlab.research.alpha.kronos.protocol import ForecastEngine, NullForecastEngine

logger = logging.getLogger(__name__)

_ENGINE: ForecastEngine | None = None
_ENGINE_KEY: str | None = None


def default_vendor_path() -> Path:
    # src/quantlab/research/alpha/kronos/loader.py → repo root
    return Path(__file__).resolve().parents[5] / "third_party" / "kronos"


def resolve_device(pref: str) -> str:
    pref_l = (pref or "auto").strip().lower()
    if pref_l == "cpu":
        return "cpu"
    try:
        import torch  # type: ignore[import-untyped]

        if pref_l == "cuda" and torch.cuda.is_available():
            return "cuda:0"
        if pref_l == "auto" and torch.cuda.is_available():
            return "cuda:0"
    except Exception:  # noqa: BLE001
        pass
    return "cpu"


def ensure_vendor_on_path(vendor: Path) -> None:
    s = str(vendor.resolve())
    if s not in sys.path:
        sys.path.insert(0, s)


def check_kronos_deps(vendor: Path) -> KronosSkipReason | None:
    if not vendor.is_dir():
        return KronosSkipReason.DEPS_MISSING
    try:
        import pandas  # noqa: F401  # type: ignore[import-untyped]
        import torch  # noqa: F401  # type: ignore[import-untyped]
    except ImportError:
        return KronosSkipReason.DEPS_MISSING
    return None


def get_forecast_engine(config: KronosConfig) -> ForecastEngine:
    """Singleton lazy. Fallos → NullForecastEngine tipado."""
    global _ENGINE, _ENGINE_KEY
    if not config.enabled:
        return NullForecastEngine(KronosSkipReason.DISABLED)

    # Evita UnicodeEncodeError de barras tqdm en consolas ASCII (Windows).
    os.environ.setdefault("TQDM_DISABLE", "0")
    os.environ["TQDM_ASCII"] = "1"

    vendor = Path(config.vendor_path) if config.vendor_path else default_vendor_path()
    key = f"{config.model}|{config.tokenizer}|{config.device}|{vendor}"
    if _ENGINE is not None and key == _ENGINE_KEY:
        return _ENGINE

    missing = check_kronos_deps(vendor)
    if missing is not None:
        eng: ForecastEngine = NullForecastEngine(missing)
        _ENGINE, _ENGINE_KEY = eng, key
        return eng

    try:
        from quantlab.research.alpha.kronos.forecast import KronosTorchEngine

        eng = KronosTorchEngine(config, vendor=vendor)
        _ENGINE, _ENGINE_KEY = eng, key
        return eng
    except KronosError as exc:
        logger.warning("kronos_load_failed reason=%s detail=%s", exc.reason, exc)
        eng = NullForecastEngine(exc.reason)
        _ENGINE, _ENGINE_KEY = eng, key
        return eng
    except Exception as exc:  # noqa: BLE001
        logger.warning("kronos_load_unexpected: %s", exc)
        eng = NullForecastEngine(KronosSkipReason.MODEL_LOAD_FAILED)
        _ENGINE, _ENGINE_KEY = eng, key
        return eng


def reset_engine_for_tests() -> None:
    global _ENGINE, _ENGINE_KEY
    _ENGINE = None
    _ENGINE_KEY = None


def deps_health(config: KronosConfig | None = None) -> dict[str, Any]:
    cfg = config or KronosConfig(enabled=True)
    vendor = Path(cfg.vendor_path) if cfg.vendor_path else default_vendor_path()
    reason = check_kronos_deps(vendor)
    return {
        "vendor_path": str(vendor),
        "vendor_exists": vendor.is_dir(),
        "deps_ok": reason is None,
        "reason": None if reason is None else reason.value,
        "device_resolved": resolve_device(cfg.device),
    }


__all__ = [
    "check_kronos_deps",
    "default_vendor_path",
    "deps_health",
    "ensure_vendor_on_path",
    "get_forecast_engine",
    "reset_engine_for_tests",
    "resolve_device",
]
