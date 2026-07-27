"""Estrategias bar-based classic (señal long/flat) — espectro F115.

Research-safe: producen OrderIntent; ejecución venue solo vía paper / demo
post-unlock (LIVE_BLOCKED). Sin dependencias ML ni L2.
"""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from typing import Any

from quantlab.core.contracts.strategy import StrategyContext
from quantlab.core.types.enums import IntentType, OrderSide, OrderType, TimeInForce
from quantlab.core.types.market import Bar, MarketEvent
from quantlab.core.types.orders import OrderIntent

SignalFn = Callable[["ClassicBarStrategy", Bar], int]
# Señal: 1 = long, 0 = flat, -1 = salir a flat (mismo que 0 en long-only)


def _sma(values: list[Decimal], n: int) -> Decimal | None:
    if n <= 0 or len(values) < n:
        return None
    window = values[-n:]
    return sum(window, Decimal("0")) / Decimal(n)


def _ema_update(prev: Decimal | None, price: Decimal, n: int) -> Decimal:
    if n <= 0:
        return price
    alpha = Decimal("2") / (Decimal(n) + Decimal("1"))
    if prev is None:
        return price
    return alpha * price + (Decimal("1") - alpha) * prev


def _noop(bar: Bar, intent_id: str = "noop") -> tuple[OrderIntent, ...]:
    return (
        OrderIntent(
            intent_id=intent_id,
            intent_type=IntentType.NO_ACTION,
            instrument_id=bar.instrument_id,
        ),
    )


