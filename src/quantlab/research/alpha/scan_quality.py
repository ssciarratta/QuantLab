"""Diagnóstico de calidad del ranking Alpha Scanner (degradado / empatados en 0)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

_EPS = 1e-12


def _f(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def composites_of(scores: Sequence[Mapping[str, Any]]) -> list[float]:
    out: list[float] = []
    for row in scores:
        if not isinstance(row, Mapping):
            continue
        c = _f(row.get("composite"))
        if c is None:
            c = _f(row.get("base_score"))
        if c is not None:
            out.append(c)
    return out


def zero_variance_factor_names(scores: Sequence[Mapping[str, Any]]) -> list[str]:
    """Factores con raw idéntico (o todos normalizados a 0) en el cross-section."""
    by_name: dict[str, list[float]] = {}
    for row in scores:
        if not isinstance(row, Mapping):
            continue
        comps = row.get("components")
        if not isinstance(comps, Sequence):
            continue
        for c in comps:
            if not isinstance(c, Mapping):
                continue
            name = str(c.get("name") or "").strip().lower()
            if not name:
                continue
            raw = _f(c.get("raw"))
            if raw is None:
                continue
            by_name.setdefault(name, []).append(raw)
    tied: list[str] = []
    for name, vals in sorted(by_name.items()):
        if len(vals) < 2:
            continue
        if max(vals) - min(vals) <= _EPS:
            tied.append(name)
    return tied


def assess_scan_quality(
    scan_out: Mapping[str, Any],
    *,
    fetch_failures: Mapping[str, str] | None = None,
    md_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Devuelve score_status, score_reason, warnings y anota filas si aplica."""
    scores = list(scan_out.get("scores") or [])
    warnings: list[str] = []
    status = "ok"
    reason = ""

    comps = composites_of(scores)
    tied_factors = zero_variance_factor_names(scores)
    all_zero = len(comps) >= 2 and all(abs(c) <= _EPS for c in comps)

    failures = dict(fetch_failures or scan_out.get("fetch_failures") or {})
    if failures:
        sample = "; ".join(f"{k}: {v}" for k, v in list(failures.items())[:3])
        more = f" (+{len(failures) - 3})" if len(failures) > 3 else ""
        warnings.append(
            f"{len(failures)} símbolo(s) sin datos MD (no entran al ranking): {sample}{more}"
        )
        if status == "ok":
            status = "partial"
            reason = "fetch_failures"

    md = dict(md_meta or scan_out.get("md_meta") or {})
    provider = str(md.get("provider") or "")
    if provider == "a3-fake":
        warnings.append(
            "A3 usa MD demo (fake): series cortas ~120h, no cubren un mes real. "
            "Para MD Matba Rofex: QUANTLAB_A3_MD_READONLY=1 + credenciales."
        )
        if status == "ok":
            status = "degraded"
            reason = "a3_fake_md"

    n_est = scan_out.get("n_bars_estimate")
    kline = scan_out.get("kline_limit")
    if (
        provider == "a3-fake"
        and isinstance(n_est, (int, float))
        and isinstance(kline, (int, float))
        and float(n_est) > 200
    ):
        warnings.append(
            f"Pediste ≈{int(n_est)} velas; el fake A3 no tiene esa historia "
            f"(el ranking usa lo disponible, truncado a {int(kline)})."
        )

    profile = str(scan_out.get("profile") or "").strip().lower()
    if profile in ("market_making", "microstructure") and not scan_out.get("has_order_book"):
        warnings.append(
            f"Perfil «{profile}» idealmente usa libro (bid/ask); "
            "sin book se usa proxy OHLC y puede empatar todo en 0."
        )

    if all_zero:
        status = "degraded"
        reason = "zero_cross_section_variance"
        fac_txt = ", ".join(tied_factors) if tied_factors else "factores del perfil"
        msg = (
            "Todos los scores = 0.000: sin discriminación entre monedas "
            f"(varianza cero en {fac_txt}). "
            "No interpretes 0 pts como «peor» — el ranking está empatado / degradado."
        )
        warnings.append(msg)
        for row in scores:
            if not isinstance(row, dict):
                continue
            row["score_status"] = "tied_zero"
            row["score_reason"] = (
                "zero_variance:" + (",".join(tied_factors) if tied_factors else "all")
            )
    elif tied_factors and len(comps) >= 2:
        warnings.append(
            "Factores sin variación entre monedas: "
            + ", ".join(tied_factors)
            + ". El score puede ser poco informativo."
        )
        if status == "ok":
            status = "degraded"
            reason = "partial_zero_variance"

    excl = scan_out.get("exclusion_counts")
    if isinstance(excl, Mapping) and excl:
        parts = [f"{k}={v}" for k, v in excl.items() if v]
        if parts:
            warnings.append("Exclusiones de calidad: " + ", ".join(parts))

    # dedupe preservando orden
    seen: set[str] = set()
    uniq: list[str] = []
    for w in warnings:
        if w not in seen:
            seen.add(w)
            uniq.append(w)

    return {
        "score_status": status,
        "score_reason": reason,
        "warnings": uniq,
        "tied_factors": tied_factors,
        "md_meta": md or None,
        "fetch_failures": failures or None,
    }


def attach_scan_quality(
    scan_out: dict[str, Any],
    *,
    fetch_failures: Mapping[str, str] | None = None,
    md_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Enriquece el payload del scanner con score_status / warnings."""
    assessed = assess_scan_quality(
        scan_out, fetch_failures=fetch_failures, md_meta=md_meta
    )
    scan_out["score_status"] = assessed["score_status"]
    scan_out["score_reason"] = assessed["score_reason"]
    scan_out["warnings"] = assessed["warnings"]
    if assessed.get("tied_factors"):
        scan_out["tied_factors"] = assessed["tied_factors"]
    if assessed.get("md_meta"):
        scan_out["md_meta"] = assessed["md_meta"]
    if assessed.get("fetch_failures"):
        scan_out["fetch_failures"] = assessed["fetch_failures"]
    if assessed["score_status"] != "ok" and assessed["warnings"]:
        note = str(scan_out.get("note") or "")
        extra = assessed["warnings"][0]
        if extra not in note:
            scan_out["note"] = (note + " · " + extra).strip(" ·")
    return scan_out


__all__ = [
    "assess_scan_quality",
    "attach_scan_quality",
    "composites_of",
    "zero_variance_factor_names",
]
