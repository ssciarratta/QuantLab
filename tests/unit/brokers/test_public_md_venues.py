"""Tests unitarios — public MD OKX / Bybit / Hyperliquid (sin red)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from quantlab.brokers.bybit.public_md import BybitPublicMdClient
from quantlab.brokers.hyperliquid.public_md import HyperliquidPublicMdClient
from quantlab.brokers.okx.public_md import MAX_KLINES_TOTAL, OkxPublicMdClient
from quantlab.core.exceptions import ValidationError


def _okx_row(i: int, *, base_ms: int = 1_700_000_000_000) -> list[str]:
    t0 = base_ms + i * 3_600_000
    px = str(100 + i)
    return [str(t0), px, px, px, px, "10", "0", "0", "1"]


def _bybit_row(i: int, *, base_ms: int = 1_700_000_000_000) -> list[str]:
    t0 = base_ms + i * 3_600_000
    px = str(200 + i)
    return [str(t0), px, px, px, px, "5", "1000"]


def _hl_candle(i: int, *, base_ms: int = 1_700_000_000_000) -> dict[str, object]:
    t0 = base_ms + i * 3_600_000
    t1 = t0 + 3_599_999
    px = str(300 + i)
    return {"t": t0, "T": t1, "o": px, "h": px, "l": px, "c": px, "v": "7"}


# --- OKX ---


def test_okx_klines_parse_single_page() -> None:
    client = OkxPublicMdClient()
    payload = {"code": "0", "msg": "", "data": [_okx_row(i) for i in range(5)]}
    client._get_json = MagicMock(return_value=payload)  # type: ignore[method-assign]
    bars = client.klines("BTC-USDT-SWAP", interval="1h", limit=5)
    assert len(bars) == 5
    assert bars[0].instrument_id == "OKX:BTC-USDT-SWAP"
    assert bars[0].timeframe == "1h"
    assert bars[0].open == Decimal("100")
    assert bars[0].timestamp_open < bars[-1].timestamp_open


def test_okx_klines_paginates_with_after() -> None:
    client = OkxPublicMdClient()
    page1 = [_okx_row(i, base_ms=2_000_000) for i in range(300, 600)]
    page2 = [_okx_row(i, base_ms=2_000_000) for i in range(250, 300)]
    calls: list[str] = []

    def fake_get(path: str) -> dict[str, object]:
        calls.append(path)
        if "after=" not in path:
            return {"code": "0", "data": page1}
        return {"code": "0", "data": page2}

    client._get_json = fake_get  # type: ignore[method-assign]
    bars = client.klines("ETH-USDT-SWAP", interval="1h", limit=350)
    assert len(bars) == 350
    assert len(calls) >= 2
    assert "after=" in calls[1]
    assert "bar=1H" in calls[0]


def test_okx_klines_rejects_insufficient() -> None:
    client = OkxPublicMdClient()
    client._get_json = MagicMock(  # type: ignore[method-assign]
        return_value={"code": "0", "data": [_okx_row(0), _okx_row(1)]}
    )
    with pytest.raises(ValidationError, match="insuficientes"):
        client.klines("BTC-USDT-SWAP", interval="1h", limit=3)


def test_okx_funding_rates() -> None:
    client = OkxPublicMdClient()
    client._get_json = MagicMock(  # type: ignore[method-assign]
        return_value={
            "code": "0",
            "data": [
                {"fundingRate": "0.0001"},
                {"fundingRate": "-0.0002"},
            ],
        }
    )
    rates = client.funding_rates("BTC-USDT-SWAP", limit=2)
    assert rates == [Decimal("0.0001"), Decimal("-0.0002")]


# --- Bybit ---


def test_bybit_klines_reverses_newest_first() -> None:
    client = BybitPublicMdClient()
    # newest first: i=4,3,2,1,0
    rows = [_bybit_row(i) for i in reversed(range(5))]
    payload = {
        "retCode": 0,
        "retMsg": "OK",
        "result": {"symbol": "BTCUSDT", "category": "linear", "list": rows},
    }
    client._get_json = MagicMock(return_value=payload)  # type: ignore[method-assign]
    bars = client.klines("BTCUSDT", interval="1h", limit=5)
    assert len(bars) == 5
    assert bars[0].instrument_id == "BYB:BTCUSDT"
    assert bars[0].timestamp_open < bars[-1].timestamp_open
    assert bars[0].close == Decimal("200")
    assert bars[-1].close == Decimal("204")


def test_bybit_klines_interval_mapping() -> None:
    client = BybitPublicMdClient()
    client._get_json = MagicMock(  # type: ignore[method-assign]
        return_value={
            "retCode": 0,
            "retMsg": "OK",
            "result": {"list": [_bybit_row(i) for i in range(3)]},
        }
    )
    client.klines("ETHUSDT", interval="15m", limit=3)
    path = client._get_json.call_args[0][0]  # type: ignore[attr-defined]
    assert "interval=15" in path
    assert "category=linear" in path


def test_bybit_klines_paginates_with_end() -> None:
    client = BybitPublicMdClient()
    page1 = [_bybit_row(i, base_ms=2_000_000) for i in range(1000, 2000)]
    page2 = [_bybit_row(i, base_ms=2_000_000) for i in range(800, 1000)]
    page1_api = list(reversed(page1))
    page2_api = list(reversed(page2))
    calls: list[str] = []

    def fake_get(path: str) -> dict[str, object]:
        calls.append(path)
        rows = page1_api if "end=" not in path else page2_api
        return {
            "retCode": 0,
            "retMsg": "OK",
            "result": {"symbol": "BTCUSDT", "category": "linear", "list": rows},
        }

    client._get_json = fake_get  # type: ignore[method-assign]
    bars = client.klines("BTCUSDT", interval="1h", limit=1200)
    assert len(bars) == 1200
    assert len(calls) >= 2
    assert "end=" in calls[1]
    assert bars[0].timestamp_open < bars[-1].timestamp_open
    assert bars[0].instrument_id == "BYB:BTCUSDT"


def test_bybit_funding_rates() -> None:
    client = BybitPublicMdClient()
    client._get_json = MagicMock(  # type: ignore[method-assign]
        return_value={
            "retCode": 0,
            "result": {
                "list": [{"fundingRate": "0.0003"}, {"fundingRate": "0.0001"}]
            },
        }
    )
    rates = client.funding_rates("BTCUSDT", limit=2)
    assert rates == [Decimal("0.0003"), Decimal("0.0001")]


# --- Hyperliquid ---


def test_hyperliquid_klines_parse() -> None:
    client = HyperliquidPublicMdClient()
    client._post_json = MagicMock(  # type: ignore[method-assign]
        return_value=[_hl_candle(i) for i in range(4)]
    )
    bars = client.klines("BTC", interval="1h", limit=4)
    assert len(bars) == 4
    assert bars[0].instrument_id == "HL:BTC"
    assert bars[0].open == Decimal("300")
    assert bars[0].timestamp_open.tzinfo == UTC
    assert bars[0].timestamp_close >= bars[0].timestamp_open


def test_hyperliquid_klines_sends_candle_snapshot() -> None:
    client = HyperliquidPublicMdClient()
    client._post_json = MagicMock(  # type: ignore[method-assign]
        return_value=[_hl_candle(i) for i in range(3)]
    )
    client.klines("ETH", interval="4h", limit=3)
    body = client._post_json.call_args[0][0]  # type: ignore[attr-defined]
    assert body["type"] == "candleSnapshot"
    assert body["req"]["coin"] == "ETH"
    assert body["req"]["interval"] == "4h"
    assert body["req"]["endTime"] > body["req"]["startTime"]


def test_hyperliquid_funding_rates() -> None:
    client = HyperliquidPublicMdClient()
    client._post_json = MagicMock(  # type: ignore[method-assign]
        return_value=[
            {"fundingRate": "0.00005", "time": 1},
            {"fundingRate": "0.00010", "time": 2},
        ]
    )
    rates = client.funding_rates("BTC", limit=2)
    assert rates == [Decimal("0.00005"), Decimal("0.00010")]
    body = client._post_json.call_args[0][0]  # type: ignore[attr-defined]
    assert body["type"] == "fundingHistory"
    assert body["coin"] == "BTC"


def test_hyperliquid_klines_preserves_hip3_case() -> None:
    client = HyperliquidPublicMdClient()
    client._post_json = MagicMock(  # type: ignore[method-assign]
        return_value=[_hl_candle(i) for i in range(3)]
    )
    client.klines("xyz:GOLD", interval="1h", limit=3)
    body = client._post_json.call_args[0][0]  # type: ignore[attr-defined]
    assert body["req"]["coin"] == "xyz:GOLD"


def test_hyperliquid_list_all_includes_builder_dex() -> None:
    client = HyperliquidPublicMdClient()

    def fake_post(body: dict) -> object:
        t = body.get("type")
        if t == "perpDexs":
            return [None, {"name": "xyz", "fullName": "XYZ"}]
        if t == "metaAndAssetCtxs":
            dex = body.get("dex", "")
            if dex == "":
                return [{"universe": [{"name": "BTC", "maxLeverage": 50, "szDecimals": 5}]}]
            if dex == "xyz":
                return [
                    {
                        "universe": [
                            {"name": "xyz:GOLD", "maxLeverage": 20, "szDecimals": 3},
                            {"name": "xyz:TSLA", "maxLeverage": 10, "szDecimals": 2},
                        ]
                    }
                ]
        raise AssertionError(body)

    client._post_json = MagicMock(side_effect=fake_post)  # type: ignore[method-assign]
    rows = client.list_all_perp_universes(include_delisted=False)
    names = {r["name"] for r in rows}
    assert "BTC" in names
    assert "xyz:GOLD" in names
    gold = next(r for r in rows if r["name"] == "xyz:GOLD")
    assert gold["dex"] == "xyz"
    assert gold["dex_full_name"] == "XYZ"


def test_okx_rejects_over_max_total() -> None:
    client = OkxPublicMdClient()
    with pytest.raises(ValidationError, match=str(MAX_KLINES_TOTAL)):
        client.klines("BTC-USDT-SWAP", interval="1h", limit=MAX_KLINES_TOTAL + 1)
