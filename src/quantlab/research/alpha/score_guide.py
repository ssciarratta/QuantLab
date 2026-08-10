"""Guía en español del score Alpha Scanner (qué significa 0.5 / 0.8, etc.).

No garantiza rentabilidad: interpreta adecuación al perfil/rama elegido.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from quantlab.workbench.strategy_guides import FAMILY_LABELS_ES, FAMILY_WHEN_TO_USE

# (min inclusivo, max exclusivo, id, título, por qué)
_SCORE_BANDS: tuple[tuple[float, float, str, str, str], ...] = (
    (
        0.0,
        0.30,
        "weak",
        "Débil (0.00–0.29)",
        "Poco alineado con la rama elegida frente al resto del universo. "
        "En general no priorices esta moneda para esa familia; mirá otras con score ≥ 0.50.",
    ),
    (
        0.30,
        0.50,
        "low",
        "Bajo / exploratorio (0.30–0.49)",
        "Hay algo de señal, pero el ajuste es flojo. Sirve para curiosidad o stress-test, "
        "no como primera candidata a probar en el Simulador.",
    ),
    (
        0.50,
        0.75,
        "good",
        "Apto para probar (0.50–0.74)",
        "Rango útil para empezar: la moneda se parece a lo que la rama busca "
        "(mejor que la mitad del universo tipicamente). Probá 1–2 estrategias de la familia "
        "en el Simulador y mirá fees + PnL neto.",
    ),
    (
        0.75,
        0.90,
        "strong",
        "Buen ajuste (0.75–0.89)",
        "Fuerte candidata para esa rama: los factores del perfil (tendencia, liquidez, etc.) "
        "quedan altos vs pares. Ideal para comparar venues/TF con las estrategias sugeridas.",
    ),
    (
        0.90,
        1.01,
        "top",
        "Ajuste alto (0.90–1.00)",
        "De las mejores del universo para esta rama en la ventana escaneada. "
        "Seguí validando: score alto ≠ ganancia asegurada; corré histórico y Monte Carlo.",
    ),
)

_FAMILY_SCORE_WHY: dict[str, str] = {
    "trend": (
        "En Tendenciales un score alto significa que el precio muestra dirección "
        "y calidad de tendencia (no solo ruido) respecto a otras monedas del scan."
    ),
    "momentum": (
        "En Momentum un score alto indica que el precio ya se movió con fuerza "
        "y volumen/tendencia acompañan, frente al resto del universo."
    ),
    "mean_reversion": (
        "En Reversión un score alto favorece monedas con menos ‘empuje’ persistente "
        "y más ida-y-vuelta / liquidez: mejores candidatas a volver a un promedio."
    ),
    "market_making": (
        "En Market making un score alto prioriza liquidez, spread estrecho (proxy) "
        "y volumen estable: el terreno donde un cotizador puede capturar spread."
    ),
    "stats": (
        "En Estadísticas/cuant un score alto apunta a series con funding/OI/volumen "
        "útiles para filtros estadísticos (proxy; no es arbitraje real multi-venue)."
    ),
    "ml": (
        "En ML (stub) el score usa un perfil equilibrado: sirve para rankear, "
        "pero las estrategias aún pueden no ser runnable en el lab."
    ),
    "multi_asset": (
        "En Multi-activo el ranking es proxy single-serie con perfil equilibrado: "
        "elegí monedas líquidas para luego armar canastas/pares en research."
    ),
    "microstructure": (
        "En Microestructura se prioriza liquidez/spread/volumen (proxy OHLC): "
        "mejores para ideas de libro sintético, no L2 real."
    ),
    "arbitrage": (
        "En Arbitraje el score es proxy (funding/liquidez): no detecta arb cross-venue real; "
        "sirve para filtrar monedas líquidas donde estudiar bases/funding."
    ),
    "options": (
        "En Opciones/vol un score alto marca volatilidad + liquidez relativa: "
        "candidatas a proxies de vol, no a un pricer de opciones de exchange."
    ),
}

_FACTOR_LABEL_ES: dict[str, str] = {
    "volatility": "Volatilidad",
    "volume": "Volumen",
    "liquidity": "Liquidez",
    "momentum": "Momentum",
    "trend_quality": "Calidad de tendencia",
    "spread": "Spread (proxy)",
    "depth": "Profundidad (proxy)",
    "volume_quality": "Calidad de volumen",
    "volatility_quality": "Calidad de volatilidad",
    "funding": "Funding",
    "open_interest": "Open interest",
    "persistence": "Persistencia",
}


def _float_or(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def score_band(composite: float) -> dict[str, Any]:
    """Clasifica el composite en una banda legible."""
    x = max(0.0, min(1.0, float(composite)))
    for lo, hi, band_id, title, why in _SCORE_BANDS:
        if lo <= x < hi:
            return {
                "id": band_id,
                "title": title,
                "range": f"{lo:.2f}–{hi - 0.01:.2f}" if hi <= 1.0 else f"{lo:.2f}–1.00",
                "why": why,
                "optimal_for_testing": band_id in ("good", "strong", "top"),
            }
    lo, hi, band_id, title, why = _SCORE_BANDS[-1]
    return {
        "id": band_id,
        "title": title,
        "range": "0.90–1.00",
        "why": why,
        "optimal_for_testing": True,
    }


def _component_lines(score_row: Mapping[str, Any]) -> list[str]:
    comps = score_row.get("components")
    lines: list[str] = []
    if isinstance(comps, Sequence):
        rows: list[tuple[float, str]] = []
        for c in comps:
            if not isinstance(c, Mapping):
                continue
            name = str(c.get("name") or "").strip().lower()
            if not name:
                continue
            label = _FACTOR_LABEL_ES.get(name, name)
            n = _float_or(c.get("normalized"))
            w = _float_or(c.get("weight"))
            contrib = _float_or(c.get("contribution"), n * w)
            avail = c.get("available", True)
            if avail is False:
                rows.append((-1.0, f"{label}: sin dato en esta ventana (no cuenta)."))
            else:
                rows.append(
                    (
                        contrib,
                        f"{label}: {n:.2f} (peso {w:.0%}, aporte ≈ {contrib:.3f})",
                    )
                )
        rows.sort(key=lambda t: -t[0])
        lines = [t[1] for t in rows]
    if lines:
        return lines
    # Legacy sin components
    for key, label in (
        ("volatility_n", "Volatilidad"),
        ("volume_n", "Volumen"),
        ("liquidity_n", "Liquidez"),
    ):
        if key in score_row:
            lines.append(f"{label}: {_float_or(score_row.get(key)):.2f} (normalizado 0–1)")
    return lines


def explain_composite_score(
    score_row: Mapping[str, Any],
    *,
    profile: str = "trend",
    family: str | None = None,
) -> dict[str, Any]:
    """Bloque serializable: qué es el score, banda, por qué, factores, qué hacer."""
    composite = _float_or(
        score_row.get("composite"),
        _float_or(score_row.get("base_score")),
    )
    fam = (family or profile or "trend").strip().lower()
    if fam in ("legacy_v1", "legacy", "balanced", ""):
        fam = "trend"
    label = FAMILY_LABELS_ES.get(fam, fam)
    band = score_band(composite)
    family_why = _FAMILY_SCORE_WHY.get(
        fam,
        f"El score mide qué tan bien encaja esta moneda con la rama «{label}» "
        "frente a las otras del universo escaneado.",
    )
    when = list(FAMILY_WHEN_TO_USE.get(fam, []))[:2]
    factors = _component_lines(score_row)
    und = str(
        score_row.get("underlying")
        or score_row.get("symbol")
        or score_row.get("instrument_id")
        or "—"
    )

    headline = (
        f"Score {composite:.3f} en «{label}» → {band['title']}. "
        + (
            "Rango bueno para probar estrategias de esta rama."
            if band["optimal_for_testing"]
            else "Todavía no es el rango preferido para priorizar esta moneda."
        )
    )

    what_is = (
        "El score va de 0 a 1 y compara esta moneda con las otras del mismo scan "
        "bajo la rama elegida. No es rentabilidad esperada ni probabilidad de ganar: "
        "es un ranking de ‘qué tan parecida es a lo que esa familia busca’."
    )

    ranges_help = (
        "Guía rápida de rangos: "
        "0.00–0.29 débil · 0.30–0.49 exploratorio · "
        "0.50–0.74 apto para probar · 0.75–0.89 buen ajuste · "
        "0.90–1.00 ajuste alto. "
        "Los óptimos para probar estrategias de la rama suelen empezar en 0.50 "
        "(mejor aún ≥ 0.75)."
    )

    next_steps = [
        "Si el score ≥ 0.50: abrí las estrategias sugeridas en el Simulador con esta moneda.",
        "Compará 1–2 TF (el del scan y una alternativa) y mirá fees + PnL neto.",
        "Si el score < 0.50: preferí otras monedas del ranking o cambiá de rama.",
        "Recordá: stub = la estrategia aún no corre completa en el lab.",
    ]

    plain_paragraphs = [
        headline,
        what_is,
        family_why,
        band["why"],
        ranges_help,
    ]
    if when:
        plain_paragraphs.append("Cuándo usar esta familia: " + when[0])

    return {
        "composite": round(composite, 6),
        "underlying": und,
        "family": fam,
        "family_label_es": label,
        "band": band,
        "headline": headline,
        "what_is": what_is,
        "family_why": family_why,
        "ranges_help": ranges_help,
        "when_to_use": when,
        "factors": factors,
        "next_steps": next_steps,
        "plain_paragraphs": plain_paragraphs,
        "note": "Score ≠ rentabilidad garantizada. LIVE sigue bloqueado.",
    }


__all__ = [
    "explain_composite_score",
    "score_band",
]
