"""Errores y estados tipados de la capa Kronos (Alpha Scanner)."""

from __future__ import annotations

from enum import StrEnum


class KronosStatus(StrEnum):
    """Estado de aplicación de Kronos en un escaneo."""

    APPLIED = "applied"
    DISABLED = "disabled"
    SKIPPED_PROFILE = "skipped_profile"
    UNAVAILABLE = "unavailable"
    TIMEOUT = "timeout"
    PARTIAL = "partial"
    ERROR = "error"


class KronosSkipReason(StrEnum):
    """Motivo tipado cuando Kronos no aporta métricas (nunca fingir con 0)."""

    DISABLED = "disabled"
    LEGACY_WEIGHT_ZERO = "legacy_weight_zero"
    FUNDING_WEIGHT_ZERO = "funding_weight_zero"
    DEPS_MISSING = "deps_missing"
    MODEL_LOAD_FAILED = "model_load_failed"
    OOM = "out_of_memory"
    TIMEOUT = "timeout"
    INSUFFICIENT_BARS = "insufficient_bars"
    INVALID_OHLCV = "invalid_ohlcv"
    NOT_IN_TOP_N = "not_in_top_n"
    INFERENCE_FAILED = "inference_failed"
    CACHE_CORRUPT = "cache_corrupt"
    NO_INTERNET = "no_internet"
    USER_OVERRIDE_OFF = "user_override_off"


class KronosError(Exception):
    """Fallo de la capa Kronos (no debe tumbar el Scanner)."""

    def __init__(self, reason: KronosSkipReason, message: str) -> None:
        self.reason = reason
        super().__init__(message)


__all__ = ["KronosError", "KronosSkipReason", "KronosStatus"]
