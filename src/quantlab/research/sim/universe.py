"""Universo multi-producto para Simulador (crypto + A3 granos + meta contrato)."""

from __future__ import annotations

from typing import Any

# Curado lab crypto: display estable sin red.
SIM_COINS: tuple[dict[str, str], ...] = (
    {"id": "BTC", "name": "Bitcoin", "label": "Bitcoin (BTC)"},
    {"id": "ETH", "name": "Ethereum", "label": "Ethereum (ETH)"},
    {"id": "SOL", "name": "Solana", "label": "Solana (SOL)"},
    {"id": "BNB", "name": "BNB", "label": "BNB (BNB)"},
    {"id": "XRP", "name": "XRP", "label": "XRP (XRP)"},
    {"id": "ADA", "name": "Cardano", "label": "Cardano (ADA)"},
    {"id": "DOGE", "name": "Dogecoin", "label": "Dogecoin (DOGE)"},
    {"id": "AVAX", "name": "Avalanche", "label": "Avalanche (AVAX)"},
    {"id": "LINK", "name": "Chainlink", "label": "Chainlink (LINK)"},
    {"id": "DOT", "name": "Polkadot", "label": "Polkadot (DOT)"},
    {"id": "MATIC", "name": "Polygon", "label": "Polygon (MATIC)"},
    {"id": "NEAR", "name": "NEAR Protocol", "label": "NEAR Protocol (NEAR)"},
    {"id": "ATOM", "name": "Cosmos", "label": "Cosmos (ATOM)"},
    {"id": "LTC", "name": "Litecoin", "label": "Litecoin (LTC)"},
    {"id": "UNI", "name": "Uniswap", "label": "Uniswap (UNI)"},
    {"id": "APT", "name": "Aptos", "label": "Aptos (APT)"},
    {"id": "ARB", "name": "Arbitrum", "label": "Arbitrum (ARB)"},
    {"id": "OP", "name": "Optimism", "label": "Optimism (OP)"},
    {"id": "SUI", "name": "Sui", "label": "Sui (SUI)"},
    {"id": "PEPE", "name": "Pepe", "label": "Pepe (PEPE)"},
)

# Futuros A3 / Matba Rofex (símbolos de ejemplo lab + fake). Con MD env se
# enriquecen con get_all_instruments cuando esté disponible.
A3_CURATED_PRODUCTS: tuple[dict[str, Any], ...] = (
    {
        "id": "SOJ/MAY26",
        "name": "Soja Rosario MAY26",
        "label": "Soja Rosario MAY26 (SOJ/MAY26)",
        "underlying_name": "Soja",
        "contract_kind": "dated",
        "expiry": "2026-05-01",
        "expiry_label": "vence MAY26",
        "has_daily_variation": True,
        "margin_note": (
            "Para operar Soja Rosario MAY26 el contrato exige margen "
            "(inicial/mantenimiento según cámara Matba Rofex) y está sujeto a "
            "diferencias diarias (mark-to-market / variación de margen). "
            "No es un perpetuo crypto: hay vencimiento y liquidación diaria."
        ),
    },
    {
        "id": "SOJ/JUL26",
        "name": "Soja Rosario JUL26",
        "label": "Soja Rosario JUL26 (SOJ/JUL26)",
        "underlying_name": "Soja",
        "contract_kind": "dated",
        "expiry": "2026-07-01",
        "expiry_label": "vence JUL26",
        "has_daily_variation": True,
        "margin_note": (
            "Para operar Soja Rosario JUL26 el margen lo fija la cámara y el "
            "contrato está sujeto a diferencias diarias hasta el vencimiento."
        ),
    },
    {
        "id": "MAI/JUL26",
        "name": "Maíz Rosario JUL26",
        "label": "Maíz Rosario JUL26 (MAI/JUL26)",
        "underlying_name": "Maíz",
        "contract_kind": "dated",
        "expiry": "2026-07-01",
        "expiry_label": "vence JUL26",
        "has_daily_variation": True,
        "margin_note": (
            "Para operar Maíz Rosario JUL26 hace falta margen de cámara y hay "
            "diferencias diarias. Revisá el margen vigente en Matba Rofex / A3."
        ),
    },
    {
        "id": "MAI/DIC25",
        "name": "Maíz Rosario DIC25",
        "label": "Maíz Rosario DIC25 (MAI/DIC25)",
        "underlying_name": "Maíz",
        "contract_kind": "dated",
        "expiry": "2025-12-01",
        "expiry_label": "vence DIC25",
        "has_daily_variation": True,
        "margin_note": (
            "Maíz DIC25: margen de cámara + diferencias diarias hasta vencimiento."
        ),
    },
    {
        "id": "TRI/DIC25",
        "name": "Trigo Rosario DIC25",
        "label": "Trigo Rosario DIC25 (TRI/DIC25)",
        "underlying_name": "Trigo",
        "contract_kind": "dated",
        "expiry": "2025-12-01",
        "expiry_label": "vence DIC25",
        "has_daily_variation": True,
        "margin_note": (
            "Para operar Trigo Rosario DIC25 el margen es el de cámara Matba Rofex "
            "y el contrato está sujeto a diferencias diarias."
        ),
    },
    {
        "id": "TRI/MAR26",
        "name": "Trigo Rosario MAR26",
        "label": "Trigo Rosario MAR26 (TRI/MAR26)",
        "underlying_name": "Trigo",
        "contract_kind": "dated",
        "expiry": "2026-03-01",
        "expiry_label": "vence MAR26",
        "has_daily_variation": True,
        "margin_note": (
            "Trigo MAR26: margen de cámara + diferencias diarias (no perp)."
        ),
    },
    {
        "id": "DLR/DIC25",
        "name": "Dólar futuro DIC25",
        "label": "Dólar futuro DIC25 (DLR/DIC25)",
        "underlying_name": "USD",
        "contract_kind": "dated",
        "expiry": "2025-12-01",
        "expiry_label": "vence DIC25",
        "has_daily_variation": True,
        "margin_note": (
            "DLR es futuro de tipo de cambio: margen de cámara y diferencias diarias."
        ),
    },
    {
        "id": "DLR/DIC24",
        "name": "Dólar futuro DIC24",
        "label": "Dólar futuro DIC24 (DLR/DIC24)",
        "underlying_name": "USD",
        "contract_kind": "dated",
        "expiry": "2024-12-01",
        "expiry_label": "vence DIC24",
        "has_daily_variation": True,
        "margin_note": (
            "DLR/DIC24 (lab/fake): margen de cámara + diferencias diarias."
        ),
    },
)

