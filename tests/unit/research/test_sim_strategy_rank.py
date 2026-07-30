"""Ranking diverso de estrategias (sim) — sin red."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.research.sim.strategy_rank import (
    RankCandidate,
    ranking_strategy_metas,
    run_sim_strategy_rank,
    select_diverse_top,
)
from quantlab.workbench.api import (
    ApiError,
    WorkbenchState,
    handle_post_lab_sim_rank_strategies,
)
from quantlab.workbench.session import WorkbenchSession


def _cand(
    sid: str,
    family: str,
    pnl_pct: str,
    pnl: str = "0",
) -> RankCandidate:
    return RankCandidate(
        strategy_id=sid,
        strategy_name=sid,
        family=family,
        family_label_es=family,
        pnl=Decimal(pnl),
        pnl_pct=Decimal(pnl_pct),
        payload={"strategy_id": sid, "family": family},
    )


def test_ranking_metas_exclude_demo() -> None:
    metas = ranking_strategy_metas()
    ids = {m.id for m in metas}
    assert "dummy" not in ids
    assert "buy_once" not in ids
    assert len(metas) >= 30
    assert all(m.runnable for m in metas)


def test_select_diverse_top_fills_to_10_with_family_floor() -> None:
    cands = [
        _cand("a1", "trend", "50"),
        _cand("a2", "trend", "40"),
        _cand("b1", "momentum", "45"),
        _cand("c1", "mean_reversion", "30"),
        _cand("d1", "stats", "20"),
        _cand("e1", "ml", "10"),
        _cand("f1", "market_making", "5"),
        _cand("g1", "microstructure", "4"),
        _cand("h1", "options", "3"),
        _cand("i1", "multi_asset", "2"),
        _cand("a3", "trend", "49"),
    ]
    selected = select_diverse_top(cands, top_n=10)
    families = {c.family for c in selected}
    assert families == {
        "trend",
        "momentum",
        "mean_reversion",
        "stats",
        "ml",
        "market_making",
        "microstructure",
        "options",
        "multi_asset",
    }
    assert len(selected) == 10
    assert selected[0].strategy_id == "a1"
    assert "a3" in {c.strategy_id for c in selected}


def test_select_diverse_top_expands_when_more_families_than_top_n() -> None:
    cands = [_cand(f"s{i}", f"fam{i}", str(100 - i)) for i in range(12)]
    selected = select_diverse_top(cands, top_n=10)
    assert len(selected) == 12
    assert len({c.family for c in selected}) == 12
    assert selected[0].pnl_pct >= selected[-1].pnl_pct


def test_run_sim_strategy_rank_rejects_multi_coin() -> None:
    with pytest.raises(ValidationError, match="exactamente una moneda"):
        run_sim_strategy_rank(
            {
                "pairs": [
                    {"venue": "binance", "underlying": "ADA"},
                    {"venue": "okx", "underlying": "ETH"},
                ],
                "market_type": "futures",
                "leverage": "1",
            }
        )


def test_handle_post_lab_sim_rank_strategies_ok(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "sim-rank")
    state = WorkbenchState(session=session)
    fake = {
        "ok": True,
        "kind": "sim_strategy_rank",
        "coin": "ADA",
        "markets": [],
        "common": {},
        "live_blocked": True,
    }
    with patch(
        "quantlab.research.sim.strategy_rank.run_sim_strategy_rank",
        return_value=dict(fake),
    ):
        out = handle_post_lab_sim_rank_strategies(
            state,
            {
                "pairs": [{"venue": "binance", "underlying": "ADA"}],
                "leverage": "5",
            },
        )
    assert out["kind"] == "sim_strategy_rank"
    assert out["session_id"] == session.session_id
    assert out["coin"] == "ADA"


def test_handle_post_lab_sim_rank_strategies_bad_body(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "sim-rank-bad")
    state = WorkbenchState(session=session)
    with pytest.raises(ApiError) as exc:
        handle_post_lab_sim_rank_strategies(state, "x")  # type: ignore[arg-type]
    assert exc.value.status == 400
