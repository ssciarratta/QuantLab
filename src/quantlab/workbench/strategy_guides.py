"""Guías paso a paso exhaustivas por strategy_id (UI Simulador / API)."""

from __future__ import annotations

from typing import Any

from quantlab.workbench.strategy_catalog import STRATEGY_CATALOG, StrategyMeta

FAMILY_LABELS_ES: dict[str, str] = {
    "demo": "Demo / aprendizaje",
    "trend": "Tendenciales",
    "momentum": "Momentum",
    "mean_reversion": "Reversión a la media",
    "market_making": "Market making",
    "stats": "Estadísticas / cuant",
    "ml": "Machine learning (stubs)",
    "multi_asset": "Multi-activo (stubs)",
    "microstructure": "Microestructura (stubs)",
    "arbitrage": "Arbitraje (stubs)",
    "options": "Opciones / vol (stubs)",
}

_LAB_COMMON = [
    "Motor lab bar-based (5A): una decisión por vela OHLCV.",
    "Long-only en classic: señal >0 compra; señal ≤0 cierra a flat (no short neto).",
    "Fills: MARKET al close de la vela o LIMIT si el OHLC toca el precio.",
    "Fees: Simulador compare usa taker_bps del venue; Guided default ≈ Binance Spot VIP0.",
    "LIVE producción bloqueado (LIVE_BLOCKED=True). Paper/demo ≠ exchange real.",
]


def _params_lines(meta: StrategyMeta) -> list[str]:
    out: list[str] = []
    for k, v in meta.default_params.items():
        out.append(f"{k} = {v!s} (default del catálogo; se puede override en params).")
    if not out:
        out.append("Sin parámetros publicados en el catálogo.")
    return out


def _guide(
    *,
    idea: str,
    steps: list[str],
    when_buy: str,
    when_sell: str,
    params: list[str],
    risks: list[str],
    lab_notes: list[str] | None = None,
    runnable_note: str | None = None,
) -> dict[str, Any]:
    return {
        "idea": idea,
        "steps": steps,
        "when_buy": when_buy,
        "when_sell": when_sell,
        "params_explained": params,
        "risks": risks,
        "lab_notes": list(_LAB_COMMON) + list(lab_notes or []),
        "runnable_note": runnable_note,
    }


