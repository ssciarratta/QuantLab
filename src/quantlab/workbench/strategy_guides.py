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
    (
        "En español simple: el lab mira velas (OHLCV) una por una "
        "y decide comprar, vender o no hacer nada."
    ),
    (
        "Casi todas las estrategias ‘classic’ solo compran (long) o se quedan "
        "en cero (flat): no venden en corto."
    ),
    (
        "Cuando ‘compra’, suele hacerlo al precio de cierre de esa vela "
        "(o un límite si la vela toca el precio)."
    ),
    (
        "Las comisiones las pone el schedule del exchange (VIP0). "
        "Podés verificarlas en el link oficial del panel."
    ),
    "LIVE real sigue bloqueado: esto es investigación / paper, no trading en vivo.",
]

# Recomendaciones generales por familia (fijas; el Alpha Scanner las enriquecerá después).
FAMILY_WHEN_TO_USE: dict[str, list[str]] = {
    "demo": [
        "Usala solo para probar que el panel y el motor responden.",
        "No sirve para decidir si una moneda ‘está buena’.",
    ],
    "trend": [
        "Cuando el mercado tiene dirección clara (sube o baja con fuerza durante muchas velas).",
        "Mejor en temporalidades medias/altas (ej. 1h, 4h, 1d) para filtrar ruido.",
        "Evitala en rangos laterales estrechos: entra y sale demasiado.",
    ],
    "momentum": [
        "Cuando el precio ya se movió con fuerza y querés ‘seguir la ola’ un tramo más.",
        "Útil tras rupturas o noticias que empujan el precio.",
        "Cuidado si el movimiento ya se agotó: podés llegar tarde.",
    ],
    "mean_reversion": [
        "Cuando el precio suele volver a un promedio (bandas, sobrecompra/sobreventa).",
        "Mejor en mercados laterales o con ida y vuelta, no en tendencias fuertes.",
        "En tendencias violentas puede comprar ‘barato’ y seguir bajando.",
    ],
    "market_making": [
        (
            "Cuando hay ida y vuelta frecuente y querés ganar el ‘spread’ "
            "(comprar un poco más abajo / vender un poco más arriba)."
        ),
        "No es una apuesta direccional fuerte.",
        "En lab es un proxy: no es el libro real del exchange.",
    ],
    "stats": [
        "Cuando querés un filtro estadístico (residual, pairs simplificado) sobre una serie.",
        "Requiere entender que es un proxy de research, no arbitraje real multi-venue.",
    ],
    "ml": [
        "Solo como stub de research por ahora: aún no corre completa en el lab.",
        "Cuando exista modelo entrenado, se usará con datos históricos validados.",
    ],
    "multi_asset": [
        "Pensada para varias monedas a la vez; hoy puede ser stub.",
        "Útil cuando compares pares o canastas, no una sola serie aislada.",
    ],
    "microstructure": [
        "Proxies de microestructura sobre OHLC (no libro L2 real todavía).",
        "Usala para explorar ideas, no como señal de producción.",
    ],
    "arbitrage": [
        "Ideas de arbitraje / bases; muchas están en stub.",
        "En lab single-serie no hay true cross-venue arb.",
    ],
    "options": [
        "Proxies de volatilidad/opciones; revisar si está runnable.",
        "No es un pricer de opciones de exchange.",
    ],
}


def _params_lines(meta: StrategyMeta) -> list[str]:
    out: list[str] = []
    for k, v in meta.default_params.items():
        out.append(f"{k} = {v!s} (valor por defecto; se puede cambiar).")
    if not out:
        out.append("Sin parámetros publicados en el catálogo.")
    return out


def _params_summary(meta: StrategyMeta) -> str:
    parts = [f"{k}={v}" for k, v in list(meta.default_params.items())[:6]]
    return ", ".join(parts) if parts else "params por defecto del catálogo"


