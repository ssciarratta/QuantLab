"""FASE 2 — persistencia / normalize / hashes / lab contexto."""

from __future__ import annotations

from pathlib import Path

from quantlab.montecarlo.traceability import (
    MONTECARLO_SCHEMA_VERSION_CURRENT,
    MONTECARLO_SCHEMA_VERSION_LEGACY,
    hash_mapping,
    normalize_montecarlo_payload,
)
from quantlab.workbench import lab_services
from quantlab.workbench.montecarlo_runs import (
    delete_montecarlo_run,
    get_montecarlo_run,
    list_montecarlo_runs,
)


def test_normalize_legacy_v1_payload() -> None:
    legacy = {
        "schema_version": 1,
        "ci_high": 50014.0,
        "ci_level": 0.95,
        "ci_low": 50013.0,
        "created_at": "2026-07-27T12:00:00+00:00",
        "final_equities": [50013.5, 50014.0],
        "kind": "montecarlo",
        "mean_equity": 50013.75,
        "n_bars": 16,
        "n_scenarios": 5,
        "noise_bps": 10,
        "ok": True,
        "run_id": "mc-legacy",
        "seed": 42,
        "std_equity": 0.2,
    }
    norm = normalize_montecarlo_payload(legacy)
    assert norm["schema_version"] == MONTECARLO_SCHEMA_VERSION_LEGACY
    assert norm["context"]["orphan_technical_mode"] is True
    assert norm["context"]["strategy_id"] is None
    assert norm["config"]["n_bars"] == 16
    assert norm["metrics"]["mean_equity"] == 50013.75
    assert norm["mean_equity"] == 50013.75


def test_lab_montecarlo_persists_v2_with_hashes(tmp_path: Path) -> None:
    out = lab_services.run_lab_montecarlo(
        n_scenarios=3,
        n_bars=12,
        seed=7,
        persist=True,
        montecarlo_root=tmp_path,
        session_id="sess-test",
        scan_id="scan-abc",
        backtest_id="bt-xyz",
        strategy_id="buy_once",
    )
    assert out["ok"] is True
    assert out["schema_version"] == MONTECARLO_SCHEMA_VERSION_CURRENT
    assert out["context"]["scan_id"] == "scan-abc"
    assert out["context"]["backtest_id"] == "bt-xyz"
    assert out["context"]["orphan_technical_mode"] is False
    assert out["config_hash"]
    assert out["relations"]["dataset_hash"]
    assert out["bar_horizon_label"]
    loaded = get_montecarlo_run(tmp_path, out["run_id"])
    assert loaded["run_id"] == out["run_id"]
    listed = list_montecarlo_runs(tmp_path)
    assert listed["count"] == 1
    delete_montecarlo_run(tmp_path, out["run_id"])
    assert list_montecarlo_runs(tmp_path)["count"] == 0


def test_same_seed_reproducible(tmp_path: Path) -> None:
    a = lab_services.run_lab_montecarlo(
        n_scenarios=4, n_bars=10, seed=42, persist=False, montecarlo_root=None
    )
    b = lab_services.run_lab_montecarlo(
        n_scenarios=4, n_bars=10, seed=42, persist=False, montecarlo_root=None
    )
    assert a["final_equities"] == b["final_equities"]
    assert hash_mapping(a["config"]) == hash_mapping(b["config"])


def test_orphan_warning_without_links() -> None:
    out = lab_services.run_lab_montecarlo(
        n_scenarios=2, n_bars=8, seed=1, persist=False
    )
    assert out["context"]["orphan_technical_mode"] is True
    assert out["warnings"]