# Guías específicas (exhaustivas) — el resto usa plantilla por familia.
_GUIDES: dict[str, dict[str, Any]] = {
    "dummy": _guide(
        idea=(
            "Estrategia de humo para validar el pipeline. En cada barra emite un PLACE "
            "con precio/cantidad fijos (no mira el mercado)."
        ),
        steps=[
            "1) Llega una barra OHLCV al motor.",
            "2) Dummy ignora open/high/low/close/volume.",
            "3) Emite OrderIntent PLACE (LIMIT o según params) con price y quantity del catálogo.",
            "4) El simulado intenta fill; si el precio LIMIT no toca el OHLC, puede no llenar.",
            "5) Repite en la barra siguiente (no hay ‘una sola vez’).",
        ],
        when_buy="Siempre intenta colocar la orden configurada (no es señal de mercado).",
        when_sell="No gestiona salida lógica; depende de fills y del portfolio.",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "dummy")),
        risks=[
            "No tiene edge: solo prueba wiring UI → API → motor.",
            "Puede acumular intents sin sentido económico.",
        ],
        lab_notes=["Usar solo para aprender el panel, no para comparar venues."],
    ),
    "buy_once": _guide(
        idea=(
            "Compra una sola vez en la primera barra útil y después no vuelve a comprar. "
            "Sirve para ver fees, capital y un fill limpio."
        ),
        steps=[
            "1) Primera barra: si aún no compró, emite BUY MARKET (o equivalente) por quantity.",
            "2) Marca internamente que ya compró.",
            "3) Barras siguientes: NO_ACTION (no vende automáticamente).",
            "4) El equity se mueve con el mark-to-market del inventario + fees del fill.",
            "5) Al final del backtest seguís long hasta que el motor liquida la sesión.",
        ],
        when_buy="Solo en la primera oportunidad (barra 1 del run).",
        when_sell="No vende por señal; cierre implícito al terminar el experimento / flat manual.",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "buy_once")),
        risks=["Sesgo de punto de entrada: una sola compra al inicio del sample."],
    ),
    "ma_crossover": _guide(
        idea=(
            "Tendencia por cruce de medias móviles simples (SMA). Cuando la rápida supera "
            "a la lenta → long; cuando se corta hacia abajo → flat."
        ),
        steps=[
            "1) Acumula closes de cada barra.",
            "2) Calcula SMA(fast) y SMA(slow) cuando hay historial suficiente.",
            "3) Señal +1 si SMA_fast > SMA_slow; 0 si no.",
            "4) Si señal +1 y posición ≤0 → BUY quantity.",
            "5) Si señal 0 y posición >0 → SELL para flat.",
            "6) Sin historial (warmup) → no opera.",
        ],
        when_buy="SMA rápida cruza o está por encima de la lenta.",
        when_sell="SMA rápida vuelve por debajo de la lenta (cierra long).",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "ma_crossover")),
        risks=[
            "Retraso en rangos laterales (whipsaw).",
            "fast/slow cortos → más trades y fees; largos → menos reacciones.",
        ],
    ),
    "ema": _guide(
        idea="Igual que MA crossover pero con EMA (más peso en precios recientes).",
        steps=[
            "1) Actualiza EMA_fast y EMA_slow en cada close (alpha=2/(n+1)).",
            "2) Señal long si EMA_fast > EMA_slow.",
            "3) Compra al pasar a long; vende a flat al cortar abajo.",
        ],
        when_buy="EMA rápida > EMA lenta.",
        when_sell="EMA rápida ≤ EMA lenta.",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "ema")),
        risks=["Más sensible al ruido que SMA de misma longitud."],
    ),
    "donchian_breakout": _guide(
        idea="Ruptura del canal de Donchian: compra si el close supera el máximo de N barras.",
        steps=[
            "1) Mantiene high/low de las últimas `channel` barras.",
            "2) Señal long si close > max(highs previos del canal).",
            "3) Sale a flat si close < min(lows del canal) (según implementación classic).",
            "4) Warmup hasta completar el canal.",
        ],
        when_buy="Close rompe el techo Donchian.",
        when_sell="Close rompe el piso Donchian / señal flat.",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "donchian_breakout")),
        risks=["Falsas rupturas en mercados choppy."],
    ),
    "turtle": _guide(
        idea="Variante Turtle: entrada por ruptura N-bar y salida por canal más corto.",
        steps=[
            "1) Canal de entrada (`entry` barras) y de salida (`exit` barras).",
            "2) Entra long al romper máximo de entrada.",
            "3) Sale al romper mínimo de salida (o señal flat).",
            "4) Quantity fija por trade (sin units Turtle reales de riesgo %).",
        ],
        when_buy="Ruptura al alza del canal de entrada.",
        when_sell="Ruptura a la baja del canal de salida.",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "turtle")),
        risks=["Simplificación lab: no replica size por ATR ni reglas multi-unit originales."],
    ),
    "supertrend": _guide(
        idea="Sigue SuperTrend (ATR + banda); dirección define long/flat.",
        steps=[
            "1) Estima ATR y banda SuperTrend.",
            "2) Dirección alcista → señal long; bajista → flat.",
            "3) Compra/vende al cambiar de dirección.",
        ],
        when_buy="SuperTrend en modo alcista.",
        when_sell="Cambia a modo bajista / flat.",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "supertrend")),
        risks=["Depende de ATR: shocks de vol pueden voltear tarde o temprano."],
    ),
    "macd": _guide(
        idea="MACD (EMA rápida − lenta) vs línea señal; histograma cruza → long/flat.",
        steps=[
            "1) Actualiza EMA fast/slow y línea señal.",
            "2) MACD = fast − slow; compara con señal.",
            "3) Long si MACD > señal; flat si no.",
        ],
        when_buy="MACD cruza por encima de la señal.",
        when_sell="MACD cae por debajo de la señal.",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "macd")),
        risks=["Clásico lag en tendencias fuertes y whipsaw en rango."],
    ),
    "momentum": _guide(
        idea="Momentum simple: si el close sube vs lookback, mantiene/compra long.",
        steps=[
            "1) Compara close[t] vs close[t−lookback].",
            "2) Si retorno positivo → long; si no → flat.",
            "3) Emite BUY/SELL según cambio de posición.",
        ],
        when_buy="Precio por encima del close de hace lookback barras.",
        when_sell="Momentum deja de ser positivo.",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "momentum")),
        risks=["Lookback corto = ruido; largo = atraso."],
        lab_notes=["En lab backtest, momentum default lookback=2 si no viene en params."],
    ),
    "bollinger": _guide(
        idea="Reversión a bandas de Bollinger: compra cerca de banda inferior, flat en superior.",
        steps=[
            "1) SMA y desviación → bandas ±k·σ.",
            "2) Close ≤ banda inferior → señal long.",
            "3) Close ≥ banda superior → flat / salida.",
        ],
        when_buy="Precio en o bajo la banda inferior.",
        when_sell="Precio alcanza banda superior (o mid, según señal).",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "bollinger")),
        risks=["En tendencia fuerte la banda inferior puede seguir bajando (cuchillo cayendo)."],
    ),
    "rsi_reversion": _guide(
        idea="RSI: sobreventa (<30) compra; sobrecompra (>70) sale.",
        steps=[
            "1) Calcula RSI sobre window de closes.",
            "2) RSI < 30 → long; RSI > 70 → flat.",
            "3) Zona media: mantiene estado previo / flat según implementación.",
        ],
        when_buy="RSI en zona de sobreventa.",
        when_sell="RSI en zona de sobrecompra.",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "rsi_reversion")),
        risks=["En tendencias, RSI puede quedarse extremo mucho tiempo."],
    ),
    "inventory_mm": _guide(
        idea=(
            "Market maker con skew por inventario: cotiza bid/ask alrededor del mid "
            "y sesga precios para no acumular stock."
        ),
        steps=[
            "1) El adapter bar inyecta best_bid/ask sintéticos desde close ± half_spread.",
            "2) Lee inventario del portfolio.",
            "3) Calcula quotes con skew (si largo, baja bid/ask para vender; viceversa).",
            "4) Emite LIMIT bid y/o ask.",
            "5) Fill si el OHLC de la barra toca el LIMIT.",
        ],
        when_buy="Cuando el bid cotizado es tocado por el mercado (barra).",
        when_sell="Cuando el ask cotizado es tocado.",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "inventory_mm")),
        risks=[
            "Sin L2 real: el book es sintético desde la vela.",
            "Adverse selection no modelada con trades agresivos reales.",
        ],
        lab_notes=["Factory mm + BarSyntheticBookAdapter en paper/lab."],
    ),
    "avellaneda_stoikov": _guide(
        idea="Cotizador estilo Avellaneda–Stoikov (reserva + spread óptimo) en simulación bar.",
        steps=[
            "1) Estima mid y volatilidad proxy.",
            "2) Calcula reservation price y optimal spread.",
            "3) Publica LIMIT bid/ask.",
            "4) Fills por toque OHLC; inventario actualiza la reserva.",
        ],
        when_buy="Fill en bid cotizado.",
        when_sell="Fill en ask cotizado.",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "avellaneda_stoikov")),
        risks=["MVP simulado: no es el AS completo de continuous time + intensity."],
    ),
}