def _default_example_steps(
    meta: StrategyMeta,
    *,
    when_buy: str,
    when_sell: str,
) -> list[str]:
    """Ejemplo numérico genérico pero concreto para cualquier id."""
    name = meta.name
    sid = meta.id
    ps = _params_summary(meta)
    return [
        f"Abrís Simulador → elegís «{name}» (id={sid}) con {ps}.",
        "En Comparar: BTCUSDT (o la moneda que quieras), intervalo 1h, período 30 días, "
        "capital 10.000 USDT y fees del mercado.",
        f"El lab recorre cada vela. Cuando se cumple: «{when_buy}» → compra "
        f"(cantidad ≈ {meta.default_params.get('quantity', '1')}) y paga fee taker/maker.",
        "Mientras la señal sigue activa, no recompra de más: tu capital sube/baja con el precio.",
        f"Cuando se cumple: «{when_sell}» → vende, vuelve a efectivo y suma la fee de salida.",
        "Al terminar ves en la tabla: PnL neto, fees, margen pico y si te faltó capital.",
    ]


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
    in_plain_words: str | None = None,
    example: str | None = None,
    example_steps: list[str] | None = None,
    when_to_use: list[str] | None = None,
    meta: StrategyMeta | None = None,
) -> dict[str, Any]:
    plain = (in_plain_words or idea).strip()
    ex = (example or "").strip() or (
        "Ejemplo: imaginá BTC a 60.000 en la vela 1. "
        "Si la estrategia dice ‘comprar’, el lab compra ahí y paga fee. "
        "En la vela 40 el precio está 63.000 y dice ‘salir’: vende y vuelve a efectivo. "
        "Entre medias, si no hay señal, no opera (ahorra fees)."
    )
    ex_steps = list(example_steps or [])
    if not ex_steps and meta is not None:
        ex_steps = _default_example_steps(meta, when_buy=when_buy, when_sell=when_sell)
    return {
        "idea": idea,
        "in_plain_words": plain,
        "example": ex,
        "example_steps": ex_steps,
        "when_to_use": list(when_to_use or []),
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
        in_plain_words=(
            "Es un ‘botón de prueba’. No mira si el precio sube o baja: en cada vela "
            "intenta poner la misma orden. Sirve para ver si el panel y el motor responden."
        ),
        example=(
            "Ejemplo: configurás quantity=1 y price=100. En cada vela el lab intenta "
            "comprar 1 unidad a 100. Si la vela nunca toca 100, puede no llenar. "
            "No uses esto para comparar exchanges: no tiene lógica de mercado."
        ),
        steps=[
            "1) Llega una vela (barra) de precios.",
            "2) Dummy no mira open/high/low/close: ignora el mercado.",
            "3) Emite la misma orden (precio y cantidad fijos del catálogo).",
            "4) Si el precio límite no toca la vela, puede no ejecutarse.",
            "5) En la vela siguiente vuelve a intentar lo mismo.",
        ],
        when_buy="Siempre intenta colocar la orden configurada (no es señal de mercado).",
        when_sell="No gestiona una salida inteligente; depende de fills y del portafolio.",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "dummy")),
        risks=[
            "No tiene ventaja: solo prueba el cableado UI → API → motor.",
            "Puede acumular órdenes sin sentido económico.",
        ],
        lab_notes=["Usar solo para aprender el panel, no para comparar venues."],
    ),
    "buy_once": _guide(
        idea=(
            "Compra una sola vez en la primera barra útil y después no vuelve a comprar. "
            "Sirve para ver fees, capital y un fill limpio."
        ),
        in_plain_words=(
            "Compra una vez al arrancar y se queda quieta. Ideal para ver cuánto te cobró "
            "de comisión y cómo se mueve tu capital con el precio, sin mil trades."
        ),
        example=(
            "Ejemplo: capital 10.000 USDT, compra 0,1 BTC en la primera vela a 60.000. "
            "Paga fee de esa compra. Después no vende sola: el valor de tu cuenta sube/baja "
            "con BTC hasta que termina la simulación."
        ),
        steps=[
            "1) Primera vela: si todavía no compró, compra (MARKET o equivalente).",
            "2) Marca ‘ya compré’.",
            "3) Velas siguientes: no hace nada (no vuelve a comprar).",
            "4) Tu capital se mueve con el precio del activo + la fee del fill.",
            "5) Al cerrar el experimento seguís ‘comprado’ hasta el fin del run.",
        ],
        when_buy="Solo en la primera oportunidad (barra 1 del run).",
        when_sell="No vende por señal; el cierre es al terminar el experimento.",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "buy_once")),
        risks=["Todo depende del primer precio: una sola entrada puede ser mala suerte."],
    ),
    "ma_crossover": _guide(
        idea=(
            "Tendencia por cruce de medias móviles simples (SMA). Cuando la rápida supera "
            "a la lenta → long; cuando se corta hacia abajo → flat."
        ),
        in_plain_words=(
            "Mira dos promedios del precio: uno corto (‘rápido’) y uno largo (‘lento’). "
            "Si el corto está por encima del lento, compra. Si se pone por debajo, vende "
            "y se queda en efectivo. Es como seguir la tendencia con un filtro suave."
        ),
        example=(
            "Ejemplo: SMA rápida 10 velas y lenta 30. BTC venía bajando y las medias "
            "estaban ‘rápida abajo’. Un día la rápida cruza arriba → compra. Semanas "
            "después cruza abajo → vende. En un mercado de lado (sin tendencia) puede "
            "comprar y vender mucho y gastar fees."
        ),
        steps=[
            "1) Guarda el cierre de cada vela.",
            "2) Calcula el promedio rápido y el lento cuando ya hay historial.",
            "3) Si promedio rápido > lento → señal de compra.",
            "4) Si no estás comprado y hay señal → compra.",
            "5) Si la señal se apaga y estás comprado → vende (vuelve a efectivo).",
            "6) Al principio (warmup) no opera hasta tener velas suficientes.",
        ],
        when_buy="El promedio rápido está por encima del lento (o acaba de cruzar arriba).",
        when_sell="El promedio rápido vuelve por debajo del lento.",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "ma_crossover")),
        risks=[
            "En mercados laterales compra/vende de más (whipsaw) y come fees.",
            "Promedios muy cortos = más nervioso; muy largos = reacciona tarde.",
        ],
    ),
    "ema": _guide(
        idea="Igual que MA crossover pero con EMA (más peso en precios recientes).",
        in_plain_words=(
            "Igual que el cruce de medias, pero el promedio ‘recuerda’ más el precio de "
            "ayer que el de hace un mes. Reacciona un poco más rápido a cambios."
        ),
        example=(
            "Ejemplo: el precio sube fuerte tres días. La EMA rápida se pone arriba de la "
            "lenta antes que una SMA clásica → compra antes. Si el rally fue falso y "
            "vuelve, también puede vender antes (y pagar más fees)."
        ),
        steps=[
            "1) Actualiza EMA rápida y lenta en cada cierre.",
            "2) Si EMA rápida > lenta → modo compra.",
            "3) Compra al pasar a modo compra; vende al salir.",
        ],
        when_buy="EMA rápida por encima de la lenta.",
        when_sell="EMA rápida por debajo o igual a la lenta.",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "ema")),
        risks=["Más sensible al ruido que una SMA de la misma longitud."],
    ),
    "donchian_breakout": _guide(
        idea="Ruptura del canal de Donchian: compra si el close supera el máximo de N barras.",
        in_plain_words=(
            "Dibuja un ‘techo’ con el máximo de las últimas N velas. Si el precio cierra "
            "por encima de ese techo, compra (ruptura). Si cae por el piso del canal, sale."
        ),
        example=(
            "Ejemplo: canal de 20 velas, techo en 65.000. Una vela cierra en 65.200 → compra. "
            "Si después el piso del canal se rompe a la baja → vende. Sirve en tendencias "
            "claras; en mercados nerviosos hay muchas rupturas falsas."
        ),
        steps=[
            "1) Recuerda máximos y mínimos de las últimas N velas.",
            "2) Si el cierre rompe el techo → señal de compra.",
            "3) Si el cierre rompe el piso → sale a efectivo.",
            "4) Al principio espera a llenar el canal (warmup).",
        ],
        when_buy="El cierre rompe el techo del canal Donchian.",
        when_sell="El cierre rompe el piso del canal / señal flat.",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "donchian_breakout")),
        risks=["Falsas rupturas en mercados laterales."],
    ),
    "turtle": _guide(
        idea="Variante Turtle: entrada por ruptura N-bar y salida por canal más corto.",
        in_plain_words=(
            "Entra cuando el precio rompe un máximo de muchas velas, y sale cuando rompe "
            "un mínimo de un canal más corto. Idea: ‘dejar correr la ganancia, cortar rápido’."
        ),
        example=(
            "Ejemplo: entrada 20 velas, salida 10. Rompe el máximo de 20 → compra. "
            "Si el precio cae y rompe el mínimo de las últimas 10 → vende. "
            "En el lab el tamaño del trade es fijo (no el sistema Turtle original con ATR)."
        ),
        steps=[
            "1) Canal de entrada (más largo) y de salida (más corto).",
            "2) Entra al romper el máximo de entrada.",
            "3) Sale al romper el mínimo de salida.",
            "4) Cantidad fija por trade (simplificado respecto al Turtle clásico).",
        ],
        when_buy="Ruptura al alza del canal de entrada.",
        when_sell="Ruptura a la baja del canal de salida.",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "turtle")),
        risks=["Simplificación lab: no replica size por ATR ni multi-unit originales."],
    ),
    "supertrend": _guide(
        idea="Sigue SuperTrend (ATR + banda); dirección define long/flat.",
        in_plain_words=(
            "Dibuja una línea debajo o arriba del precio según la volatilidad (ATR). "
            "Si el precio está ‘del lado alcista’ de esa línea, compra; si se da vuelta, sale."
        ),
        example=(
            "Ejemplo: BTC sube y SuperTrend queda debajo del precio → estás comprado. "
            "Una caída fuerte hace que la línea se ponga arriba → vende. "
            "En picos de volatilidad puede cambiar de lado tarde o temprano."
        ),
        steps=[
            "1) Estima volatilidad (ATR) y la banda SuperTrend.",
            "2) Modo alcista → compra; bajista → efectivo.",
            "3) Compra/vende solo cuando cambia de modo.",
        ],
        when_buy="SuperTrend en modo alcista.",
        when_sell="Cambia a modo bajista / flat.",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "supertrend")),
        risks=["Depende del ATR: shocks de volatilidad pueden voltear la señal."],
    ),
    "macd": _guide(
        idea="MACD (EMA rápida − lenta) vs línea señal; histograma cruza → long/flat.",
        in_plain_words=(
            "Compara dos promedios exponenciales y mira si su diferencia (MACD) está "
            "por encima o debajo de una ‘línea señal’. Arriba = compra; abajo = sale."
        ),
        example=(
            "Ejemplo: el MACD cruza arriba de su señal → compra ETH. Días después cruza "
            "abajo → vende. En tendencia fuerte funciona; en zigzag lateral hace muchos "
            "cruces y gasta comisiones."
        ),
        steps=[
            "1) Calcula EMA rápida, lenta y la línea señal.",
            "2) MACD = rápida − lenta; se compara con la señal.",
            "3) MACD > señal → compra; si no → efectivo.",
        ],
        when_buy="MACD cruza por encima de la señal.",
        when_sell="MACD cae por debajo de la señal.",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "macd")),
        risks=["Retraso en tendencias y muchos cruces en rango."],
    ),
    "momentum": _guide(
        idea="Momentum simple: si el close sube vs lookback, mantiene/compra long.",
        in_plain_words=(
            "Mira si el precio de hoy está más alto que hace N velas. Si sí, compra o "
            "se queda comprado. Si no, vende. Idea: ‘lo que sube sigue un rato’."
        ),
        example=(
            "Ejemplo: lookback=10. Cierre hace 10 velas = 50.000; hoy = 52.000 → compra. "
            "Si mañana cae a 49.500 vs hace 10 velas → vende. "
            "Lookback chico = más trades; grande = más lento."
        ),
        steps=[
            "1) Compara el cierre de hoy con el de hace N velas.",
            "2) Si subió → modo compra; si no → efectivo.",
            "3) Compra/vende solo cuando cambia el modo.",
        ],
        when_buy="Precio por encima del cierre de hace N velas.",
        when_sell="El momentum deja de ser positivo.",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "momentum")),
        risks=["Lookback corto = ruido; largo = atraso."],
        lab_notes=["En lab backtest, momentum default lookback=2 si no viene en params."],
    ),
    "bollinger": _guide(
        idea="Reversión a bandas de Bollinger: compra cerca de banda inferior, flat en superior.",
        in_plain_words=(
            "Dibuja un ‘tubo’ alrededor del precio promedio. Si el precio toca el borde "
            "de abajo (barato vs el tubo), compra esperando que vuelva al medio. "
            "Si toca el borde de arriba, vende."
        ),
        example=(
            "Ejemplo: banda inferior en 58.000, BTC cierra en 57.800 → compra. "
            "Luego toca la banda superior en 62.000 → vende. "
            "Si el mercado cae en tendencia fuerte, comprar ‘barato’ puede seguir "
            "perdiendo un tiempo (cuchillo cayendo)."
        ),
        steps=[
            "1) Calcula promedio y bandas ± k desviaciones.",
            "2) Cierre en o bajo la banda inferior → compra.",
            "3) Cierre en o sobre la banda superior → vende.",
        ],
        when_buy="Precio en o bajo la banda inferior.",
        when_sell="Precio alcanza la banda superior (o zona de salida).",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "bollinger")),
        risks=["En tendencia fuerte la banda inferior puede seguir bajando."],
    ),
    "rsi_reversion": _guide(
        idea="RSI: sobreventa (<30) compra; sobrecompra (>70) sale.",
        in_plain_words=(
            "El RSI mide si el precio ‘se pasó de acelerado’. Muy bajo (sobreventa) → "
            "compra esperando rebote. Muy alto (sobrecompra) → vende. "
            "En el medio no fuerza operaciones nuevas."
        ),
        example=(
            "Ejemplo: RSI cae a 25 → compra. Sube a 72 → vende. "
            "En un mercado que solo sube, el RSI puede quedarse alto mucho tiempo "
            "y la estrategia vende ‘temprano’ respecto a la tendencia."
        ),
        steps=[
            "1) Calcula RSI con una ventana de cierres.",
            "2) RSI bajo (p.ej. <30) → compra.",
            "3) RSI alto (p.ej. >70) → vende.",
        ],
        when_buy="RSI en zona de sobreventa.",
        when_sell="RSI en zona de sobrecompra.",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "rsi_reversion")),
        risks=["En tendencias, el RSI puede quedarse extremo mucho tiempo."],
    ),
    "inventory_mm": _guide(
        idea=(
            "Market maker con skew por inventario: cotiza bid/ask alrededor del mid "
            "y sesga precios para no acumular stock."
        ),
        in_plain_words=(
            "En vez de ‘apostar dirección’, pone precios de compra y de venta cerca del "
            "medio, como un cambiador. Si ya tiene mucho inventario, sesga para vender "
            "más fácil y no quedar tan cargado."
        ),
        example=(
            "Ejemplo: mid 100. Cotiza compra a 99,8 y venta a 100,2. Si alguien ‘toca’ "
            "99,8 en la vela, compra inventario. Si se llena de stock, baja un poco ambos "
            "precios para incentivar vender. En el lab el libro es sintético desde la vela "
            "(no es el order book real del exchange)."
        ),
        steps=[
            "1) Arma un mid sintético desde el cierre ± spread.",
            "2) Mira cuánto inventario ya tiene.",
            "3) Ajusta bid/ask (skew) para equilibrar inventario.",
            "4) Publica órdenes límite.",
            "5) Si la vela toca el límite, hay fill.",
        ],
        when_buy="Cuando el bid cotizado es tocado por la vela.",
        when_sell="Cuando el ask cotizado es tocado.",
        params=_params_lines(next(m for m in STRATEGY_CATALOG if m.id == "inventory_mm")),
        risks=[
            "Sin libro real L2: el book es sintético desde la vela.",
            "No modela adverse selection de trades agresivos reales.",
        ],
        lab_notes=["Factory mm + BarSyntheticBookAdapter en paper/lab."],
    ),
    "avellaneda_stoikov": _guide(
        idea="Cotizador estilo Avellaneda–Stoikov (reserva + spread óptimo) en simulación bar.",
        in_plain_words=(
            "Market maker ‘con fórmula’: calcula un precio de reserva y un spread según "
            "inventario y volatilidad, y cotiza compra/venta alrededor. Versión simplificada "
            "para velas del lab."
        ),
        example=(
            "Ejemplo: con poco inventario cotiza casi simétrico. Si se llena de compras, "
            "el precio de reserva baja y el ask se pone más atractivo para vender. "
            "No es el modelo AS completo de tiempo continuo."
        ),
        steps=[
            "1) Estima mid y volatilidad aproximada.",
            "2) Calcula precio de reserva y spread.",
            "3) Publica límites bid/ask.",
            "4) Fills si la vela toca; el inventario actualiza la reserva.",
        ],
        when_buy="Fill en el bid cotizado.",
        when_sell="Fill en el ask cotizado.",
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
    plain = (
        f"Forma parte de la familia «{FAMILY_LABELS_ES.get(fam, fam)}». "
        f"{idea} "
        "En el lab decide vela a vela si comprar o volver a efectivo."
    )
    example = (
        f"Ejemplo con «{meta.name}» (params {_params_summary(meta)}): "
        "en BTC 1h, cuando la señal pasa a compra el lab compra al cierre y paga fee; "
        "cuando pasa a salir, vende. Si es stub (runnable=false), "
        "aparece en el catálogo pero todavía no se puede correr en Comparar."
    )
    if fam == "trend":
        steps = [
            "1) Lee el cierre de cada vela en orden.",
            "2) Calcula el indicador de tendencia (medias, canal, MACD, SuperTrend, etc.).",
            "3) Espera el warmup: no opera hasta tener velas suficientes para el indicador.",
            "4) Si la tendencia es alcista → señal de compra.",
            "5) Si no estás comprado y hay señal → compra (cantidad del param quantity).",
            "6) Si pierde la tendencia → vende y queda en efectivo.",
            "7) Si no hay cambio de señal → no opera (no gasta fees de más).",
        ]
        when_buy = "El indicador dice tendencia alcista / ruptura alcista."
        when_sell = "El indicador vuelve a flat o rompe el nivel de salida."
        plain = (
            f"«{meta.name}» es tendencial: intenta comprar cuando el mercado ‘empuja’ "
            "para arriba y salir cuando esa fuerza se corta. No intenta adivinar el piso."
        )
        example = (
            f"Ejemplo «{meta.name}» ({_params_summary(meta)}): el indicador pasa a alcista "
            "en BTC → compra 1 unidad al cierre. Días después pasa a bajista → vende. "
            "Si el mercado solo lateraliza, puede entrar y salir muchas veces y comer fees."
        )
    elif fam == "momentum":
        steps = [
            "1) Mide si el precio viene fuerte (subiendo vs hace N velas / ROC / RSI).",
            "2) Confirma el umbral de momentum según los params.",
            "3) Si el momentum es positivo → señal de compra.",
            "4) Si no estás comprado → compra al cambio de señal.",
            "5) Si el momentum se agota → vende y vuelve a efectivo.",
            "6) Entre señales estables no reopera (evita churn).",
        ]
        when_buy = "Momentum positivo / confirmación según el id."
        when_sell = "Momentum deja de confirmar."
        plain = (
            f"«{meta.name}» es de momentum: compra si el precio ya viene subiendo con fuerza "
            "y sale cuando esa fuerza se corta."
        )
        example = (
            f"Ejemplo «{meta.name}» ({_params_summary(meta)}): el precio está X% arriba "
            "vs el lookback → compra. Si después queda abajo del umbral → vende. "
            "Útil tras rupturas; peligroso si llegás tarde al movimiento."
        )
    elif fam == "mean_reversion":
        steps = [
            "1) Estima un ‘precio justo’ (promedio, bandas Bollinger, z-score, VWAP).",
            "2) Mide qué tan lejos está el cierre respecto a ese justo.",
            "3) Si está ‘barato’ (banda baja / z negativo / RSI oversold) → compra.",
            "4) Espera que el precio vuelva hacia el justo.",
            "5) Si vuelve al justo o se va ‘caro’ → vende.",
            "6) En tendencias fuertes puede comprar barato y seguir cayendo: recortá tamaño.",
        ]
        when_buy = "Precio barato vs media/banda/z-score."
        when_sell = "Volvió al justo o se fue caro / overbought."
        plain = (
            f"«{meta.name}» es de reversión: compra cuando el precio se fue ‘demasiado abajo’ "
            "respecto a su promedio, esperando que vuelva."
        )
        example = (
            f"Ejemplo «{meta.name}» ({_params_summary(meta)}): el precio toca la banda "
            "o z-score de abajo → compra; cuando vuelve al medio o toca la banda de arriba → vende."
        )
    elif fam == "market_making":
        steps = [
            "1) Arma un precio medio sintético desde el cierre de la vela.",
            "2) Calcula bid (compra) y ask (venta) con un half-spread.",
            "3) Ajusta (skew) según inventario: si estás largo, facilitá vender.",
            "4) Publica límites; si la vela toca el precio, hay fill.",
            "5) Actualiza inventario y fees de cada fill.",
            "6) Repite en la siguiente vela (no es el libro L2 real del exchange).",
        ]
        when_buy = "Fill en el bid cotizado."
        when_sell = "Fill en el ask cotizado."
        plain = (
            f"«{meta.name}» es market making: no apuesta fuerte a ‘va a subir’. "
            "Pone precios de compra y venta cerca del medio y gana (en teoría) el spread."
        )
        example = (
            f"Ejemplo «{meta.name}» ({_params_summary(meta)}): mid 100 → compra 99,5 / "
            "vende 100,5. Si se llena de stock, sesga para vender más fácil. "
            "En el lab el book es sintético desde la vela."
        )
    elif fam == "stats":
        steps = [
            "1) Aplica un proxy estadístico sobre cierres (residual, z, filtro).",
            "2) Espera warmup del período estadístico.",
            "3) Si el residual dice infra-precio → compra.",
            "4) Si se normaliza → vende / flat.",
            "5) Opera cantidad fija al cambiar la señal.",
            "6) Recordá: es proxy single-serie, no arbitraje multi-venue real.",
        ]
        when_buy = "El filtro dice infra-precio."
        when_sell = "El filtro se normaliza o pasa a flat."
        plain = (
            f"«{meta.name}» es estadística: usa residuales o filtros "
            "para decidir compra o efectivo sobre una serie."
        )
        example = (
            f"Ejemplo «{meta.name}» ({_params_summary(meta)}): el residual cae bajo el "
            "umbral de entrada → compra; cuando vuelve a 0 → vende."
        )
    else:
        steps = [
            "1) Esta familia puede ser stub de research o proxy por vela.",
            "2) Leé ‘En simple’ y el ejemplo: ahí está la lógica en español.",
            "3) Si runnable=false: todavía no se puede correr en el lab.",
            "4) Si runnable=true: sigue el patrón compra/efectivo del motor.",
            "5) Configurá params del catálogo y probá en Comparar con histórico.",
            f"6) Descripción del catálogo: {meta.description}",
        ]
        when_buy = "Según la señal de esa estrategia (ver ‘En simple’ y el ejemplo)."
        when_sell = "Según la señal de salida / flat."

    risks = [
        "Resultados del lab ≠ garantía de rentabilidad futura.",
        "Una sola serie OHLCV: no es el mercado completo multi-venue ni el libro L2 real.",
    ]
    if not runnable:
        risks.insert(0, "No ejecutable hoy (stub).")

    return _guide(
        idea=idea,
        in_plain_words=plain,
        example=example,
        when_to_use=list(FAMILY_WHEN_TO_USE.get(fam, [])),
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
        meta=meta,
    )


def _ensure_rich_guide(meta: StrategyMeta, base: dict[str, Any]) -> dict[str, Any]:
    """Completa example_steps y refuerza pasos cortos de guías legacy."""
    out = dict(base)
    when_buy = str(out.get("when_buy") or "señal de compra")
    when_sell = str(out.get("when_sell") or "señal de salida")
    if not out.get("when_to_use"):
        out["when_to_use"] = list(FAMILY_WHEN_TO_USE.get(meta.family, []))
    if not out.get("example_steps"):
        out["example_steps"] = _default_example_steps(
            meta, when_buy=when_buy, when_sell=when_sell
        )
    steps = list(out.get("steps") or [])
    if len(steps) < 5:
        steps.extend(
            [
                "Esperá el warmup del indicador antes de la primera orden.",
                "Cada fill paga fee del schedule del exchange (VIP0 / override del panel).",
                "Al final del run revisá PnL neto y margen pico en Comparar.",
            ][: 5 - len(steps)]
        )
        out["steps"] = steps
    ex = str(out.get("example") or "").strip()
    if len(ex) < 90:
        out["example"] = (
            f"Ejemplo «{meta.name}» ({_params_summary(meta)}): "
            f"compra cuando «{when_buy}»; vende cuando «{when_sell}». "
            "Probá BTCUSDT 1h · 30 días en Comparar y mirá fees + PnL neto."
        )
    return out


def get_strategy_guide(strategy_id: str) -> dict[str, Any]:
    """Devuelve guía serializable para un id del catálogo."""
    meta = next((m for m in STRATEGY_CATALOG if m.id == strategy_id), None)
    if meta is None:
        raise KeyError(strategy_id)
    raw = _GUIDES.get(strategy_id) or _family_template(meta)
    base = _ensure_rich_guide(meta, dict(raw))
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
            "in_plain_words": guide["in_plain_words"],
            "example": guide["example"],
            "example_steps": guide.get("example_steps") or [],
            "when_to_use": guide.get("when_to_use") or [],
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
