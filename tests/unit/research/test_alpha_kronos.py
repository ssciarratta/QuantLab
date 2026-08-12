"""Tests Kronos-inside-Scanner: métricas, blend, legacy, anti-leakage, fallback."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from quantlab.core.types.market import Bar
from quantlab.research.alpha.kronos import (
    KronosConfig,
    KronosSkipReason,
    NullForecastEngine,
    TrajectoryBatch,
    apply_kronos_to_scan,
    blend_scores,
    compute_kronos_metrics,
    profile_kronos_score,
    reset_engine_for_tests,
)
from quantlab.research.alpha.kronos.cache import KronosDiskCache, forecast_cache_key, hash_closes
from quantlab.research.alpha.kronos.protocol import ForecastRequest, ForecastResult
from quantlab.research.alpha.kronos.scoring_bridge import build_score_fields


def _bars(n: int, *, start: float = 100.0, vol: float = 1.0) -> list[Bar]:
    out: list[Bar] = []
    t0 = datetime(2024, 1, 1, tzinfo=UTC)
    px = start
    for i in range(n):
        o = px
        c = px + (0.1 if i % 2 == 0 else -0.05) * vol
        h = max(o, c) + 0.2 * vol
        l_ = min(o, c) - 0.2 * vol
        ts_o = t0 + timedelta(hours=i)
        ts_c = ts_o + timedelta(hours=1)
        out.append(
            Bar(
                instrument_id="BN:TESTUSDT",
                open=Decimal(str(round(o, 6))),
                high=Decimal(str(round(h, 6))),
                low=Decimal(str(round(l_, 6))),
                close=Decimal(str(round(c, 6))),
                volume=Decimal("1000"),
                timestamp_open=ts_o,
                timestamp_close=ts_c,
                timeframe="1h",
            )
        )
        px = c
    return out


def _range_traj(
    *,
    k: int,
    h: int,
    base: float = 100.0,
    breakout: bool = False,
    trend: bool = False,
) -> TrajectoryBatch:
    opens: list[tuple[float, ...]] = []
    highs: list[tuple[float, ...]] = []
    lows: list[tuple[float, ...]] = []
    closes: list[tuple[float, ...]] = []
    for s in range(k):
        path_c: list[float] = []
        path_h: list[float] = []
        path_l: list[float] = []
        path_o: list[float] = []
        for t in range(h):
            c = base + t * 0.5 + s * 0.01 if trend else base + (0.05 if t % 2 == 0 else -0.05)
            o = c
            hi = c + 0.1
            lo = c - 0.1
            if breakout and t == h - 1:
                hi = base + 50.0
                c = base + 49.0
            path_o.append(o)
            path_h.append(hi)
            path_l.append(lo)
            path_c.append(c)
        opens.append(tuple(path_o))
        highs.append(tuple(path_h))
        lows.append(tuple(path_l))
        closes.append(tuple(path_c))
    return TrajectoryBatch(
        opens=tuple(opens),
        highs=tuple(highs),
        lows=tuple(lows),
        closes=tuple(closes),
    )


class SyntheticEngine:
    """Motor determinista para tests (sin torch)."""

    def __init__(self, batch: TrajectoryBatch) -> None:
        self.batch = batch

    def forecast(self, request: ForecastRequest) -> ForecastResult:
        _ = request
        return ForecastResult(
            ok=True,
            trajectories=self.batch,
            device="cpu",
            model_revision="synth",
        )

    def health(self) -> dict[str, object]:
        return {"ok": True, "engine": "synthetic", "device": "cpu", "revision": "synth"}


def test_blend_scores_none_keeps_traditional() -> None:
    trad, k, final = blend_scores(0.8, None, 0.25)
    assert trad == 0.8
    assert k is None
    assert final == 0.8


def test_blend_scores_formula() -> None:
    trad, k, final = blend_scores(0.8, 0.4, 0.25)
    assert k == 0.4
    assert abs(final - (0.75 * 0.8 + 0.25 * 0.4)) < 1e-9


def test_absent_metrics_not_zero() -> None:
    fields = build_score_fields(
        traditional_score=0.7,
        metrics=None,
        profile="market_making",
        weight=0.25,
        applied=False,
        skip_reason=KronosSkipReason.DEPS_MISSING.value,
    )
    assert fields["kronos_score"] is None
    assert fields["kronos_metrics"] is None
    assert fields["final_score"] == 0.7
    assert fields["kronos_skip_reason"] == KronosSkipReason.DEPS_MISSING.value


def test_range_vs_breakout_metrics() -> None:
    stable = _range_traj(k=4, h=8, breakout=False, trend=False)
    risky = _range_traj(k=4, h=8, breakout=True, trend=False)
    m_ok = compute_kronos_metrics(stable, range_high=101.0, range_low=99.0)
    m_bad = compute_kronos_metrics(risky, range_high=101.0, range_low=99.0)
    assert m_ok.kronos_breakout_risk is not None
    assert m_bad.kronos_breakout_risk is not None
    assert m_bad.kronos_breakout_risk > m_ok.kronos_breakout_risk
    assert m_ok.kronos_range_probability is not None
    assert m_ok.kronos_range_probability >= m_bad.kronos_range_probability  # type: ignore[operator]
    assert m_ok.confidence_is_calibrated_probability is False


def test_profiles_interpret_kronos_differently() -> None:
    trending = _range_traj(k=4, h=12, trend=True, breakout=False)
    m = compute_kronos_metrics(trending, range_high=200.0, range_low=50.0)
    mom = profile_kronos_score(m, "momentum")
    mr = profile_kronos_score(m, "mean_reversion")
    assert mom is not None and mr is not None
    assert mom > mr  # tendencia favorece momentum, no MR


def test_legacy_weight_zero_unchanged_ranking() -> None:
    reset_engine_for_tests()
    bars = {"BN:A": _bars(40), "BN:B": _bars(40, start=50.0)}
    scan = {
        "top_n": 2,
        "scores": [
            {"instrument_id": "BN:A", "symbol": "AUSDT", "composite": 0.9},
            {"instrument_id": "BN:B", "symbol": "BUSDT", "composite": 0.5},
        ],
        "selected": ["BN:A"],
    }
    out = apply_kronos_to_scan(
        scan,
        bars,
        config=KronosConfig(enabled=True),
        profile="legacy_v1",
        interval="1h",
        engine=SyntheticEngine(_range_traj(k=2, h=8)),
    )
    assert out["scores"][0]["instrument_id"] == "BN:A"
    assert out["scores"][0]["traditional_score"] == 0.9
    assert out["scores"][0]["kronos_score"] is None
    assert out["scores"][0]["final_score"] == 0.9
    assert out["kronos"]["skip_reason"] == KronosSkipReason.LEGACY_WEIGHT_ZERO.value
    assert out["kronos"]["popups"]


def test_disabled_identical_to_traditional() -> None:
    bars = {"BN:A": _bars(40)}
    scan = {
        "top_n": 1,
        "scores": [{"instrument_id": "BN:A", "symbol": "A", "composite": 0.42}],
        "selected": ["BN:A"],
    }
    out = apply_kronos_to_scan(
        dict(scan),
        bars,
        config=KronosConfig(enabled=False),
        profile="market_making",
        engine=NullForecastEngine(),
    )
    assert out["scores"][0]["final_score"] == 0.42
    assert out["scores"][0]["kronos_score"] is None


def test_load_failure_does_not_break_scanner() -> None:
    bars = {"BN:A": _bars(40)}
    scan = {
        "top_n": 1,
        "scores": [{"instrument_id": "BN:A", "symbol": "A", "composite": 0.55}],
        "selected": ["BN:A"],
    }
    out = apply_kronos_to_scan(
        scan,
        bars,
        config=KronosConfig(enabled=True),
        profile="market_making",
        engine=NullForecastEngine(KronosSkipReason.MODEL_LOAD_FAILED),
    )
    assert out.get("ok", True)
    assert out["scores"][0]["final_score"] == 0.55
    assert out["kronos"]["status"] == "unavailable"


def test_mm_penalizes_breakout_vs_stable() -> None:
    bars_a = _bars(48, start=100.0)
    bars_b = _bars(48, start=100.0)
    # A mejor tradicional, pero breakout futuro; B estable
    scan = {
        "top_n": 2,
        "scores": [
            {"instrument_id": "BN:A", "symbol": "A", "composite": 0.82},
            {"instrument_id": "BN:B", "symbol": "B", "composite": 0.78},
        ],
        "selected": ["BN:A", "BN:B"],
    }

    class DualEngine:
        def forecast(self, request: ForecastRequest) -> ForecastResult:
            if "A" in request.instrument_id:
                batch = _range_traj(k=4, h=12, breakout=True)
            else:
                batch = _range_traj(k=4, h=12, breakout=False)
            return ForecastResult(ok=True, trajectories=batch, device="cpu")

        def health(self) -> dict[str, object]:
            return {"ok": True, "engine": "dual", "device": "cpu"}

    out = apply_kronos_to_scan(
        scan,
        {"BN:A": bars_a, "BN:B": bars_b},
        config=KronosConfig(
            enabled=True,
            top_n=20,
            sample_count=4,
            lookback=32,
            weight=0.40,  # acentúa penalización futura en el test
        ),
        profile="market_making",
        engine=DualEngine(),
    )
    # B debería ganar o al menos A bajar relativo
    finals = {r["instrument_id"]: r["final_score"] for r in out["scores"]}
    kro = {r["instrument_id"]: r.get("kronos_score") for r in out["scores"]}
    assert kro["BN:A"] is not None and kro["BN:B"] is not None
    assert kro["BN:B"] > kro["BN:A"]
    assert finals["BN:A"] < 0.82  # penalizada vs tradicional
    assert finals["BN:B"] >= finals["BN:A"]
    assert out["scores"][0]["instrument_id"] == "BN:B"


def test_cache_reproducible(tmp_path: Path) -> None:
    key = forecast_cache_key(
        symbol="X",
        interval="1h",
        model="m",
        lookback=10,
        pred_len=12,
        sample_count=4,
        temperature=1.0,
        top_p=0.9,
        seed=42,
        data_hash=hash_closes((1.0, 2.0, 3.0)),
    )
    cache = KronosDiskCache(tmp_path)
    payload = {"opens": [[1]], "highs": [[1]], "lows": [[1]], "closes": [[1]], "meta": {}}
    cache.set(key, payload)
    assert cache.get(key) == payload


def test_no_leakage_only_rank_bars_passed() -> None:
    """El caller debe pasar solo rank bars; integramos assert de longitud."""
    rank = _bars(30)
    # Si se pasara OOS completo (60), el lookback tomaría el final OOS — test de contrato:
    # apply usa solo lo que recibe; documentamos que lab_services pasa rank_universe.
    seen_len: list[int] = []

    class LenEngine:
        def forecast(self, request: ForecastRequest) -> ForecastResult:
            seen_len.append(len(request.lookback_closes))
            return ForecastResult(
                ok=True,
                trajectories=_range_traj(k=2, h=request.pred_len),
                device="cpu",
            )

        def health(self) -> dict[str, object]:
            return {"ok": True, "engine": "len", "device": "cpu"}

    scan = {
        "top_n": 1,
        "scores": [{"instrument_id": "BN:TESTUSDT", "symbol": "TEST", "composite": 0.8}],
        "selected": ["BN:TESTUSDT"],
    }
    apply_kronos_to_scan(
        scan,
        {"BN:TESTUSDT": rank},
        config=KronosConfig(enabled=True, lookback=20, top_n=5),
        profile="balanced",
        engine=LenEngine(),
    )
    assert seen_len
    assert seen_len[0] <= 20
    assert seen_len[0] <= len(rank)


def test_legacy_override_allows_minimal_weight() -> None:
    cfg = KronosConfig(enabled=True, legacy_override=True)
    assert cfg.weight_for_profile("legacy_v1") == pytest.approx(0.05)


def test_safe_stdio_absorbs_unicode_progress_bars() -> None:
    """Regresión: ████ en consola ASCII no debe tumbar el Scanner."""
    import sys

    from quantlab.research.alpha.kronos.stdio_guard import safe_stdio

    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout.reconfigure(encoding="ascii", errors="strict")
        sys.stderr.reconfigure(encoding="ascii", errors="strict")
        # Sin guard: falla (documenta el bug).
        with pytest.raises(UnicodeEncodeError):
            sys.stdout.write("Fetching 5 files:  40%|████      | 2/5\n")
        # Con guard: no levanta.
        with safe_stdio():
            n = sys.stdout.write("Fetching 5 files:  40%|████      | 2/5\n")
            assert n > 0
            sys.stdout.write("Un score alto indica adecuación\n")
    finally:
        sys.stdout = old_out
        sys.stderr = old_err


def test_forecast_catches_unicode_encode_error() -> None:
    """UnicodeEncodeError en inferencia → fail-soft (no 500 HTTP)."""
    import sys

    from quantlab.research.alpha.kronos.errors import KronosSkipReason
    from quantlab.research.alpha.kronos.forecast import KronosTorchEngine

    eng = object.__new__(KronosTorchEngine)
    eng.config = KronosConfig(enabled=True)
    eng.vendor = Path(".")
    eng.device = "cpu"
    eng.model_revision = "test"

    eng._predictor = object()

    def _raise_ascii(_request: ForecastRequest) -> TrajectoryBatch:
        raise UnicodeEncodeError("ascii", "████", 0, 4, "ordinal not in range(128)")

    eng._predict_trajectories = _raise_ascii  # type: ignore[method-assign]
    bars = _bars(16)
    ns = tuple(int(b.timestamp_close.timestamp() * 1e9) for b in bars)
    req = ForecastRequest(
        instrument_id="BN:TESTUSDT",
        lookback_opens=tuple(float(b.open) for b in bars),
        lookback_highs=tuple(float(b.high) for b in bars),
        lookback_lows=tuple(float(b.low) for b in bars),
        lookback_closes=tuple(float(b.close) for b in bars),
        lookback_volumes=tuple(float(b.volume) for b in bars),
        lookback_amounts=tuple(float(b.volume) for b in bars),
        timestamps_ns=ns,
        pred_len=4,
        sample_count=1,
        temperature=1.0,
        top_p=0.9,
        seed=1,
    )
    old_out = sys.stdout
    try:
        sys.stdout.reconfigure(encoding="ascii", errors="strict")
        result = eng.forecast(req)
    finally:
        sys.stdout = old_out
    assert result.ok is False
    assert result.reason == KronosSkipReason.INFERENCE_FAILED
    assert result.detail and "stdio_ascii" in result.detail