class ClassicBarStrategy:
    """Long-only bar strategy dirigida por ``signal_kind`` del catálogo."""

    def __init__(
        self,
        parameters: dict[str, Any] | None = None,
        *,
        signal_kind: str = "momentum",
    ) -> None:
        self._parameters = dict(parameters or {})
        self._signal_kind = signal_kind
        self._closes: list[Decimal] = []
        self._highs: list[Decimal] = []
        self._lows: list[Decimal] = []
        self._volumes: list[Decimal] = []
        self._position = Decimal("0")
        self._ema_fast: Decimal | None = None
        self._ema_slow: Decimal | None = None
        self._ema_signal: Decimal | None = None
        self._macd_prev: Decimal | None = None
        self._atr: Decimal | None = None
        self._supertrend: Decimal | None = None
        self._super_dir = 1
        self._vwap_num = Decimal("0")
        self._vwap_den = Decimal("0")
        self._bar_i = 0
        self._kalman_x: Decimal | None = None
        self._kalman_p = Decimal("1")
        self._ml_score_ema: Decimal | None = None

    def on_event(self, event: MarketEvent, context: StrategyContext) -> tuple[OrderIntent, ...]:
        return ()

    def on_bar(self, bar: Bar, context: StrategyContext) -> tuple[OrderIntent, ...]:
        self._bar_i += 1
        self._closes.append(bar.close)
        self._highs.append(bar.high)
        self._lows.append(bar.low)
        self._volumes.append(bar.volume)

        if context.portfolio_state is not None:
            held = Decimal("0")
            for p in context.portfolio_state.positions:
                if p.instrument_id == bar.instrument_id:
                    held = p.quantity
            self._position = held

        signal = self._compute_signal(bar)
        qty = Decimal(str(self._parameters.get("quantity", "1")))

        if signal > 0 and self._position <= 0:
            self._position = qty
            return (
                OrderIntent(
                    intent_id=f"{self._signal_kind}-buy-{self._bar_i}",
                    intent_type=IntentType.PLACE_ORDER,
                    instrument_id=bar.instrument_id,
                    side=OrderSide.BUY,
                    quantity=qty,
                    price=bar.high,
                    order_type=OrderType.LIMIT,
                    time_in_force=TimeInForce.GTC,
                ),
            )
        if signal <= 0 and self._position > 0:
            sell_qty = self._position
            self._position = Decimal("0")
            return (
                OrderIntent(
                    intent_id=f"{self._signal_kind}-sell-{self._bar_i}",
                    intent_type=IntentType.PLACE_ORDER,
                    instrument_id=bar.instrument_id,
                    side=OrderSide.SELL,
                    quantity=sell_qty,
                    price=bar.low,
                    order_type=OrderType.LIMIT,
                    time_in_force=TimeInForce.GTC,
                ),
            )
        return _noop(bar)

    def _compute_signal(self, bar: Bar) -> int:
        kind = self._signal_kind
        fn = _SIGNAL_TABLE.get(kind)
        if fn is None:
            # fallback: mismo criterio que SimpleMomentum
            return self._sig_momentum(bar)
        return fn(self, bar)

    def _sig_momentum(self, _bar: Bar) -> int:
        lookback = int(self._parameters.get("lookback", 3))
        if len(self._closes) < lookback + 1:
            return 0
        window = self._closes[-(lookback + 1) :]
        up = all(window[i] > window[i - 1] for i in range(1, len(window)))
        down = all(window[i] < window[i - 1] for i in range(1, len(window)))
        if up:
            return 1
        if down:
            return 0
        return 1 if self._position > 0 else 0

    def _sig_ma_crossover(self, _bar: Bar) -> int:
        fast = int(self._parameters.get("fast", 5))
        slow = int(self._parameters.get("slow", 20))
        if len(self._closes) < slow + 1:
            return 0
        f0 = _sma(self._closes[:-1], fast)
        s0 = _sma(self._closes[:-1], slow)
        f1 = _sma(self._closes, fast)
        s1 = _sma(self._closes, slow)
        if None in (f0, s0, f1, s1):
            return 0
        assert f0 is not None and s0 is not None and f1 is not None and s1 is not None
        if f0 <= s0 and f1 > s1:
            return 1
        if f0 >= s0 and f1 < s1:
            return 0
        return 1 if self._position > 0 else 0

    def _sig_ema(self, bar: Bar) -> int:
        fast_n = int(self._parameters.get("fast", 8))
        slow_n = int(self._parameters.get("slow", 21))
        prev_f, prev_s = self._ema_fast, self._ema_slow
        self._ema_fast = _ema_update(self._ema_fast, bar.close, fast_n)
        self._ema_slow = _ema_update(self._ema_slow, bar.close, slow_n)
        if prev_f is None or prev_s is None:
            return 0
        if prev_f <= prev_s and self._ema_fast > self._ema_slow:
            return 1
        if prev_f >= prev_s and self._ema_fast < self._ema_slow:
            return 0
        return 1 if self._position > 0 else 0

    def _sig_donchian(self, bar: Bar) -> int:
        n = int(self._parameters.get("channel", 20))
        if len(self._highs) < n + 1:
            return 0
        prior_high = max(self._highs[-(n + 1) : -1])
        prior_low = min(self._lows[-(n + 1) : -1])
        if bar.close > prior_high:
            return 1
        if bar.close < prior_low:
            return 0
        return 1 if self._position > 0 else 0

    def _sig_turtle(self, bar: Bar) -> int:
        entry_n = int(self._parameters.get("entry", 20))
        exit_n = int(self._parameters.get("exit", 10))
        if len(self._highs) < entry_n + 1:
            return 0
        entry_high = max(self._highs[-(entry_n + 1) : -1])
        exit_low = min(self._lows[-(exit_n + 1) : -1]) if len(self._lows) > exit_n else bar.low
        if bar.close > entry_high:
            return 1
        if bar.close < exit_low:
            return 0
        return 1 if self._position > 0 else 0

    def _sig_supertrend(self, bar: Bar) -> int:
        period = int(self._parameters.get("atr_period", 10))
        mult = Decimal(str(self._parameters.get("mult", "2")))
        if len(self._closes) < 2:
            return 0
        tr = max(
            bar.high - bar.low,
            abs(bar.high - self._closes[-2]),
            abs(bar.low - self._closes[-2]),
        )
        if self._atr is None:
            self._atr = tr
        else:
            self._atr = (self._atr * Decimal(period - 1) + tr) / Decimal(period)
        mid = (bar.high + bar.low) / 2
        upper = mid + mult * self._atr
        lower = mid - mult * self._atr
        if self._supertrend is None:
            self._supertrend = upper
            self._super_dir = -1
        if self._super_dir > 0:
            self._supertrend = max(lower, self._supertrend)
            if bar.close < self._supertrend:
                self._super_dir = -1
                self._supertrend = upper
        else:
            self._supertrend = min(upper, self._supertrend)
            if bar.close > self._supertrend:
                self._super_dir = 1
                self._supertrend = lower
        return 1 if self._super_dir > 0 else 0

    def _sig_macd(self, bar: Bar) -> int:
        fast_n = int(self._parameters.get("fast", 12))
        slow_n = int(self._parameters.get("slow", 26))
        sig_n = int(self._parameters.get("signal", 9))
        self._ema_fast = _ema_update(self._ema_fast, bar.close, fast_n)
        self._ema_slow = _ema_update(self._ema_slow, bar.close, slow_n)
        if self._ema_fast is None or self._ema_slow is None:
            return 0
        macd = self._ema_fast - self._ema_slow
        self._ema_signal = _ema_update(self._ema_signal, macd, sig_n)
        if self._ema_signal is None or self._macd_prev is None:
            self._macd_prev = macd
            return 0
        prev_hist = self._macd_prev - self._ema_signal
        hist = macd - self._ema_signal
        self._macd_prev = macd
        if prev_hist <= 0 and hist > 0:
            return 1
        if prev_hist >= 0 and hist < 0:
            return 0
        return 1 if self._position > 0 else 0

    def _sig_rsi_momentum(self, _bar: Bar) -> int:
        period = int(self._parameters.get("period", 14))
        lo = Decimal(str(self._parameters.get("oversold", "40")))
        hi = Decimal(str(self._parameters.get("overbought", "70")))
        rsi = self._rsi(period)
        if rsi is None:
            return 0
        if rsi < lo:
            return 1
        if rsi > hi:
            return 0
        return 1 if self._position > 0 else 0

    def _sig_rsi_reversion(self, _bar: Bar) -> int:
        period = int(self._parameters.get("period", 14))
        lo = Decimal(str(self._parameters.get("oversold", "30")))
        hi = Decimal(str(self._parameters.get("overbought", "70")))
        rsi = self._rsi(period)
        if rsi is None:
            return 0
        if rsi < lo:
            return 1
        if rsi > hi:
            return 0
        return 1 if self._position > 0 else 0

    def _rsi(self, period: int) -> Decimal | None:
        if len(self._closes) < period + 1:
            return None
        gains = Decimal("0")
        losses = Decimal("0")
        for i in range(-period, 0):
            diff = self._closes[i] - self._closes[i - 1]
            if diff >= 0:
                gains += diff
            else:
                losses -= diff
        if losses == 0:
            return Decimal("100")
        rs = (gains / Decimal(period)) / (losses / Decimal(period))
        return Decimal("100") - (Decimal("100") / (Decimal("1") + rs))

    def _sig_roc(self, _bar: Bar) -> int:
        period = int(self._parameters.get("period", 10))
        thr = Decimal(str(self._parameters.get("threshold", "0")))
        if len(self._closes) < period + 1:
            return 0
        prev = self._closes[-(period + 1)]
        if prev == 0:
            return 0
        roc = (self._closes[-1] - prev) / prev
        if roc > thr:
            return 1
        if roc < -thr:
            return 0
        return 1 if self._position > 0 else 0

    def _sig_relative_strength(self, _bar: Bar) -> int:
        # Proxy single-asset: close vs SMA (sin benchmark externo).
        period = int(self._parameters.get("period", 20))
        sma = _sma(self._closes, period)
        if sma is None:
            return 0
        if self._closes[-1] > sma:
            return 1
        return 0

    def _sig_breakout(self, bar: Bar) -> int:
        n = int(self._parameters.get("lookback", 20))
        if len(self._highs) < n + 1:
            return 0
        level = max(self._highs[-(n + 1) : -1])
        if bar.close > level:
            return 1
        if bar.close < min(self._lows[-(n + 1) : -1]):
            return 0
        return 1 if self._position > 0 else 0

    def _sig_volume_momentum(self, bar: Bar) -> int:
        n = int(self._parameters.get("lookback", 10))
        if len(self._closes) < n + 1:
            return 0
        avg_vol = _sma(self._volumes, n)
        if avg_vol is None or avg_vol <= 0:
            return self._sig_momentum(bar)
        vol_ok = self._volumes[-1] > avg_vol
        price_up = self._closes[-1] > self._closes[-2]
        if vol_ok and price_up:
            return 1
        if self._closes[-1] < self._closes[-2]:
            return 0
        return 1 if self._position > 0 else 0

    def _sig_bollinger(self, bar: Bar) -> int:
        period = int(self._parameters.get("period", 20))
        k = Decimal(str(self._parameters.get("k", "2")))
        if len(self._closes) < period:
            return 0
        mean = _sma(self._closes, period)
        if mean is None:
            return 0
        window = self._closes[-period:]
        var = sum((x - mean) ** 2 for x in window) / Decimal(period)
        std = var.sqrt() if var > 0 else Decimal("0")
        lower = mean - k * std
        upper = mean + k * std
        if bar.close < lower:
            return 1
        if bar.close > upper:
            return 0
        return 1 if self._position > 0 else 0

    def _sig_zscore(self, bar: Bar) -> int:
        period = int(self._parameters.get("period", 20))
        entry = Decimal(str(self._parameters.get("entry_z", "-1.5")))
        exit_z = Decimal(str(self._parameters.get("exit_z", "0")))
        if len(self._closes) < period:
            return 0
        mean = _sma(self._closes, period)
        if mean is None:
            return 0
        window = self._closes[-period:]
        var = sum((x - mean) ** 2 for x in window) / Decimal(period)
        std = var.sqrt() if var > 0 else Decimal("0")
        if std == 0:
            return 0
        z = (bar.close - mean) / std
        if z <= entry:
            return 1
        if z >= exit_z:
            return 0
        return 1 if self._position > 0 else 0

    def _sig_vwap_reversion(self, bar: Bar) -> int:
        typical = (bar.high + bar.low + bar.close) / 3
        vol = self._volumes[-1] if self._volumes else Decimal("1")
        if vol <= 0:
            vol = Decimal("1")
        self._vwap_num += typical * vol
        self._vwap_den += vol
        if self._vwap_den <= 0:
            return 0
        vwap = self._vwap_num / self._vwap_den
        band = Decimal(str(self._parameters.get("band_pct", "0.005")))
        if bar.close < vwap * (Decimal("1") - band):
            return 1
        if bar.close > vwap * (Decimal("1") + band):
            return 0
        return 1 if self._position > 0 else 0

    def _sig_cointegration_proxy(self, bar: Bar) -> int:
        # Proxy single-series: mean-revert vs SMA (pares reales = stub).
        return self._sig_zscore(bar)

    def _sig_pairs_lag(self, bar: Bar) -> int:
        """Spread close vs close retrasado N (proxy de pares sin 2ª serie)."""
        lag = int(self._parameters.get("lag", 5))
        period = int(self._parameters.get("period", 20))
        entry = Decimal(str(self._parameters.get("entry_z", "-1.0")))
        exit_z = Decimal(str(self._parameters.get("exit_z", "0.5")))
        if len(self._closes) < lag + period:
            return 0
        spreads = [
            self._closes[i] - self._closes[i - lag]
            for i in range(-(period), 0)
        ]
        mean = sum(spreads, Decimal("0")) / Decimal(period)
        var = sum((s - mean) ** 2 for s in spreads) / Decimal(period)
        std = var.sqrt() if var > 0 else Decimal("0")
        if std == 0:
            return 0
        z = (spreads[-1] - mean) / std
        if z <= entry:
            return 1
        if z >= exit_z:
            return 0
        return 1 if self._position > 0 else 0

    def _sig_kalman(self, bar: Bar) -> int:
        """Filtro Kalman 1D sobre el precio: long si precio << estimación."""
        q = Decimal(str(self._parameters.get("process_var", "0.001")))
        r = Decimal(str(self._parameters.get("measure_var", "0.01")))
        entry = Decimal(str(self._parameters.get("entry_z", "-1.0")))
        exit_z = Decimal(str(self._parameters.get("exit_z", "0")))
        z_obs = bar.close
        if self._kalman_x is None:
            self._kalman_x = z_obs
            self._kalman_p = Decimal("1")
            return 0
        # Predict
        x_pred = self._kalman_x
        p_pred = self._kalman_p + q
        # Update
        k = p_pred / (p_pred + r)
        self._kalman_x = x_pred + k * (z_obs - x_pred)
        self._kalman_p = (Decimal("1") - k) * p_pred
        innov = z_obs - self._kalman_x
        scale = (self._kalman_p + r).sqrt() if (self._kalman_p + r) > 0 else Decimal("1")
        z = innov / scale if scale != 0 else Decimal("0")
        if z <= entry:
            return 1
        if z >= exit_z:
            return 0
        return 1 if self._position > 0 else 0

    def _sig_pca_proxy(self, bar: Bar) -> int:
        """PC1 proxy de [ret, rango%, vol_rel] con pesos fijos (sin sklearn)."""
        period = int(self._parameters.get("period", 20))
        if len(self._closes) < period + 1:
            return 0
        ret = (self._closes[-1] / self._closes[-2] - Decimal("1")) if self._closes[-2] else Decimal("0")  # noqa: E501
        rng = (bar.high - bar.low) / bar.close if bar.close else Decimal("0")
        avg_vol = _sma(self._volumes, period) or Decimal("1")
        vol_rel = (self._volumes[-1] / avg_vol - Decimal("1")) if avg_vol else Decimal("0")
        # Pesos fijos ≈ dirección de máxima varianza típica research
        w_ret = Decimal(str(self._parameters.get("w_ret", "0.5")))
        w_rng = Decimal(str(self._parameters.get("w_range", "0.3")))
        w_vol = Decimal(str(self._parameters.get("w_vol", "0.2")))
        score = w_ret * ret + w_rng * rng + w_vol * vol_rel
        thr = Decimal(str(self._parameters.get("threshold", "0")))
        if score > thr:
            return 1
        if score < -thr:
            return 0
        return 1 if self._position > 0 else 0

    def _sig_obi_proxy(self, bar: Bar) -> int:
        """Imbalance proxy OHLC: (close-open)/(high-low)."""
        span = bar.high - bar.low
        if span <= 0:
            return 1 if self._position > 0 else 0
        imb = (bar.close - bar.open) / span
        thr = Decimal(str(self._parameters.get("threshold", "0.2")))
        if imb >= thr:
            return 1
        if imb <= -thr:
            return 0
        return 1 if self._position > 0 else 0

    def _sig_liquidity_proxy(self, bar: Bar) -> int:
        """Liquidez proxy: volumen vs SMA + rango estrecho."""
        period = int(self._parameters.get("period", 20))
        avg_vol = _sma(self._volumes, period)
        if avg_vol is None or avg_vol <= 0:
            return 0
        mult = Decimal(str(self._parameters.get("vol_mult", "1.2")))
        liquid = self._volumes[-1] >= avg_vol * mult
        if liquid and bar.close > bar.open:
            return 1
        if not liquid and bar.close < bar.open:
            return 0
        return 1 if self._position > 0 else 0

    def _sig_toxicity_proxy(self, bar: Bar) -> int:
        """Toxicidad proxy: |ret| alto con volumen alto → flat; ret suave → long."""
        if len(self._closes) < 2:
            return 0
        period = int(self._parameters.get("period", 20))
        ret = abs(self._closes[-1] / self._closes[-2] - Decimal("1"))
        avg_vol = _sma(self._volumes, period) or Decimal("1")
        vol_rel = self._volumes[-1] / avg_vol if avg_vol else Decimal("1")
        tox = ret * vol_rel
        bad = Decimal(str(self._parameters.get("tox_exit", "0.02")))
        good = Decimal(str(self._parameters.get("tox_entry", "0.005")))
        if tox >= bad:
            return 0
        if tox <= good and bar.close >= bar.open:
            return 1
        return 1 if self._position > 0 else 0

    def _sig_ml_feature_score(self, bar: Bar) -> int:
        """Score lineal sobre features (proxy ML sin modelo entrenado)."""
        period = int(self._parameters.get("period", 14))
        if len(self._closes) < period + 1:
            return 0
        mom = self._closes[-1] / self._closes[-(period + 1)] - Decimal("1")
        rsi = self._rsi(period) or Decimal("50")
        rsi_n = (rsi - Decimal("50")) / Decimal("50")
        avg_vol = _sma(self._volumes, period) or Decimal("1")
        vol_n = self._volumes[-1] / avg_vol - Decimal("1") if avg_vol else Decimal("0")
        w_m = Decimal(str(self._parameters.get("w_mom", "0.4")))
        w_r = Decimal(str(self._parameters.get("w_rsi", "0.4")))
        w_v = Decimal(str(self._parameters.get("w_vol", "0.2")))
        score = w_m * mom + w_r * rsi_n + w_v * vol_n
        self._ml_score_ema = _ema_update(self._ml_score_ema, score, 5)
        use = self._ml_score_ema if self._ml_score_ema is not None else score
        thr = Decimal(str(self._parameters.get("threshold", "0")))
        if use > thr:
            return 1
        if use < -thr:
            return 0
        return 1 if self._position > 0 else 0

    def _sig_vol_regime(self, bar: Bar) -> int:
        """Vol trading proxy: long si ATR% > percentil / umbral."""
        period = int(self._parameters.get("atr_period", 14))
        if len(self._closes) < 2:
            return 0
        tr = max(
            bar.high - bar.low,
            abs(bar.high - self._closes[-2]),
            abs(bar.low - self._closes[-2]),
        )
        if self._atr is None:
            self._atr = tr
        else:
            self._atr = (self._atr * Decimal(period - 1) + tr) / Decimal(period)
        atr_pct = self._atr / bar.close if bar.close else Decimal("0")
        thr = Decimal(str(self._parameters.get("atr_pct_entry", "0.01")))
        exit_thr = Decimal(str(self._parameters.get("atr_pct_exit", "0.005")))
        if atr_pct >= thr and bar.close >= bar.open:
            return 1
        if atr_pct <= exit_thr:
            return 0
        return 1 if self._position > 0 else 0

    def get_parameters(self) -> dict[str, Any]:
        out = dict(self._parameters)
        out["signal_kind"] = self._signal_kind
        return out

    def set_parameters(self, params: dict[str, Any]) -> None:
        self._parameters = dict(params)
        if "signal_kind" in params:
            self._signal_kind = str(params["signal_kind"])

    def get_state(self) -> dict[str, Any]:
        return {
            "position": str(self._position),
            "n_bars": self._bar_i,
            "signal_kind": self._signal_kind,
        }

    def reset(self) -> None:
        self._closes.clear()
        self._highs.clear()
        self._lows.clear()
        self._volumes.clear()
        self._position = Decimal("0")
        self._ema_fast = None
        self._ema_slow = None
        self._ema_signal = None
        self._macd_prev = None
        self._atr = None
        self._supertrend = None
        self._super_dir = 1
        self._vwap_num = Decimal("0")
        self._vwap_den = Decimal("0")
        self._bar_i = 0
        self._kalman_x = None
        self._kalman_p = Decimal("1")
        self._ml_score_ema = None


