"""UI smoke: favoritos tip + panes Spot/Futures."""

from __future__ import annotations

from pathlib import Path

STATIC = Path(__file__).resolve().parents[3] / "src/quantlab/workbench/static"


def test_favorites_default_core_six() -> None:
    js = (STATIC / "js/shell.js").read_text(encoding="utf-8")
    assert 'FAV_STORAGE_KEY = "ql_menu_favorites_v4"' in js
    assert '"chat"' in js
    assert '"scanner"' in js
    assert '"simulator"' in js
    assert '"montecarlo"' in js
    assert '"binance_spot"' in js
    assert '"binance_futures"' in js


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
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    assert "Lab avanzado / Guided" in html
    # Favoritos reset text mentions Spot/Futures
    assert "Spot · Futures" in html