def _family_template(meta: StrategyMeta) -> dict[str, Any]:
    fam = meta.family
    runnable = meta.runnable
    stub_note = None if runnable else (
        "STUB research: aparece en catálogo pero assert_runnable falla — "
        "no hay factory ejecutable completa en lab aún."
    )
    idea = meta.description or f"Estrategia familia {fam}."
    if fam == "trend":
        steps = [
            "1) Lee OHLCV barra a barra.",
            "2) Calcula indicador de tendencia (medias, canal, MACD, SuperTrend…).",
            "3) Señal long si la tendencia es alcista según el indicador.",
            "4) Compra quantity al pasar a long; vende a flat al perder tendencia.",
            "5) Warmup: no opera hasta tener barras suficientes para el indicador.",
        ]
        when_buy = "Indicador de tendencia en modo alcista / ruptura alcista."
        when_sell = "Indicador vuelve a flat o rompe soporte de salida."
    elif fam == "momentum":
        steps = [
            "1) Mide fuerza relativa del precio (ROC, RSI momentum, volumen, etc.).",
            "2) Si el momentum supera umbral → long.",
            "3) Si se agota → flat.",
            "4) Emite BUY/SELL según cambio de posición.",
        ]
        when_buy = "Momentum positivo / ruptura con volumen según el id."
        when_sell = "Momentum deja de confirmar."
    elif fam == "mean_reversion":
        steps = [
            "1) Estima un ‘valor justo’ (SMA, VWAP, z-score, bandas).",
            "2) Si el precio está barato vs justo → long.",
            "3) Si vuelve al justo o se va caro → flat.",
        ]
        when_buy = "Desvío a la baja vs media/banda."
        when_sell = "Reversión completada o overshoot alcista."
    elif fam == "market_making":
        steps = [
            "1) Mid sintético desde close (± spread).",
            "2) Calcula bid/ask con reglas MM (spread, skew, niveles).",
            "3) Publica LIMIT; fill si la vela toca.",
            "4) Inventario sesga las próximas cotizaciones.",
        ]
        when_buy = "Fill bid."
        when_sell = "Fill ask."
    elif fam == "stats":
        steps = [
            "1) Proxy estadístico sobre una serie de closes "
            "(pairs/coint/Kalman simplificados).",
            "2) Señal long/flat según residual o filtro.",
            "3) Ejecuta quantity fija al cambiar señal.",
        ]
        when_buy = "Residual / filtro indica infra-precio."
        when_sell = "Residual normalizado o señal flat."
    else:
        steps = [
            "1) Esta familia está modelada como research stub o proxy bar.",
            "2) Si runnable=false: no se puede correr en backtest lab hasta implementar factory.",
            "3) Si runnable=true: sigue el patrón long/flat del motor 5A con su signal_kind.",
            f"4) Descripción catálogo: {meta.description}",
        ]
        when_buy = "Según signal_kind / factory (ver código classic_bar o mm)."
        when_sell = "Según señal flat / salida."

    risks = [
        "Research-safe: resultados de lab ≠ rentabilidad futura.",
        "Una sola serie OHLCV: no modela multi-venue ni L2 salvo adapters MM.",
    ]
    if not runnable:
        risks.insert(0, "No ejecutable hoy (stub).")

    return _guide(
        idea=idea,
        steps=steps,
        when_buy=when_buy,
        when_sell=when_sell,
        params=_params_lines(meta),
        risks=risks,
        lab_notes=[
            f"Familia UI: {FAMILY_LABELS_ES.get(fam, fam)}.",
            f"factory={meta.factory}; signal_kind={meta.signal_kind!r}.",
        ],
        runnable_note=stub_note,
    )


