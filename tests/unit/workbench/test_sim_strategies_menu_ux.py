"""UI: panel Estrategias + favoritos menú + ranking ventanas."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STATIC = ROOT / "src/quantlab/workbench/static"


def test_strategies_pane_exists() -> None:
    js = (STATIC / "js/panes/strategies.js").read_text(encoding="utf-8")
    assert "createStrategiesPane" in js
    assert "Abrir en Simulador" in js


def test_index_loads_strategies_and_favorites() -> None:
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    assert "panes/strategies.js" in html
    assert "ql-favorites" in html
    assert "Mis favoritos" in html


def test_simulator_no_longer_embeds_guides_section() -> None:
    js = (STATIC / "js/panes/simulator.js").read_text(encoding="utf-8")
    assert "sim-strat-section" not in js
    assert "sim-open-strategies" in js
    assert "openRankMarketWindow" not in js
    assert "sim-rank-dock" in js
    assert "bindRankDockActions" in js
    assert "openSimMemoPresentation" in js
    assert "sim-run-rank" in js
    assert "QLFmt" in js or "minimumFractionDigits: 2" in js


def test_shell_has_strategies_opener_and_wm() -> None:
    js = (STATIC / "js/shell.js").read_text(encoding="utf-8")
    assert "openStrategies" in js
    assert "strategies: openStrategies" in js
    assert "wm: wm" in js
    assert "ql_menu_favorites" in js
    assert 'FAV_DEFAULT = ["scanner", "simulator", "strategies"]' in js


def test_lab_common_qlfmt_2_decimals() -> None:
    js = (STATIC / "js/panes/lab_common.js").read_text(encoding="utf-8")
    assert "QLFmt" in js
    assert "maximumFractionDigits: d" in js


def test_simulator_memo_presentation() -> None:
    js = (STATIC / "js/panes/simulator.js").read_text(encoding="utf-8")
    assert "openSimMemoPresentation" in js
    assert "buildCompareMemo" in js
    assert "buildRankMemo" in js
    assert "registerSimRun" in js
    assert "QLSimRegistry" in js
    css = (STATIC / "css/workbench.css").read_text(encoding="utf-8")
    assert ".pane-sim-memo" in css
    reg = (STATIC / "js/sim_registry.js").read_text(encoding="utf-8")
    assert "Descargar CSV" in reg
    assert "Compartir WhatsApp" in reg
    assert "pane-sim-memo" in reg


def test_simulator_memo_css() -> None:
    css = (STATIC / "css/workbench.css").read_text(encoding="utf-8")
    assert ".pane-sim-memo" in css
    assert ".sim-memo-body" in css
