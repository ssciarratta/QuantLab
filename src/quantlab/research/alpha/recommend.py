"""Recomendaciones Alpha Scanner → familia + estrategias + TF (solo score/ranking).

No ejecuta órdenes ni garantiza rentabilidad: traduce un score/perfil en
sugerencias para el Simulador (texto + chips).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from quantlab.workbench.strategy_guides import FAMILY_LABELS_ES, FAMILY_WHEN_TO_USE
from quantlab.research.alpha.score_guide import explain_composite_score

PROFILE_AUTO = "auto"
SCORING_PROFILE_AUTO = "balanced"

PROFILE_TO_FAMILY: dict[str, str | None] = {
    # Familias Simulador (selector Alpha Scanner)
    "trend": "trend",
    "momentum": "momentum",
    "mean_reversion": "mean_reversion",
    "market_making": "market_making",
    "stats": "stats",
    "ml": "ml",
    "multi_asset": "multi_asset",
    "microstructure": "microstructure",
    "arbitrage": "arbitrage",
    "options": "options",
    # Auto / vacío: no ancla familia → heurística por factores
    PROFILE_AUTO: None,
    "": None,
    "none": None,
    "all_families": None,
    # Perfiles técnicos legacy (compat)
    "legacy_v1": None,
    "legacy": None,
    "avellaneda_stoikov": "market_making",
    "funding": "stats",
    "balanced": None,
}

TF_CANDIDATES: tuple[str, ...] = ("15m", "1h", "4h", "1d")

_FAMILY_FALLBACK_ORDER: tuple[str, ...] = (
    "momentum",
    "trend",
    "mean_reversion",
    "market_making",
    "stats",
)


def _float_or(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def normalized_factors(score_row: Mapping[str, Any]) -> dict[str, float]:
    """Extrae factores normalizados desde fila legacy o profile-scored."""
    out: dict[str, float] = {
        "volatility": _float_or(score_row.get("volatility_n")),
        "volume": _float_or(score_row.get("volume_n")),
        "liquidity": _float_or(score_row.get("liquidity_n")),
        "momentum": 0.0,
        "trend_quality": 0.0,
        "spread": 0.0,
    }
    comps = score_row.get("components")
    if isinstance(comps, Sequence):
        for c in comps:
            if not isinstance(c, Mapping):
                continue
            name = str(c.get("name") or "").strip().lower()
            if not name:
                continue
            out[name] = _float_or(c.get("normalized"), out.get(name, 0.0))
    return out


def is_auto_profile(profile: str | None) -> bool:
    key = (profile or "").strip().lower()
    return key in ("", PROFILE_AUTO, "none", "all_families")


def resolve_scoring_profile(profile: str | None) -> tuple[str, str, bool]:
    """(requested, scoring_key, is_auto). Auto scorea con balanced e infiere familia."""
    raw = (profile or "").strip().lower()
    if is_auto_profile(raw):
        return PROFILE_AUTO, SCORING_PROFILE_AUTO, True
    return raw or "trend", raw or "trend", False


def infer_family(
    score_row: Mapping[str, Any],
    *,
    profile: str = "legacy_v1",
) -> str:
    """Familia sugerida: perfil ancla o heurística sobre factores."""
    key = (profile or "legacy_v1").strip().lower()
    if key in PROFILE_TO_FAMILY:
        mapped = PROFILE_TO_FAMILY[key]
        if mapped:
            return mapped
        # None = auto/legacy/balanced → heurística
    elif key not in ("",):
        # familia desconocida: si parece id de familia del catálogo, úsala
        if key in FAMILY_LABELS_ES:
            return key

    f = normalized_factors(score_row)
    mom = max(f.get("momentum", 0.0), f.get("trend_quality", 0.0))
    vol = f.get("volatility", 0.0)
    liq = max(f.get("volume", 0.0), f.get("liquidity", 0.0), f.get("volume_score", 0.0))

    if mom >= 0.65 and vol >= 0.35:
        return "momentum"
    if vol >= 0.70 and mom < 0.45:
        return "mean_reversion"
    if liq >= 0.65 and vol < 0.55:
        return "market_making"
    if mom >= 0.50:
        return "trend"
    if vol >= 0.45:
        return "mean_reversion"
    return "trend"


def strategies_for_family(
    family: str,
    *,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """2–3 estrategias del catálogo (runnable primero)."""
    from quantlab.workbench.strategy_catalog import STRATEGY_CATALOG

    fam = (family or "").strip().lower()
    metas = [m for m in STRATEGY_CATALOG if m.family == fam]
    if not metas:
        for alt in _FAMILY_FALLBACK_ORDER:
            metas = [m for m in STRATEGY_CATALOG if m.family == alt]
            if metas:
                fam = alt
                break
    metas = sorted(metas, key=lambda m: (not m.runnable, m.name.lower(), m.id))
    n = max(1, min(int(limit), 5))
    return [
        {
            "id": m.id,
            "name": m.name,
            "family": m.family,
            "runnable": m.runnable,
        }
        for m in metas[:n]
    ]


def recommend_timeframes(
    interval: str,
    score_row: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """TF actual + alternativas ordenadas por volatilidad relativa."""
    current = (interval or "1h").strip()
    f = normalized_factors(score_row)
    vol = f.get("volatility", 0.5)

    # Vol alta → TF más cortos; vol baja → más largos.
    if vol >= 0.65:
        preference = ("15m", "1h", "4h", "1d")
    elif vol <= 0.35:
        preference = ("1d", "4h", "1h", "15m")
    else:
        preference = ("1h", "4h", "15m", "1d")

    ordered: list[str] = []
    if current:
        ordered.append(current)
    for tf in preference:
        if tf not in ordered:
            ordered.append(tf)
    for tf in TF_CANDIDATES:
        if tf not in ordered:
            ordered.append(tf)

    out: list[dict[str, Any]] = []
    for i, tf in enumerate(ordered[:4]):
        out.append(
            {
                "interval": tf,
                "primary": i == 0,
                "reason": (
                    "intervalo del scan"
                    if tf == current
                    else (
                        "mejor para vol. alta"
                        if vol >= 0.65 and tf in ("15m", "1h")
                        else (
                            "mejor para vol. baja"
                            if vol <= 0.35 and tf in ("4h", "1d")
                            else "alternativa"
                        )
                    )
                ),
            }
        )
    return out


def recommend_for_score(
    score_row: Mapping[str, Any],
    *,
    profile: str = "legacy_v1",
    interval: str = "1h",
    strategy_limit: int = 3,
) -> dict[str, Any]:
    """Bloque recommendation serializable para una fila de score."""
    auto = is_auto_profile(profile)
    # En Auto forzar heurística (no anclar familia)
    fam_profile = PROFILE_AUTO if auto else profile
    family = infer_family(score_row, profile=fam_profile)
    strategies = strategies_for_family(family, limit=strategy_limit)
    tfs = recommend_timeframes(interval, score_row)
    composite = _float_or(
        score_row.get("composite"),
        _float_or(score_row.get("base_score")),
    )
    label = FAMILY_LABELS_ES.get(family, family)
    when = list(FAMILY_WHEN_TO_USE.get(family, []))[:2]
    strat_names = ", ".join(s["name"] for s in strategies) or "—"
    primary_tf = tfs[0]["interval"] if tfs else interval
    if auto:
        text = (
            f"Modo Auto · score {composite:.3f}. "
            f"Para este activo conviene probar la familia «{label}» "
            f"con: {strat_names}. "
            f"TF sugerido: {primary_tf}"
            + (
                f" · también {', '.join(t['interval'] for t in tfs[1:3])}."
                if len(tfs) > 1
                else "."
            )
        )
    else:
        text = (
            f"Score {composite:.3f} · familia sugerida: {label}. "
            f"Estrategias a probar: {strat_names}. "
            f"TF del scan: {interval}"
            + (
                f" · también: {', '.join(t['interval'] for t in tfs[1:3])}."
                if len(tfs) > 1
                else "."
            )
        )
    if when:
        text += " " + when[0]
    explained = explain_composite_score(
        score_row, profile=fam_profile if auto else profile, family=family
    )
    return {
        "family": family,
        "family_label_es": label,
        "when_to_use": when,
        "strategies": strategies,
        "timeframes": tfs,
        "text": text,
        "profile": PROFILE_AUTO if auto else (profile or "legacy_v1").strip().lower(),
        "auto_mode": auto,
        "score_explained": explained,
        "note": (
            "Un score alto indica adecuación al perfil, no rentabilidad garantizada."
            if not auto
            else "Auto: ranking equilibrado + familia/estrategias/TF inferidos. No garantiza rentabilidad."
        ),
    }


def build_auto_proposal(
    scores: Sequence[Mapping[str, Any]],
    *,
    interval: str = "1h",
    venue: str | None = None,
    top_n: int = 5,
) -> dict[str, Any]:
    """Propuesta agregada del conjunto: familia mayoritaria + estrategias/TF del top."""
    rows = [r for r in scores if isinstance(r, Mapping)][: max(1, top_n)]
    if not rows:
        return {
            "auto_mode": True,
            "family": "trend",
            "family_label_es": FAMILY_LABELS_ES.get("trend", "trend"),
            "strategies": strategies_for_family("trend", limit=3),
            "timeframes": recommend_timeframes(interval, {}),
            "votes": {},
            "text": "Sin scores para proponer.",
            "venue": venue,
        }

    votes: dict[str, int] = {}
    for row in rows:
        rec = row.get("recommendation") if isinstance(row.get("recommendation"), Mapping) else None
        if rec and rec.get("family"):
            fam = str(rec["family"])
        else:
            fam = infer_family(row, profile=PROFILE_AUTO)
        votes[fam] = votes.get(fam, 0) + 1

    winner = max(votes.items(), key=lambda kv: (kv[1], kv[0]))[0]
    # Preferir la recomendación completa del mejor score cuya familia = winner
    primary_rec: dict[str, Any] | None = None
    primary_row: Mapping[str, Any] = rows[0]
    for row in rows:
        rec = row.get("recommendation")
        if isinstance(rec, Mapping) and str(rec.get("family")) == winner:
            primary_rec = dict(rec)
            primary_row = row
            break
    if primary_rec is None:
        primary_rec = recommend_for_score(
            primary_row, profile=PROFILE_AUTO, interval=interval, strategy_limit=3
        )

    und = str(
        primary_row.get("underlying")
        or primary_row.get("symbol")
        or primary_row.get("instrument_id")
        or "—"
    )
    label = FAMILY_LABELS_ES.get(winner, winner)
    strat_names = ", ".join(s["name"] for s in (primary_rec.get("strategies") or [])) or "—"
    tfs = primary_rec.get("timeframes") or recommend_timeframes(interval, primary_row)
    primary_tf = tfs[0]["interval"] if tfs else interval
    vote_txt = ", ".join(f"{FAMILY_LABELS_ES.get(k, k)}×{v}" for k, v in sorted(votes.items(), key=lambda x: -x[1]))
    scope = f" en {venue}" if venue else ""
    text = (
        f"Propuesta Auto{scope}: para este conjunto conviene la familia «{label}» "
        f"(votos top: {vote_txt}). "
        f"Ejemplo con {und}: estrategias {strat_names}; TF {primary_tf}."
    )
    return {
        "auto_mode": True,
        "family": winner,
        "family_label_es": label,
        "when_to_use": list(FAMILY_WHEN_TO_USE.get(winner, []))[:2],
        "strategies": list(primary_rec.get("strategies") or []),
        "timeframes": list(tfs),
        "votes": votes,
        "top_underlying": und,
        "venue": venue,
        "text": text,
        "note": "Propuesta del conjunto (mayoría en el top). Score ≠ rentabilidad.",
    }


def underlying_from_symbol(symbol: str) -> str:
    """BTCUSDT / BTC-USDT-SWAP → BTC (HL HIP-3 se deja tal cual)."""
    raw = (symbol or "").strip()
    if not raw:
        return ""
    if ":" in raw:
        prefix, rest = raw.split(":", 1)
        # Venue prefixes lab; resto (xyz:GOLD) es HIP-3 case-sensitive.
        if prefix.upper() in {"BN", "BNF", "OKX", "BYB", "HL", "A3"}:
            raw = rest
        else:
            return raw
    text = raw.upper().replace("/", "")
    for suffix in ("-USDT-SWAP", "USDT", "-USDT", "SWAP"):
        if text.endswith(suffix):
            text = text[: -len(suffix)]
            break
    text = text.replace("-", "")
    return text or raw


def attach_recommendations(
    scan_out: dict[str, Any],
    *,
    profile: str | None = None,
    interval: str | None = None,
) -> dict[str, Any]:
    """Enriquece scores[] y añade recommendations del top-1."""
    requested, _scoring, auto = resolve_scoring_profile(
        profile if profile is not None else str(scan_out.get("profile") or "legacy_v1")
    )
    # Para inferencia/recomendar: en auto usar "auto"; si no, el requested
    prof = PROFILE_AUTO if auto else requested
    iv = (interval or scan_out.get("interval") or "1h").strip()
    scores = scan_out.get("scores")
    if not isinstance(scores, list):
        return scan_out

    selected_syms = scan_out.get("selected_symbols") or []
    enriched: list[dict[str, Any]] = []
    for i, row in enumerate(scores):
        if not isinstance(row, dict):
            continue
        item = dict(row)
        sym = str(
            item.get("symbol")
            or (
                selected_syms[i]
                if i < len(selected_syms) and isinstance(selected_syms[i], str)
                else ""
            )
            or item.get("instrument_id")
            or ""
        )
        und = str(item.get("underlying") or underlying_from_symbol(sym))
        if und:
            item["underlying"] = und
        if sym and "symbol" not in item:
            iid = str(item.get("instrument_id") or "")
            if ":" in iid:
                item["symbol"] = iid.split(":", 1)[1]
            elif sym:
                item["symbol"] = underlying_from_symbol(sym) and sym or sym
        item["recommendation"] = recommend_for_score(
            item, profile=prof, interval=iv, strategy_limit=3
        )
        enriched.append(item)

    scan_out["scores"] = enriched
    if enriched:
        top = enriched[0]
        scan_out["recommendations"] = {
            "top_instrument_id": top.get("instrument_id"),
            "top_underlying": top.get("underlying"),
            "top_symbol": top.get("symbol"),
            **dict(top.get("recommendation") or {}),
        }
    if auto:
        scan_out["auto_mode"] = True
        scan_out["profile"] = PROFILE_AUTO
        scan_out["scoring_profile"] = SCORING_PROFILE_AUTO
        top_n = int(scan_out.get("top_n") or 5)
        scan_out["proposal"] = build_auto_proposal(
            enriched,
            interval=iv,
            venue=str(scan_out.get("venue") or "") or None,
            top_n=top_n,
        )
    return scan_out


__all__ = [
    "PROFILE_AUTO",
    "PROFILE_TO_FAMILY",
    "SCORING_PROFILE_AUTO",
    "TF_CANDIDATES",
    "attach_recommendations",
    "build_auto_proposal",
    "infer_family",
    "is_auto_profile",
    "normalized_factors",
    "recommend_for_score",
    "recommend_timeframes",
    "resolve_scoring_profile",
    "strategies_for_family",
    "underlying_from_symbol",
]
