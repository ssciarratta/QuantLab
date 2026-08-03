"""Configuración explícita Kronos-inside-Scanner."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from quantlab.research.alpha.kronos.errors import KronosSkipReason
from quantlab.research.alpha.profiles import (
    PROFILE_AVELLANEDA_STOIKOV,
    PROFILE_BALANCED,
    PROFILE_FUNDING,
    PROFILE_LEGACY_V1,
    PROFILE_MARKET_MAKING,
    PROFILE_MEAN_REVERSION,
    PROFILE_MOMENTUM,
    PROFILE_OPTIONS,
    PROFILE_TREND,
)

# Pesos por perfil (conservadores). legacy/funding = 0 por diseño.
DEFAULT_KRONOS_WEIGHT_BY_PROFILE: dict[str, float] = {
    PROFILE_LEGACY_V1: 0.0,
    "legacy": 0.0,
    PROFILE_FUNDING: 0.0,
    "stats": 0.0,
    "arbitrage": 0.0,
    PROFILE_MOMENTUM: 0.15,
    PROFILE_TREND: 0.15,
    PROFILE_BALANCED: 0.15,
    "ml": 0.15,
    "multi_asset": 0.15,
    PROFILE_MEAN_REVERSION: 0.20,
    PROFILE_AVELLANEDA_STOIKOV: 0.20,
    PROFILE_MARKET_MAKING: 0.25,
    "microstructure": 0.25,
    PROFILE_OPTIONS: 0.10,
}

KRONOS_MAX_CONTEXT = 512
KRONOS_TOP_N_MAX = 30
KRONOS_TOP_N_DEFAULT = 20


@dataclass(frozen=True, slots=True)
class KronosConfig:
    """Parámetros de inferencia / scoring Kronos (visibles y configurables)."""

    enabled: bool = True
    model: str = "NeoQuasar/Kronos-small"
    tokenizer: str = "NeoQuasar/Kronos-Tokenizer-base"
    device: str = "auto"  # auto | cpu | cuda
    top_n: int = KRONOS_TOP_N_DEFAULT
    lookback: int = 256
    pred_len: int | None = None  # None → alineado al TF (default 12)
    sample_count: int = 4
    temperature: float = 1.0
    top_p: float = 0.9
    weight: float | None = None  # None → tabla por perfil
    legacy_override: bool = False  # si True y legacy, peso mínimo 0.05
    timeout_seconds: float = 120.0
    cache_enabled: bool = True
    seed: int = 42
    max_context: int = KRONOS_MAX_CONTEXT
    vendor_path: str | None = None
    weights_by_profile: dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_KRONOS_WEIGHT_BY_PROFILE)
    )

    def resolved_pred_len(self, interval: str | None = None) -> int:
        if self.pred_len is not None and self.pred_len > 0:
            return int(self.pred_len)
        # Alineado al TF: horizonte corto de "seguir siendo adecuada".
        _ = interval
        return 12

    def resolved_lookback(self) -> int:
        return max(8, min(int(self.lookback), int(self.max_context)))

    def resolved_top_n(self) -> int:
        return max(1, min(int(self.top_n), KRONOS_TOP_N_MAX))

    def weight_for_profile(self, profile: str) -> float:
        if self.weight is not None:
            return float(max(0.0, min(1.0, self.weight)))
        key = (profile or "").strip().lower()
        base = float(self.weights_by_profile.get(key, 0.15))
        if key in (PROFILE_LEGACY_V1, "legacy"):
            if self.legacy_override:
                return 0.05
            return 0.0
        return float(max(0.0, min(1.0, base)))

    def skip_reason_for_weight(self, profile: str, weight: float) -> KronosSkipReason | None:
        if not self.enabled:
            return KronosSkipReason.DISABLED
        if weight <= 0.0:
            key = (profile or "").strip().lower()
            if key in (PROFILE_LEGACY_V1, "legacy") and not self.legacy_override:
                return KronosSkipReason.LEGACY_WEIGHT_ZERO
            if key in (PROFILE_FUNDING, "stats", "arbitrage"):
                return KronosSkipReason.FUNDING_WEIGHT_ZERO
            return KronosSkipReason.DISABLED
        return None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["resolved_lookback"] = self.resolved_lookback()
        d["resolved_top_n"] = self.resolved_top_n()
        return d


def kronos_config_from_mapping(raw: dict[str, Any] | None) -> KronosConfig:
    """Parsea body API / flags UI → KronosConfig (defaults seguros)."""
    if not raw:
        return KronosConfig()
    enabled = raw.get("kronos_enabled", raw.get("enabled", True))
    if isinstance(enabled, str):
        enabled = enabled.strip().lower() in ("1", "true", "yes", "on")
    pred = raw.get("kronos_pred_len", raw.get("pred_len"))
    pred_len: int | None = (
        None if pred is None or pred == "" or pred == "auto" else int(pred)
    )
    weight_raw = raw.get("kronos_weight", raw.get("weight"))
    weight = float(weight_raw) if weight_raw is not None else None
    top_n = int(raw.get("kronos_top_n", raw.get("top_n", KRONOS_TOP_N_DEFAULT)))
    return KronosConfig(
        enabled=bool(enabled),
        model=str(raw.get("kronos_model", raw.get("model", "NeoQuasar/Kronos-small"))),
        tokenizer=str(
            raw.get(
                "kronos_tokenizer",
                raw.get("tokenizer", "NeoQuasar/Kronos-Tokenizer-base"),
            )
        ),
        device=str(raw.get("kronos_device", raw.get("device", "auto"))),
        top_n=top_n,
        lookback=int(raw.get("kronos_lookback", raw.get("lookback", 256))),
        pred_len=pred_len,
        sample_count=int(raw.get("kronos_sample_count", raw.get("sample_count", 4))),
        temperature=float(raw.get("kronos_temperature", raw.get("temperature", 1.0))),
        top_p=float(raw.get("kronos_top_p", raw.get("top_p", 0.9))),
        weight=weight,
        legacy_override=bool(
            raw.get("kronos_legacy_override", raw.get("legacy_override", False))
        ),
        timeout_seconds=float(
            raw.get("kronos_timeout_seconds", raw.get("timeout_seconds", 120.0))
        ),
        cache_enabled=bool(raw.get("kronos_cache_enabled", raw.get("cache_enabled", True))),
        seed=int(raw.get("kronos_seed", raw.get("seed", 42))),
        max_context=int(raw.get("kronos_max_context", raw.get("max_context", 512))),
        vendor_path=(
            str(raw["kronos_vendor_path"])
            if raw.get("kronos_vendor_path")
            else (str(raw["vendor_path"]) if raw.get("vendor_path") else None)
        ),
    )


__all__ = [
    "DEFAULT_KRONOS_WEIGHT_BY_PROFILE",
    "KRONOS_MAX_CONTEXT",
    "KRONOS_TOP_N_DEFAULT",
    "KRONOS_TOP_N_MAX",
    "KronosConfig",
    "kronos_config_from_mapping",
]