VENUE_LABELS: dict[str, str] = {
    "binance": "Binance",
    "okx": "OKX",
    "bybit": "Bybit",
    "hyperliquid": "Hyperliquid",
    "a3": "A3 / Matba Rofex",
}

VENUE_KINDS: dict[str, str] = {
    "binance": "crypto",
    "okx": "crypto",
    "bybit": "crypto",
    "hyperliquid": "crypto",
    "a3": "futures_grains_fx",
}

_CRYPTO_PERP_MARGIN = (
    "Contrato perpetuo crypto: no vence en una fecha fija. "
    "El margen depende del leverage que elijas. "
    "Puede haber funding periódico; no hay «diferencias diarias» de cámara "
    "como en futuros A3/Matba."
)

_CRYPTO_SPOT_MARGIN = (
    "Spot: comprás/vendés el activo al contado. "
    "Sin vencimiento y sin variación diaria de cámara. "
    "No hay margen de futuro (salvo margen de compra con crédito del venue)."
)


def tradingview_url(*, venue: str, symbol: str, market_type: str) -> str | None:
    """URL de gráfico TradingView (TV no es un mercado: solo visualización)."""
    v = venue.lower()
    sym = symbol.strip().upper()
    if not sym:
        return None
    if v == "binance":
        tv = f"BINANCE:{sym}" if sym.endswith("USDT") else f"BINANCE:{sym}USDT"
        if market_type == "futures" and not sym.endswith(".P"):
            # Perp USDT-M en TV suele ser BINANCE:BTCUSDT.P
            base = sym if sym.endswith("USDT") else f"{sym}USDT"
            tv = f"BINANCE:{base}.P"
        return f"https://www.tradingview.com/chart/?symbol={tv}"
    if v == "okx":
        # BTC-USDT-SWAP → OKX:BTCUSDT.P
        clean = sym.replace("-SWAP", "").replace("-", "")
        return f"https://www.tradingview.com/chart/?symbol=OKX:{clean}.P"
    if v == "bybit":
        base = sym if sym.endswith("USDT") else f"{sym}USDT"
        return f"https://www.tradingview.com/chart/?symbol=BYBIT:{base}.P"
    if v == "hyperliquid":
        return f"https://www.tradingview.com/chart/?symbol=HYPERLIQUID:{sym}USD"
    if v == "a3":
        # Muchos ROFX no están en TV; link de búsqueda genérico
        q = sym.replace("/", "%20")
        return f"https://www.tradingview.com/symbols/search/?search={q}"
    return None


def _crypto_product(
    coin: dict[str, str],
    *,
    venue: str,
    market_type: str,
) -> dict[str, Any]:
    cid = coin["id"]
    mt = market_type
    if mt == "spot":
        kind = "spot"
        expiry_label = "spot (sin vencimiento)"
        has_var = False
        margin = _CRYPTO_SPOT_MARGIN
        sym = f"{cid}USDT" if venue != "hyperliquid" else cid
        if venue == "okx":
            sym = f"{cid}-USDT"
    else:
        kind = "perpetual"
        expiry_label = "perpetuo"
        has_var = False
        margin = _CRYPTO_PERP_MARGIN
        if venue == "okx":
            sym = f"{cid}-USDT-SWAP"
        elif venue == "hyperliquid":
            sym = cid
        else:
            sym = f"{cid}USDT"
    label = coin.get("label") or f"{coin['name']} ({cid})"
    return {
        "id": cid,
        "name": coin["name"],
        "label": f"{label} · {expiry_label}",
        "symbol": sym,
        "contract_kind": kind,
        "expiry": None,
        "expiry_label": expiry_label,
        "has_daily_variation": has_var,
        "margin_note": margin,
        "tradingview_url": tradingview_url(venue=venue, symbol=sym, market_type=mt),
        "source": "curated",
    }