def get_strategy_guide(strategy_id: str) -> dict[str, Any]:
    """Devuelve guía serializable para un id del catálogo."""
    meta = next((m for m in STRATEGY_CATALOG if m.id == strategy_id), None)
    if meta is None:
        raise KeyError(strategy_id)
    base = _GUIDES.get(strategy_id) or _family_template(meta)
    return {
        "id": meta.id,
        "name": meta.name,
        "family": meta.family,
        "family_label_es": FAMILY_LABELS_ES.get(meta.family, meta.family),
        "runnable": meta.runnable,
        "tags": list(meta.tags),
        "description": meta.description,
        "default_params": dict(meta.default_params),
        **base,
    }


def attach_guides_to_catalog_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Enriquece filas de list_strategy_catalog con how_it_works."""
    out: list[dict[str, Any]] = []
    for row in rows:
        sid = str(row["id"])
        guide = get_strategy_guide(sid)
        enriched = dict(row)
        enriched["family_label_es"] = guide["family_label_es"]
        enriched["how_it_works"] = {
            "idea": guide["idea"],
            "steps": guide["steps"],
            "when_buy": guide["when_buy"],
            "when_sell": guide["when_sell"],
            "params_explained": guide["params_explained"],
            "risks": guide["risks"],
            "lab_notes": guide["lab_notes"],
            "runnable_note": guide.get("runnable_note"),
        }
        out.append(enriched)
    return out


__all__ = [
    "FAMILY_LABELS_ES",
    "attach_guides_to_catalog_rows",
    "get_strategy_guide",
]
