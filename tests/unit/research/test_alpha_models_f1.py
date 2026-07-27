"""FASE 1 — contratos Alpha Scanner + adapter legacy_v1."""

from __future__ import annotations

import json
from pathlib import Path

from quantlab.research.alpha.legacy import run_legacy_v1_scan
from quantlab.research.alpha.models import (
    FORMULA_VERSION_LEGACY,
    PROFILE_LEGACY_V1,
    AlphaScanRequest,
)
from quantlab.workbench.lab_services import make_scanner_universe, run_lab_scanner


def test_legacy_v1_matches_lab_scanner_baseline() -> None:
    universe = make_scanner_universe()
    legacy_api = run_lab_scanner(top_n=3)
    req = AlphaScanRequest(
        venue="lab",
        network="local",
        market_type="synthetic",
        profile=PROFILE_LEGACY_V1,
        top_n=3,
        lookback_bars=16,
    )
    v2 = run_legacy_v1_scan(universe, req)

    assert v2.profile == PROFILE_LEGACY_V1
    assert v2.formula_version == FORMULA_VERSION_LEGACY
    assert list(v2.legacy_selected) == list(legacy_api["selected"])
    assert v2.fetched == 3
    assert v2.eligible == 3
    assert v2.excluded == 0

    # Mismos composites (orden + valores)
    api_scores = legacy_api["scores"]
    for i, cand in enumerate(v2.candidates):
        raw = api_scores[i]
        api_c = raw["composite"] if isinstance(raw, dict) else raw.composite
        assert cand.composite == float(api_c)
        assert cand.rank == i + 1
        assert cand.components  # breakdown visible
        assert cand.summary
        assert abs(sum(c.contribution or 0.0 for c in cand.components) - cand.composite) < 1e-6


def test_legacy_v1_matches_fase0_golden_file() -> None:
    golden = Path("docs/scanner/fase0_baseline_synthetic.json")
    assert golden.is_file()
    payload = json.loads(golden.read_text(encoding="utf-8"))
    expected_selected = payload["lab_scanner"]["selected"]
    expected_composites = [s["composite"] for s in payload["lab_scanner"]["scores"]]

    universe = make_scanner_universe()
    v2 = run_legacy_v1_scan(
        universe,
        AlphaScanRequest(venue="lab", top_n=3, profile=PROFILE_LEGACY_V1),
    )
    assert list(v2.legacy_selected) == expected_selected
    assert [c.composite for c in v2.candidates] == expected_composites


def test_alpha_scan_result_to_dict_serializable() -> None:
    universe = make_scanner_universe()
    v2 = run_legacy_v1_scan(universe, AlphaScanRequest(top_n=2))
    d = v2.to_dict()
    assert d["scanner_version"]
    assert d["note"]
    assert "rentabilidad" in d["note"].lower() or "rentabilidad" in d["warnings"][0].lower()
    assert len(d["candidates"]) == 3  # all scored; top_n only affects legacy_selected
    # top_n=2 → selected length 2 but scores still full universe ranked
    assert len(v2.legacy_selected) == 2