def _a3_products() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in A3_CURATED_PRODUCTS:
        row = dict(p)
        row["symbol"] = p["id"]
        row["tradingview_url"] = tradingview_url(
            venue="a3", symbol=p["id"], market_type="futures"
        )
        row["source"] = "curated_a3"
        out.append(row)
    return out


def _hl_live_products() -> tuple[list[dict[str, Any]], str | None]:
    """Lista todos los perps HL vía metaAndAssetCtxs. (products, error)."""
    try:
        from quantlab.brokers.hyperliquid.public_md import HyperliquidPublicMdClient

        client = HyperliquidPublicMdClient()
        meta = client.list_perp_universe()
    except Exception as exc:  # noqa: BLE001 — frontera red
        return [], str(exc)

    products: list[dict[str, Any]] = []
    for item in meta:
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        max_lev = item.get("max_leverage")
        lev_txt = f" Máx. leverage publicado ≈ {max_lev}x." if max_lev else ""
        products.append(
            {
                "id": name,
                "name": name,
                "label": f"{name} · perpetuo",
                "symbol": name,
                "contract_kind": "perpetual",
                "expiry": None,
                "expiry_label": "perpetuo",
                "has_daily_variation": False,
                "margin_note": _CRYPTO_PERP_MARGIN + lev_txt,
                "max_leverage": max_lev,
                "sz_decimals": item.get("sz_decimals"),
                "tradingview_url": tradingview_url(
                    venue="hyperliquid", symbol=name, market_type="futures"
                ),
                "source": "hl_live",
            }
        )
    products.sort(key=lambda r: str(r["id"]))
    return products, None


def list_sim_universe(
    *,
    market_type: str = "futures",
    hl_live: bool = True,
) -> dict[str, Any]:
    """Catálogo por venue: productos con vencimiento/margen + link TradingView."""
    mt = (market_type or "futures").strip().lower()
    if mt not in ("spot", "futures"):
        mt = "futures"

    products_by_venue: dict[str, list[dict[str, Any]]] = {}
    notes: list[str] = []

    for vid in ("binance", "okx", "bybit", "hyperliquid"):
        if vid == "hyperliquid" and hl_live and mt == "futures":
            live, err = _hl_live_products()
            if live:
                products_by_venue[vid] = live
                notes.append(f"hyperliquid: {len(live)} perps vía metaAndAssetCtxs")
            else:
                products_by_venue[vid] = [
                    _crypto_product(c, venue=vid, market_type=mt) for c in SIM_COINS
                ]
                notes.append(
                    "hyperliquid: fallback curado "
                    + (f"(live falló: {err})" if err else "(live vacío)")
                )
        else:
            products_by_venue[vid] = [
                _crypto_product(c, venue=vid, market_type=mt) for c in SIM_COINS
            ]

    # A3 solo tiene sentido como futuros con vencimiento
    if mt == "futures":
        products_by_venue["a3"] = _a3_products()
        notes.append(
            "a3: catálogo curado soja/maíz/trigo/DLR (lab). "
            "Con MD A3 real (QUANTLAB_A3_MD_READONLY) Guided Lab lista todos los "
            "instrumentos vigentes del ambiente."
        )
    else:
        products_by_venue["a3"] = []
        notes.append("a3: sin spot; usá modo Futuros")

    venues = [
        {
            "id": vid,
            "name": label,
            "label": f"{label} ({vid})",
            "kind": VENUE_KINDS.get(vid, "other"),
            "supports_spot": vid != "a3",
            "supports_futures": True,
            "has_daily_variation_default": vid == "a3",
        }
        for vid, label in VENUE_LABELS.items()
    ]

    # Compat UI vieja: coins = curated crypto
    coins = [dict(c) for c in SIM_COINS]

    return {
        "ok": True,
        "kind": "sim_universe",
        "market_type": mt,
        "coins": coins,
        "products_by_venue": products_by_venue,
        "venues": venues,
        "tradingview_note": (
            "TradingView no es un exchange de QuantLab: es solo el gráfico. "
            "Cada producto trae tradingview_url para corroborar el símbolo a mano."
        ),
        "notes": notes,
        "note": (
            "Elegí venue → producto. Crypto futures = perpetuos; A3 = futuros con "
            "vencimiento y diferencias diarias. underlying/id va a compare."
        ),
    }
