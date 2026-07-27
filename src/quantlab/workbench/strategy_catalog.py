"""Catálogo de estrategias workbench (paper + lab + demo Binance) — F27/F115.

Espectro por familias: runnable (backtest/paper/demo) vs stub research.
LIVE producción sigue bloqueado (LIVE_BLOCKED); “real” = paper + demo/testnet
post-unlock con los mismos strategy_id.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from quantlab.core.contracts.strategy import Strategy, StrategyContext
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import EventType
from quantlab.core.types.market import Bar, MarketEvent
from quantlab.core.types.orders import OrderIntent
from quantlab.research.strategies.avellaneda_stoikov import AvellanedaStoikovStrategy
from quantlab.research.strategies.buy_once import BuyOnceStrategy
from quantlab.research.strategies.classic_bar import ClassicBarStrategy
from quantlab.research.strategies.dummy_strategy import DummyStrategy
from quantlab.research.strategies.inventory_mm import InventoryMMStrategy
from quantlab.research.strategies.mm_spectrum import (
    AdaptiveMMStrategy,
    DynamicSpreadMMStrategy,
    MultiLevelMMStrategy,
)
from quantlab.research.strategies.simple_momentum import SimpleMomentumStrategy

# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class StrategyMeta:
    """Metadata de una estrategia del catálogo workbench."""

    id: str
    name: str
    family: str
    tags: tuple[str, ...]
    default_params: Mapping[str, Any]
    description: str = ""
    runnable: bool = True
    factory: str = "classic"  # classic | legacy | mm | stub
    signal_kind: str | None = None


def _m(
    sid: str,
    name: str,
    family: str,
    *,
    tags: tuple[str, ...] = (),
    params: Mapping[str, Any] | None = None,
    description: str = "",
    runnable: bool = True,
    factory: str = "classic",
    signal_kind: str | None = None,
) -> StrategyMeta:
    kind = signal_kind if signal_kind is not None else (sid if factory == "classic" else None)
    return StrategyMeta(
        id=sid,
        name=name,
        family=family,
        tags=tags,
        default_params=dict(params or {"quantity": "1"}),
        description=description,
        runnable=runnable,
        factory=factory,
        signal_kind=kind,
    )


STRATEGY_CATALOG: tuple[StrategyMeta, ...] = (
    # —— Demo legacy ——
    _m(
        "dummy",
        "Dummy",
        "demo",
        tags=("demo",),
        params={"quantity": "0.01", "price": "100.0"},
        description="PLACE fijo en cada barra (demo).",
        factory="legacy",
    ),
    _m(
        "buy_once",
        "Buy Once",
        "demo",
        tags=("demo",),
        params={"quantity": "1"},
        description="Compra una sola vez en la primera barra.",
        factory="legacy",
    ),
    # —— Tendenciales ——
    _m(
        "ma_crossover",
        "Moving Average Crossover",
        "trend",
        tags=("trend",),
        params={"quantity": "1", "fast": 5, "slow": 20},
        description="Cruce SMA rápida/lenta.",
        signal_kind="ma_crossover",
    ),
    _m(
        "ema",
        "EMA Crossover",
        "trend",
        tags=("trend",),
        params={"quantity": "1", "fast": 8, "slow": 21},
        description="Cruce EMA rápida/lenta.",
        signal_kind="ema",
    ),
    _m(
        "donchian_breakout",
        "Donchian Breakout",
        "trend",
        tags=("trend", "breakout"),
        params={"quantity": "1", "channel": 20},
        description="Ruptura de canal de Donchian.",
        signal_kind="donchian_breakout",
    ),
    _m(
        "turtle",
        "Turtle Trading",
        "trend",
        tags=("trend", "breakout"),
        params={"quantity": "1", "entry": 20, "exit": 10},
        description="Entrada/salida estilo Turtle (N-bar).",
        signal_kind="turtle",
    ),
    _m(
        "supertrend",
        "SuperTrend",
        "trend",
        tags=("trend",),
        params={"quantity": "1", "atr_period": 10, "mult": "2"},
        description="SuperTrend simplificado (ATR).",
        signal_kind="supertrend",
    ),
    _m(
        "macd",
        "MACD",
        "trend",
        tags=("trend", "momentum"),
        params={"quantity": "1", "fast": 12, "slow": 26, "signal": 9},
        description="Cruce histograma MACD.",
        signal_kind="macd",
    ),
    # —— Momentum ——
    _m(
        "momentum",
        "Simple Momentum",
        "momentum",
        tags=("momentum",),
        params={"quantity": "1", "lookback": 3},
        description="N closes consecutivos up/down.",
        factory="legacy",
    ),
    _m(
        "rsi_momentum",
        "RSI Momentum",
        "momentum",
        tags=("momentum",),
        params={"quantity": "1", "period": 14, "oversold": "40", "overbought": "70"},
        description="Momentum con RSI (compra oversold suave).",
        signal_kind="rsi_momentum",
    ),
    _m(
        "roc",
        "Rate of Change",
        "momentum",
        tags=("momentum",),
        params={"quantity": "1", "period": 10, "threshold": "0"},
        description="ROC vs umbral.",
        signal_kind="roc",
    ),
    _m(
        "relative_strength",
        "Relative Strength",
        "momentum",
        tags=("momentum",),
        params={"quantity": "1", "period": 20},
        description="Close vs SMA (proxy RS single-asset).",
        signal_kind="relative_strength",
    ),
    _m(
        "breakout",
        "Breakout",
        "momentum",
        tags=("momentum", "breakout"),
        params={"quantity": "1", "lookback": 20},
        description="Ruptura de máximo N barras.",
        signal_kind="breakout",
    ),
    _m(
        "volume_momentum",
        "Volumen + Momentum",
        "momentum",
        tags=("momentum", "volume"),
        params={"quantity": "1", "lookback": 10},
        description="Precio al alza con volumen > promedio.",
        signal_kind="volume_momentum",
    ),
    # —— Mean reversion ——
    _m(
        "bollinger",
        "Bollinger Bands",
        "mean_reversion",
        tags=("mean_reversion",),
        params={"quantity": "1", "period": 20, "k": "2"},
        description="Compra banda inferior / vende superior.",
        signal_kind="bollinger",
    ),
    _m(
        "rsi_reversion",
        "RSI Reversión",
        "mean_reversion",
        tags=("mean_reversion",),
        params={"quantity": "1", "period": 14, "oversold": "30", "overbought": "70"},
        description="Reversión RSI clásica 30/70.",
        signal_kind="rsi_reversion",
    ),
    _m(
        "zscore",
        "Z-Score",
        "mean_reversion",
        tags=("mean_reversion",),
        params={"quantity": "1", "period": 20, "entry_z": "-1.5", "exit_z": "0"},
        description="Z-score vs SMA.",
        signal_kind="zscore",
    ),
    _m(
        "vwap_reversion",
        "VWAP Reversion",
        "mean_reversion",
        tags=("mean_reversion",),
        params={"quantity": "1", "band_pct": "0.005"},
        description="Reversión a VWAP acumulado de sesión.",
        signal_kind="vwap_reversion",
    ),
    _m(
        "cointegration_proxy",
        "Cointegración (proxy)",
        "mean_reversion",
        tags=("mean_reversion", "stats"),
        params={"quantity": "1", "period": 20, "entry_z": "-1.5", "exit_z": "0"},
        description="Proxy single-asset (pares reales → stub cointegration).",
        signal_kind="cointegration_proxy",
    ),
    # —— Market making ——
    _m(
        "inventory_mm",
        "Inventory MM",
        "market_making",
        tags=("mm",),
        params={"quantity": "1", "half_spread": "0.5", "max_pos": "10"},
        description="MM con skew por inventario.",
        factory="mm",
    ),
    _m(
        "avellaneda_stoikov",
        "Avellaneda–Stoikov",
        "market_making",
        tags=("mm",),
        params={
            "quantity": "1",
            "gamma": 0.1,
            "sigma": 0.02,
            "kappa": 1.5,
            "horizon_events": 100,
            "max_pos": "10",
        },
        description="Cotizador AS (MVP simulado).",
        factory="mm",
    ),
    _m(
        "dynamic_spread",
        "Dynamic Spread",
        "market_making",
        tags=("mm",),
        params={
            "quantity": "1",
            "half_spread": "0.5",
            "max_pos": "10",
            "atr_period": 10,
            "vol_mult": "1",
        },
        description="Spread dinámico según volatilidad reciente.",
        factory="mm",
    ),
    _m(
        "multi_level_mm",
        "Multi-Level MM",
        "market_making",
        tags=("mm",),
        params={
            "quantity": "1",
            "half_spread": "0.5",
            "level_step": "0.5",
            "levels": 2,
            "max_pos": "10",
        },
        description="Cotiza varios niveles bid/ask.",
        factory="mm",
    ),
    _m(
        "adaptive_mm",
        "Adaptive MM",
        "market_making",
        tags=("mm",),
        params={
            "quantity": "1",
            "half_spread": "0.5",
            "max_pos": "10",
            "atr_period": 10,
            "vol_mult": "1",
            "inventory_boost": "1.5",
        },
        description="Spread dinámico + skew adaptativo por inventario.",
        factory="mm",
    ),
    # —— Estadísticas (proxies bar-runnable; multi-serie real queda documentado) ——
    _m(
        "pairs_trading",
        "Pairs Trading",
        "stats",
        tags=("stats", "proxy"),
        params={
            "quantity": "1",
            "lag": 5,
            "period": 20,
            "entry_z": "-1.0",
            "exit_z": "0.5",
        },
        description="Proxy: spread close vs close-lag (sin 2ª serie real).",
        signal_kind="pairs_lag",
    ),
    _m(
        "cointegration",
        "Cointegration",
        "stats",
        tags=("stats", "proxy"),
        params={"quantity": "1", "period": 20, "entry_z": "-1.5", "exit_z": "0"},
        description="Proxy mean-reversion vs SMA (Engle-Granger real = futuro).",
        signal_kind="cointegration_proxy",
    ),
    _m(
        "pca",
        "PCA",
        "stats",
        tags=("stats", "proxy"),
        params={
            "quantity": "1",
            "period": 20,
            "w_ret": "0.5",
            "w_range": "0.3",
            "w_vol": "0.2",
            "threshold": "0",
        },
        description="PC1 proxy con pesos fijos sobre ret/rango/vol (sin sklearn).",
        signal_kind="pca_proxy",
    ),
    _m(
        "kalman_filter",
        "Kalman Filter",
        "stats",
        tags=("stats",),
        params={
            "quantity": "1",
            "process_var": "0.001",
            "measure_var": "0.01",
            "entry_z": "-1.0",
            "exit_z": "0",
        },
        description="Kalman 1D sobre precio (hedge ratio multi-serie = futuro).",
        signal_kind="kalman",
    ),
    _m(
        "statistical_arbitrage",
        "Statistical Arbitrage",
        "stats",
        tags=("stats", "proxy"),
        params={"quantity": "1", "period": 20, "entry_z": "-1.5", "exit_z": "0"},
        description="Stat-arb proxy = z-score single-asset.",
        signal_kind="zscore",
    ),
    # —— Machine Learning (score lineal proxy; sin modelo entrenado) ——
    _m(
        "random_forest",
        "Random Forest",
        "ml",
        tags=("ml", "proxy"),
        params={
            "quantity": "1",
            "period": 14,
            "w_mom": "0.5",
            "w_rsi": "0.3",
            "w_vol": "0.2",
            "threshold": "0",
        },
        description="Proxy features (no RF entrenado). Research-only labeling.",
        signal_kind="ml_feature_score",
    ),
    _m(
        "xgboost",
        "XGBoost",
        "ml",
        tags=("ml", "proxy"),
        params={
            "quantity": "1",
            "period": 14,
            "w_mom": "0.45",
            "w_rsi": "0.35",
            "w_vol": "0.2",
            "threshold": "0",
        },
        description="Proxy features (no XGB entrenado).",
        signal_kind="ml_feature_score",
    ),
    _m(
        "lightgbm",
        "LightGBM",
        "ml",
        tags=("ml", "proxy"),
        params={
            "quantity": "1",
            "period": 10,
            "w_mom": "0.4",
            "w_rsi": "0.4",
            "w_vol": "0.2",
            "threshold": "0",
        },
        description="Proxy features (no LightGBM entrenado).",
        signal_kind="ml_feature_score",
    ),
    _m(
        "neural_net",
        "Redes Neuronales",
        "ml",
        tags=("ml", "proxy"),
        params={
            "quantity": "1",
            "period": 20,
            "w_mom": "0.35",
            "w_rsi": "0.35",
            "w_vol": "0.3",
            "threshold": "0",
        },
        description="Proxy features (no NN entrenada).",
        signal_kind="ml_feature_score",
    ),
    _m(
        "reinforcement_learning",
        "Reinforcement Learning",
        "ml",
        tags=("ml", "proxy"),
        params={
            "quantity": "1",
            "period": 14,
            "w_mom": "0.6",
            "w_rsi": "0.2",
            "w_vol": "0.2",
            "threshold": "0",
        },
        description="Proxy score (no agente RL entrenado).",
        signal_kind="ml_feature_score",
    ),
    # —— Multi-activo ——
    _m(
        "sector_rotation",
        "Rotación sectorial",
        "multi_asset",
        tags=("multi_asset",),
        description="Requiere universo multi-símbolo — stub.",
        runnable=False,
        factory="stub",
    ),
    _m(
        "portfolio_momentum",
        "Portfolio Momentum",
        "multi_asset",
        tags=("multi_asset", "momentum", "proxy"),
        params={"quantity": "1", "period": 20},
        description="Proxy single-asset RS (cross-section real = futuro).",
        signal_kind="relative_strength",
    ),
    _m(
        "risk_parity",
        "Risk Parity",
        "multi_asset",
        tags=("multi_asset", "risk"),
        description="Requiere covarianza multi-activo — stub.",
        runnable=False,
        factory="stub",
    ),
    _m(
        "asset_allocation",
        "Asset Allocation",
        "multi_asset",
        tags=("multi_asset",),
        description="Requiere canasta de activos — stub.",
        runnable=False,
        factory="stub",
    ),
    # —— Microestructura (proxies OHLC/volumen; L2 real = futuro) ——
    _m(
        "order_book_imbalance",
        "Order Book Imbalance",
        "microstructure",
        tags=("microstructure", "proxy"),
        params={"quantity": "1", "threshold": "0.2"},
        description="Proxy OHLC imbalance (L2 real = futuro).",
        signal_kind="obi_proxy",
    ),
    _m(
        "queue_position",
        "Queue Position",
        "microstructure",
        tags=("microstructure",),
        description="Posición en cola — requiere L2 — stub.",
        runnable=False,
        factory="stub",
    ),
    _m(
        "flow_toxicity",
        "Flow Toxicity",
        "microstructure",
        tags=("microstructure", "proxy"),
        params={
            "quantity": "1",
            "period": 20,
            "tox_exit": "0.02",
            "tox_entry": "0.005",
        },
        description="Proxy toxicidad ret×volumen.",
        signal_kind="toxicity_proxy",
    ),
    _m(
        "liquidity_detection",
        "Liquidity Detection",
        "microstructure",
        tags=("microstructure", "proxy"),
        params={"quantity": "1", "period": 20, "vol_mult": "1.2"},
        description="Proxy liquidez por volumen relativo.",
        signal_kind="liquidity_proxy",
    ),
    # —— Arbitrage (stubs: multi-venue / funding / basis) ——
    _m(
        "triangular_arb",
        "Triangular Arbitrage",
        "arbitrage",
        tags=("arbitrage",),
        description="Triangular FX/crypto — stub (multi-par).",
        runnable=False,
        factory="stub",
    ),
    _m(
        "cross_exchange_arb",
        "Cross Exchange",
        "arbitrage",
        tags=("arbitrage",),
        description="Arb entre venues — stub (sin multi-venue live).",
        runnable=False,
        factory="stub",
    ),
    _m(
        "funding_arb",
        "Funding Arbitrage",
        "arbitrage",
        tags=("arbitrage",),
        description="Funding perpetual — stub.",
        runnable=False,
        factory="stub",
    ),
    _m(
        "basis_trading",
        "Basis Trading",
        "arbitrage",
        tags=("arbitrage",),
        description="Basis spot/futuro — stub.",
        runnable=False,
        factory="stub",
    ),
    # —— Opciones ——
    _m(
        "volatility_trading",
        "Volatility Trading",
        "options",
        tags=("options", "proxy"),
        params={
            "quantity": "1",
            "atr_period": 14,
            "atr_pct_entry": "0.01",
            "atr_pct_exit": "0.005",
        },
        description="Proxy régimen ATR% (sin cadena de opciones).",
        signal_kind="vol_regime",
    ),
    _m(
        "delta_neutral",
        "Delta Neutral",
        "options",
        tags=("options",),
        description="Delta-neutral — stub (sin greeks).",
        runnable=False,
        factory="stub",
    ),
    _m(
        "gamma_scalping",
        "Gamma Scalping",
        "options",
        tags=("options",),
        description="Gamma scalp — stub.",
        runnable=False,
        factory="stub",
    ),
    _m(
        "covered_calls",
        "Covered Calls",
        "options",
        tags=("options",),
        description="Covered calls — stub.",
        runnable=False,
        factory="stub",
    ),
)

CANONICAL_STRATEGY_IDS: tuple[str, ...] = tuple(m.id for m in STRATEGY_CATALOG)
RUNNABLE_STRATEGY_IDS: tuple[str, ...] = tuple(m.id for m in STRATEGY_CATALOG if m.runnable)

_ALIASES: dict[str, str] = {
    "simple_momentum": "momentum",
    "as": "avellaneda_stoikov",
    "avellaneda": "avellaneda_stoikov",
    "inv_mm": "inventory_mm",
    "inventory": "inventory_mm",
    "ma_cross": "ma_crossover",
    "moving_average_crossover": "ma_crossover",
    "donchian": "donchian_breakout",
    "rsi": "rsi_momentum",
    "bbands": "bollinger",
    "bollinger_bands": "bollinger",
    "vwap": "vwap_reversion",
    "multi_level": "multi_level_mm",
    "adaptive": "adaptive_mm",
    "dynamic_spread_mm": "dynamic_spread",
}

_BY_ID: dict[str, StrategyMeta] = {m.id: m for m in STRATEGY_CATALOG}


def normalize_strategy_id(strategy_id: str) -> str:
    """Normaliza alias → id canónico; valida existencia."""
    if not isinstance(strategy_id, str) or not strategy_id.strip():
        raise ValidationError("strategy_id requerido")
    sid = strategy_id.strip().lower()
    sid = _ALIASES.get(sid, sid)
    if sid not in _BY_ID:
        raise ValidationError(
            f"strategy_id desconocido: {strategy_id!r}; "
            f"disponibles: {', '.join(CANONICAL_STRATEGY_IDS)}"
        )
    return sid


def get_strategy_meta(strategy_id: str) -> StrategyMeta:
    return _BY_ID[normalize_strategy_id(strategy_id)]


def assert_runnable(strategy_id: str) -> str:
    """Fail-closed si la estrategia es stub research."""
    sid = normalize_strategy_id(strategy_id)
    meta = _BY_ID[sid]
    if not meta.runnable:
        raise ValidationError(
            f"strategy_id {sid!r} es stub research (familia={meta.family}) — "
            "aún no ejecutable en backtest/paper/Binance demo. "
            f"Elegí una runnable: {', '.join(RUNNABLE_STRATEGY_IDS)}"
        )
    return sid


def list_strategy_ids() -> list[str]:
    return list(CANONICAL_STRATEGY_IDS)


def list_runnable_strategy_ids() -> list[str]:
    return list(RUNNABLE_STRATEGY_IDS)


def list_strategy_catalog() -> list[dict[str, Any]]:
    """Lista metadata serializable (API / UI)."""
    out: list[dict[str, Any]] = []
    for m in STRATEGY_CATALOG:
        out.append(
            {
                "id": m.id,
                "name": m.name,
                "family": m.family,
                "tags": list(m.tags),
                "default_params": dict(m.default_params),
                "description": m.description,
                "runnable": m.runnable,
                "binance_ready": m.runnable,
            }
        )
    return out


def merge_default_params(
    strategy_id: str, params: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Defaults del catálogo + override del caller."""
    meta = get_strategy_meta(strategy_id)
    merged = dict(meta.default_params)
    if params:
        merged.update(dict(params))
    return merged