_SIGNAL_TABLE: dict[str, Callable[[ClassicBarStrategy, Bar], int]] = {
    "ma_crossover": ClassicBarStrategy._sig_ma_crossover,
    "ema": ClassicBarStrategy._sig_ema,
    "donchian_breakout": ClassicBarStrategy._sig_donchian,
    "turtle": ClassicBarStrategy._sig_turtle,
    "supertrend": ClassicBarStrategy._sig_supertrend,
    "macd": ClassicBarStrategy._sig_macd,
    "rsi_momentum": ClassicBarStrategy._sig_rsi_momentum,
    "roc": ClassicBarStrategy._sig_roc,
    "relative_strength": ClassicBarStrategy._sig_relative_strength,
    "breakout": ClassicBarStrategy._sig_breakout,
    "volume_momentum": ClassicBarStrategy._sig_volume_momentum,
    "bollinger": ClassicBarStrategy._sig_bollinger,
    "rsi_reversion": ClassicBarStrategy._sig_rsi_reversion,
    "zscore": ClassicBarStrategy._sig_zscore,
    "vwap_reversion": ClassicBarStrategy._sig_vwap_reversion,
    "cointegration_proxy": ClassicBarStrategy._sig_cointegration_proxy,
    "momentum": ClassicBarStrategy._sig_momentum,
    "pairs_lag": ClassicBarStrategy._sig_pairs_lag,
    "kalman": ClassicBarStrategy._sig_kalman,
    "pca_proxy": ClassicBarStrategy._sig_pca_proxy,
    "obi_proxy": ClassicBarStrategy._sig_obi_proxy,
    "liquidity_proxy": ClassicBarStrategy._sig_liquidity_proxy,
    "toxicity_proxy": ClassicBarStrategy._sig_toxicity_proxy,
    "ml_feature_score": ClassicBarStrategy._sig_ml_feature_score,
    "vol_regime": ClassicBarStrategy._sig_vol_regime,
}
