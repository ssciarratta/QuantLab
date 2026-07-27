"""Contratos tipados Monte Carlo — evolucionan el simulador Fase 11.

Reglas:
- No inventar valores: ausente → None (UI: \"No disponible\").
- Nunca usar 0 como sentinel de \"no disponible\".
- Solo exponer métodos realmente implementados en ``MonteCarloSimulator``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from quantlab.core.exceptions import ValidationError

# Versión de contrato enriquecido (persistencia puede ir un paso atrás en schema_version).
MONTECARLO_CONTRACT_VERSION = "mc-context-v2"
METHOD_DISCLAIMER = (
    "Monte Carlo mide sensibilidad y dispersión bajo los supuestos elegidos. "
    "No predice precios futuros."
)


class MonteCarloMethod(StrEnum):
    """Métodos implementados. No listar stubs."""

    PRICE_SHOCK_RERUN = "price_shock_rerun"


class MonteCarloDistribution(StrEnum):
    """Distribuciones usadas por el método implementado."""

    GAUSSIAN = "gaussian"


IMPLEMENTED_METHODS: frozenset[MonteCarloMethod] = frozenset(
    {MonteCarloMethod.PRICE_SHOCK_RERUN}
)

METHOD_EXPLANATIONS: dict[MonteCarloMethod, str] = {
    MonteCarloMethod.PRICE_SHOCK_RERUN: (
        "Perturba OHLC de cada vela con un shock multiplicativo gaussiano "
        "(σ = noise_bps / 10000) y re-ejecuta el backtester completo por escenario. "
        "Agrega equities finales (media, desvío, IC de la media)."
    ),
}


def unavailable_label() -> str:
    """Texto UI canónico cuando un campo es None."""
    return "No disponible"


@dataclass(frozen=True, slots=True)
class MonteCarloExperimentContext:
    """Contexto trazable Scan → Instrumento → Backtest → Monte Carlo.

    Todos los campos opcionales son None si no hay dato real.
    """

    run_id: str | None = None
    session_id: str | None = None
    scan_id: str | None = None
    backtest_id: str | None = None
    strategy_id: str | None = None
    strategy_name: str | None = None
    strategy_params_hash: str | None = None
    strategy_config_id: str | None = None
    venue: str | None = None
    network: str | None = None
    symbols: tuple[str, ...] | None = None
    market_type: str | None = None
    timeframe: str | None = None
    dataset_id: str | None = None
    dataset_hash: str | None = None
    dataset_source: str | None = None
    initial_equity: float | None = None
    fee_model: str | None = None
    slippage_model: str | None = None
    funding_model: str | None = None
    code_commit: str | None = None
    created_at: datetime | None = None
    orphan_technical_mode: bool = False
    orphan_warning: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "session_id": self.session_id,
            "scan_id": self.scan_id,
            "backtest_id": self.backtest_id,
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "strategy_params_hash": self.strategy_params_hash,
            "strategy_config_id": self.strategy_config_id,
            "venue": self.venue,
            "network": self.network,
            "symbols": list(self.symbols) if self.symbols is not None else None,
            "market_type": self.market_type,
            "timeframe": self.timeframe,
            "dataset_id": self.dataset_id,
            "dataset_hash": self.dataset_hash,
            "dataset_source": self.dataset_source,
            "initial_equity": self.initial_equity,
            "fee_model": self.fee_model,
            "slippage_model": self.slippage_model,
            "funding_model": self.funding_model,
            "code_commit": self.code_commit,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "orphan_technical_mode": self.orphan_technical_mode,
            "orphan_warning": self.orphan_warning,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> MonteCarloExperimentContext:
        if not raw:
            return cls()
        symbols_raw = raw.get("symbols")
        symbols: tuple[str, ...] | None
        if symbols_raw is None:
            symbols = None
        elif isinstance(symbols_raw, (list, tuple)):
            symbols = tuple(str(s) for s in symbols_raw)
        else:
            symbols = None
        created = raw.get("created_at")
        created_at: datetime | None
        if isinstance(created, datetime):
            created_at = created
        elif isinstance(created, str) and created.strip():
            created_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
        else:
            created_at = None
        initial = raw.get("initial_equity")
        initial_equity: float | None
        if initial is None:
            initial_equity = None
        elif isinstance(initial, (int, float)) and not isinstance(initial, bool):
            initial_equity = float(initial)
        else:
            initial_equity = None
        return cls(
            run_id=_opt_str(raw.get("run_id")),
            session_id=_opt_str(raw.get("session_id")),
            scan_id=_opt_str(raw.get("scan_id")),
            backtest_id=_opt_str(raw.get("backtest_id")),
            strategy_id=_opt_str(raw.get("strategy_id")),
            strategy_name=_opt_str(raw.get("strategy_name")),
            strategy_params_hash=_opt_str(raw.get("strategy_params_hash")),
            strategy_config_id=_opt_str(raw.get("strategy_config_id")),
            venue=_opt_str(raw.get("venue")),
            network=_opt_str(raw.get("network")),
            symbols=symbols,
            market_type=_opt_str(raw.get("market_type")),
            timeframe=_opt_str(raw.get("timeframe")),
            dataset_id=_opt_str(raw.get("dataset_id")),
            dataset_hash=_opt_str(raw.get("dataset_hash")),
            dataset_source=_opt_str(raw.get("dataset_source")),
            initial_equity=initial_equity,
            fee_model=_opt_str(raw.get("fee_model")),
            slippage_model=_opt_str(raw.get("slippage_model")),
            funding_model=_opt_str(raw.get("funding_model")),
            code_commit=_opt_str(raw.get("code_commit")),
            created_at=created_at,
            orphan_technical_mode=bool(raw.get("orphan_technical_mode", False)),
            orphan_warning=_opt_str(raw.get("orphan_warning")),
        )


@dataclass(frozen=True, slots=True)
class MonteCarloConfig:
    """Configuración del experimento MC.

    ``n_bars`` / ``dataset_bar_count``: cantidad de velas del dataset de entrada
    (en lab sintético: velas 1m). No es el número de escenarios.
    """

    method: MonteCarloMethod = MonteCarloMethod.PRICE_SHOCK_RERUN
    n_scenarios: int = 50
    n_bars: int = 16
    seed: int = 42
    ci_level: float = 0.95
    noise_bps: float = 10.0
    distribution: MonteCarloDistribution = MonteCarloDistribution.GAUSSIAN
    bootstrap_block_size: int | None = None
    perturb_ohlc: bool = True
    perturb_volume: bool = False
    preserve_timestamps: bool = True
    preserve_instrument_id: bool = True
    as_of_time: datetime | None = None
    persist_result: bool = True
    # Alias semántico para UI (mismo valor que n_bars).
    dataset_bar_count: int | None = None

    def __post_init__(self) -> None:
        if self.method not in IMPLEMENTED_METHODS:
            raise ValidationError(
                f"método MC no implementado: {self.method!r}; "
                f"disponibles={[m.value for m in IMPLEMENTED_METHODS]}"
            )
        if self.n_scenarios < 2:
            raise ValidationError("n_scenarios >= 2")
        if self.n_bars < 1:
            raise ValidationError("n_bars >= 1")
        if self.noise_bps < 0:
            raise ValidationError("noise_bps debe ser >= 0")
        if not (0.0 < self.ci_level < 1.0):
            raise ValidationError("ci_level debe estar en (0, 1)")
        if self.bootstrap_block_size is not None:
            raise ValidationError(
                "bootstrap_block_size no aplica al método price_shock_rerun "
                "(block bootstrap no implementado)"
            )
        if self.dataset_bar_count is not None and self.dataset_bar_count != self.n_bars:
            raise ValidationError("dataset_bar_count debe coincidir con n_bars si se informa")

    @property
    def effective_bar_count(self) -> int:
        return self.n_bars

    @property
    def method_explanation(self) -> str:
        return METHOD_EXPLANATIONS[self.method]

    @property
    def disclaimer(self) -> str:
        return METHOD_DISCLAIMER

    def bar_horizon_label(self, timeframe: str | None) -> str:
        """Etiqueta precisa para UI (evita \"Bars\" ambiguo)."""
        tf = timeframe or "desconocido"
        n = self.effective_bar_count
        dur = _duration_hint(n, tf)
        base = f"{n} velas del dataset ({tf})"
        return f"{base}; horizonte ≈ {dur}" if dur else base

    def to_dict(self) -> dict[str, Any]:
        return {
            "method": self.method.value,
            "method_explanation": self.method_explanation,
            "disclaimer": self.disclaimer,
            "n_scenarios": self.n_scenarios,
            "n_bars": self.n_bars,
            "dataset_bar_count": self.effective_bar_count,
            "seed": self.seed,
            "ci_level": self.ci_level,
            "noise_bps": self.noise_bps,
            "distribution": self.distribution.value,
            "bootstrap_block_size": self.bootstrap_block_size,
            "perturb_ohlc": self.perturb_ohlc,
            "perturb_volume": self.perturb_volume,
            "preserve_timestamps": self.preserve_timestamps,
            "preserve_instrument_id": self.preserve_instrument_id,
            "as_of_time": self.as_of_time.isoformat() if self.as_of_time else None,
            "persist_result": self.persist_result,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> MonteCarloConfig:
        if not raw:
            return cls()
        method_raw = raw.get("method", MonteCarloMethod.PRICE_SHOCK_RERUN.value)
        dist_raw = raw.get("distribution", MonteCarloDistribution.GAUSSIAN.value)
        as_of = raw.get("as_of_time")
        as_of_time: datetime | None
        if isinstance(as_of, datetime):
            as_of_time = as_of
        elif isinstance(as_of, str) and as_of.strip():
            as_of_time = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
        else:
            as_of_time = None
        n_bars = int(raw.get("n_bars", raw.get("dataset_bar_count", 16)))
        return cls(
            method=MonteCarloMethod(str(method_raw)),
            n_scenarios=int(raw.get("n_scenarios", 50)),
            n_bars=n_bars,
            seed=int(raw.get("seed", 42)),
            ci_level=float(raw.get("ci_level", 0.95)),
            noise_bps=float(raw.get("noise_bps", 10.0)),
            distribution=MonteCarloDistribution(str(dist_raw)),
            bootstrap_block_size=(
                int(raw["bootstrap_block_size"])
                if raw.get("bootstrap_block_size") is not None
                else None
            ),
            perturb_ohlc=bool(raw.get("perturb_ohlc", True)),
            perturb_volume=bool(raw.get("perturb_volume", False)),
            preserve_timestamps=bool(raw.get("preserve_timestamps", True)),
            preserve_instrument_id=bool(raw.get("preserve_instrument_id", True)),
            as_of_time=as_of_time,
            persist_result=bool(raw.get("persist_result", True)),
            dataset_bar_count=None,
        )


@dataclass(frozen=True, slots=True)
class MonteCarloMetrics:
    """Métricas derivadas. Campos None si los datos no alcanzan.

    Drawdown / path metrics solo si hay trayectorias de equity.
    Si solo hay equities finales, ``paths_available=False``.
    """

    mean_equity: float | None = None
    std_equity: float | None = None
    ci_low: float | None = None
    ci_high: float | None = None
    ci_level: float | None = None
    ci_kind: str = "wald_mean"  # no confundir con percentiles de escenarios
    median_equity: float | None = None
    p05_equity: float | None = None
    p95_equity: float | None = None
    mean_return_pct: float | None = None
    # Fracciones 0..1 desde final_equities vs initial_equity (None si no hay datos).
    prob_profit: float | None = None  # final > initial
    prob_loss: float | None = None  # final < initial
    prob_above_initial: float | None = None  # final >= initial
    max_drawdown_mean: float | None = None
    max_drawdown_p95: float | None = None
    paths_available: bool = False
    finals_only: bool = True
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mean_equity": self.mean_equity,
            "std_equity": self.std_equity,
            "ci_low": self.ci_low,
            "ci_high": self.ci_high,
            "ci_level": self.ci_level,
            "ci_kind": self.ci_kind,
            "median_equity": self.median_equity,
            "p05_equity": self.p05_equity,
            "p95_equity": self.p95_equity,
            "mean_return_pct": self.mean_return_pct,
            "prob_profit": self.prob_profit,
            "prob_loss": self.prob_loss,
            "prob_above_initial": self.prob_above_initial,
            "max_drawdown_mean": self.max_drawdown_mean,
            "max_drawdown_p95": self.max_drawdown_p95,
            "paths_available": self.paths_available,
            "finals_only": self.finals_only,
            "notes": list(self.notes),
        }


def _opt_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        return s if s else None
    return str(value)


def _duration_hint(n_bars: int, timeframe: str) -> str | None:
    tf = timeframe.strip().lower()
    if tf.endswith("m") and tf[:-1].isdigit():
        minutes = int(tf[:-1]) * n_bars
        if minutes < 60:
            return f"{minutes} min"
        hours = minutes / 60.0
        return f"{hours:.1f} h".replace(".0 h", " h")
    if tf.endswith("h") and tf[:-1].isdigit():
        hours = int(tf[:-1]) * n_bars
        return f"{hours} h"
    if tf.endswith("d") and tf[:-1].isdigit():
        days = int(tf[:-1]) * n_bars
        return f"{days} d"
    return None