def build_strategy(strategy_id: str, params: Mapping[str, Any] | None = None) -> Strategy:
    """Factory research strategies para paper session / lab backtest / demo path."""
    sid = assert_runnable(strategy_id)
    meta = _BY_ID[sid]
    strategy_params = merge_default_params(sid, params)

    if meta.factory == "legacy":
        if sid == "dummy":
            return DummyStrategy(strategy_params)
        if sid == "buy_once":
            return BuyOnceStrategy(strategy_params)
        if sid == "momentum":
            return SimpleMomentumStrategy(strategy_params)
        raise ValidationError(f"legacy factory sin clase: {sid!r}")

    if meta.factory == "mm":
        if sid == "inventory_mm":
            return InventoryMMStrategy(strategy_params)
        if sid == "avellaneda_stoikov":
            return AvellanedaStoikovStrategy(strategy_params)
        if sid == "dynamic_spread":
            return DynamicSpreadMMStrategy(strategy_params)
        if sid == "multi_level_mm":
            return MultiLevelMMStrategy(strategy_params)
        if sid == "adaptive_mm":
            return AdaptiveMMStrategy(strategy_params)
        raise ValidationError(f"mm factory sin clase: {sid!r}")

    if meta.factory == "classic":
        kind = meta.signal_kind or sid
        return ClassicBarStrategy(strategy_params, signal_kind=kind)

    raise ValidationError(f"strategy_id sin factory: {sid!r}")


