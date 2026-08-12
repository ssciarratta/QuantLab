"""UI smoke: favoritos tip + panes Spot/Futures."""

from __future__ import annotations

from pathlib import Path

from static_test_helpers import read_static

STATIC = Path(__file__).resolve().parents[3] / "src/quantlab/workbench/static"


def test_favorites_default_core_six() -> None:
    menu_js = read_static("js/ql_menu.js")
    registry = read_static("js/panel_registry.js")
    assert "ql_menu_config_v6" in menu_js
    assert '"chat"' in registry
    assert '"scanner"' in registry
    assert '"simulator"' in registry
    assert '"montecarlo"' in registry
    assert '"binance_spot"' in registry
    assert '"binance_futures"' in registry


def test_taskbar_quick_strip_present() -> None:
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    assert 'id="taskbar-quick"' in html
    assert "binance_testnet.js" in html
    css = (STATIC / "css/workbench.css").read_text(encoding="utf-8")
    assert ".taskbar-quick" in css
    assert ".tb-quick-btn" in css


def test_binance_testnet_panes_factory() -> None:
    js = (STATIC / "js/panes/binance_testnet.js").read_text(encoding="utf-8")
    assert "createBinanceSpotPane" in js
    assert "createBinanceFuturesPane" in js
    assert "liveUnlock" in js
    assert "liveDemoSubmit" in js


def test_guided_lab_not_in_open_start_section() -> None:
    registry = read_static("js/panel_registry.js")
    # Guided Lab está en menú dinámico, no como botón fijo en index.
    assert 'id: "guided_lab"' in registry
    menu_js = read_static("js/ql_menu.js")
    assert "Spot" in menu_js or "binance_spot" in registry
