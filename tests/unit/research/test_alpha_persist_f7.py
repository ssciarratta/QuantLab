"""FASE 7 — persistencia / hashes / comparacion de scans."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from quantlab.core.types.market import Bar
from quantlab.research.alpha.legacy import run_legacy_v1_scan
from quantlab.research.alpha.models import AlphaScanRequest
from quantlab.research.alpha.persist import (
    ScanStore,
    compare_persisted,
    hash_bars_fingerprint,
    hash_request,
)
from quantlab.research.alpha.profiles import score_with_profile


def _bars(sym: str, n: int = 12) -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 6, 1, tzinfo=UTC)
    for i in range(n):
        c = Decimal(100 + i)
        t0 = base + timedelta(hours=i)
        out.append(
            Bar(
                instrument_id=f"BN:{sym}",
                open=c,
                high=c + Decimal("1"),
                low=c - Decimal("0.5"),
                close=c,
                volume=Decimal("1000"),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(hours=1),
                timeframe="1h",
            )
        )
    return out


def test_hashes_stable(tmp_path: Path) -> None:
    bars = {"BN:A": _bars("A"), "BN:B": _bars("B")}
    h1 = hash_bars_fingerprint(bars)
    h2 = hash_bars_fingerprint(bars)
    assert h1 == h2
    req = AlphaScanRequest(top_n=3)
    assert hash_request(req) == hash_request(req)


def test_save_load_roundtrip_legacy(tmp_path: Path) -> None:
    bars = {"BN:A": _bars("A"), "BN:B": _bars("B")}
    result = run_legacy_v1_scan(bars, AlphaScanRequest(top_n=2))
    store = ScanStore(tmp_path)
    meta = store.save_alpha_result(result, bars_hash=hash_bars_fingerprint(bars))
    loaded = store.load(meta.scan_id)
    assert loaded["meta"]["bars_hash"] == meta.bars_hash
    assert loaded["result"]["scan_id"] == result.scan_id
    listed = store.list_scans()
    assert len(listed) == 1
    assert listed[0].scan_id == meta.scan_id


def test_compare_identical_and_changed(tmp_path: Path) -> None:
    bars = {"BN:A": _bars("A"), "BN:B": _bars("B")}
    store = ScanStore(tmp_path)
    rows = score_with_profile(bars, "legacy_v1")
    bh = hash_bars_fingerprint(bars)
    m1 = store.save_scored(profile="legacy_v1", rows=rows, bars_hash=bh, scan_id="scan_a")
    m2 = store.save_scored(profile="legacy_v1", rows=rows, bars_hash=bh, scan_id="scan_b")
    diff = compare_persisted(store.load(m1.scan_id), store.load(m2.scan_id))
    assert diff.same_bars is True
    assert diff.same_result is True
    assert diff.rank_changes == ()

    # Cambiar ranking artificialmente
    flipped = list(reversed([r for r in rows if not r.excluded]))
    m3 = store.save_scored(profile="legacy_v1", rows=flipped, bars_hash=bh, scan_id="scan_c")
    diff2 = compare_persisted(store.load(m1.scan_id), store.load(m3.scan_id))
    assert diff2.same_result is False
    assert len(diff2.rank_changes) >= 1


def test_repeat_same_inputs_same_result_hash(tmp_path: Path) -> None:
    bars = {"BN:A": _bars("A"), "BN:B": _bars("B")}
    store = ScanStore(tmp_path)
    bh = hash_bars_fingerprint(bars)
    r1 = score_with_profile(bars, "momentum")
    r2 = score_with_profile(bars, "momentum")
    m1 = store.save_scored(profile="momentum", rows=r1, bars_hash=bh, scan_id="r1")
    m2 = store.save_scored(profile="momentum", rows=r2, bars_hash=bh, scan_id="r2")
    assert m1.result_hash == m2.result_hash