def is_mm_strategy(strategy_id: str) -> bool:
    meta = get_strategy_meta(strategy_id)
    return "mm" in meta.tags


class BarSyntheticBookAdapter:
    """Adapta estrategias MM al motor bar-based 5A.

    Inyecta ``best_bid`` / ``best_ask`` / ``inventory`` desde ``bar.close``
    (± half_spread) y portfolio. Sin microestructura real.
    """

    def __init__(self, inner: Strategy, *, half_spread: Decimal | None = None) -> None:
        self._inner = inner
        params = inner.get_parameters()
        if half_spread is not None:
            self._half = half_spread
        else:
            self._half = Decimal(str(params.get("half_spread", "0.5")))

    def on_event(self, event: MarketEvent, context: StrategyContext) -> tuple[OrderIntent, ...]:
        close_s = event.payload.get("close") if event.payload else None
        if close_s is None:
            return self._inner.on_event(event, context)
        close = Decimal(str(close_s))
        enriched = self._enrich(context, event.instrument_id, close)
        return self._inner.on_event(event, enriched)

    def on_bar(self, bar: Bar, context: StrategyContext) -> tuple[OrderIntent, ...]:
        enriched = self._enrich(context, bar.instrument_id, bar.close)
        intents = self._inner.on_event(
            MarketEvent(
                event_id=f"adapt-{bar.instrument_id}-{bar.timestamp_close.isoformat()}",
                event_type=EventType.BAR,
                timestamp=bar.timestamp_close,
                instrument_id=bar.instrument_id,
                payload={"timeframe": bar.timeframe, "close": str(bar.close)},
            ),
            enriched,
        )
        if intents:
            return intents
        return self._inner.on_bar(bar, enriched)

    def get_parameters(self) -> dict[str, Any]:
        return self._inner.get_parameters()

    def set_parameters(self, params: dict[str, Any]) -> None:
        self._inner.set_parameters(params)

    def get_state(self) -> dict[str, Any]:
        return self._inner.get_state()

    def reset(self) -> None:
        self._inner.reset()

    def _enrich(
        self, context: StrategyContext, instrument_id: str, mid: Decimal
    ) -> StrategyContext:
        half = self._half
        raw_half = self._inner.get_parameters().get("half_spread", half)
        half = Decimal(str(raw_half))
        # half_spread absoluto (ej. 0.5) rompe alts baratos: escalar a bps del mid.
        if mid > 0 and half / mid > Decimal("0.02"):
            half = mid * Decimal("0.005")
        bid = mid - half
        ask = mid + half
        if bid <= 0:
            bid = mid * Decimal("0.99") if mid > 0 else Decimal("1")
            ask = mid * Decimal("1.01") if mid > 0 else Decimal("2")
        inv = Decimal("0")
        if context.portfolio_state is not None:
            for p in context.portfolio_state.positions:
                if p.instrument_id == instrument_id:
                    inv = p.quantity
                    break
        max_pos = Decimal(str(self._inner.get_parameters().get("max_pos", "10")))
        skew = (inv / max_pos) if max_pos > 0 else Decimal("0")
        merged = {
            **dict(context.parameters),
            **self._inner.get_parameters(),
            "best_bid": str(bid),
            "best_ask": str(ask),
            "inventory": str(inv),
            "inventory_skew": str(skew),
        }
        return StrategyContext(
            clock=context.clock,
            portfolio_state=context.portfolio_state,
            parameters=merged,
        )


def maybe_wrap_for_bar_backtest(strategy_id: str, strategy: Strategy) -> Strategy:
    """Envuelve MM para lab backtest bar-based; resto sin cambio."""
    if is_mm_strategy(strategy_id):
        return BarSyntheticBookAdapter(strategy)
    return strategy
