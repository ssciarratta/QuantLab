"""Klines Binance paginadas (horizonte >1000)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from quantlab.brokers.binance.public_md import (
    MAX_KLINES_TOTAL,
    BinancePublicMdClient,
)
from quantlab.core.exceptions import ValidationError


def _row(i: int, *, base_ms: int = 1_700_000_000_000) -> list[object]:
    t0 = base_ms + i * 60_000
    px = str(100 + i)
    return [t0, px, px, px, px, "10", t0 + 59_999]


def test_klines_rejects_over_max() -> None:
    client = BinancePublicMdClient()
    with pytest.raises(ValidationError, match="3000"):
        client.klines("BTCUSDT", interval="1m", limit=MAX_KLINES_TOTAL + 1)


def test_klines_paginates_beyond_1000() -> None:
    client = BinancePublicMdClient()
    # Dos páginas: 1000 + 200 = 1200
    page1 = [_row(i, base_ms=2_000_000) for i in range(1000, 2000)]  # más recientes
    page2 = [_row(i, base_ms=2_000_000) for i in range(800, 1000)]  # más viejas
    calls: list[str] = []

    def fake_get(path: str) -> list[object]:
        calls.append(path)
        if "endTime=" not in path:
            return page1
        return page2

    client._get_json = fake_get  # type: ignore[method-assign]
    bars = client.klines("ADAUSDT", interval="1m", limit=1200)
    assert len(bars) == 1200
    assert len(calls) >= 2
    assert "endTime=" in calls[1]
    assert bars[0].timestamp_open < bars[-1].timestamp_open
    assert bars[0].instrument_id == "BN:ADAUSDT"


def test_klines_single_page_under_1000() -> None:
    client = BinancePublicMdClient()
    client._get_json = MagicMock(return_value=[_row(i) for i in range(50)])  # type: ignore[method-assign]
    bars = client.klines("BTCUSDT", interval="5m", limit=50)
    assert len(bars) == 50
    client._get_json.assert_called_once()
