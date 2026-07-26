"""Persistencia de reports lab (MetricsResult / HTML) por sesión — F29."""

from __future__ import annotations

import json
import re
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.results import MetricsResult, SimulationResult
from quantlab.core.types.serialization import to_jsonable
from quantlab.data.atomic_io import atomic_write_text
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.reporting import ReportGenerator

REPORT_SCHEMA_VERSION = 1
MAX_REPORTS_LIST = 200
_REPORT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_SUMMARY_NAME = "summary.json"
_HTML_NAME = "report_default_v1.html"


def validate_report_id(report_id: str) -> str:
    """Valida ``report_id`` seguro como segmento de path (fail-closed)."""
    if not isinstance(report_id, str):
        raise ValidationError(f"report_id inválido (tipo): {type(report_id).__name__}")
    rid = report_id.strip()
    if not rid or rid in {".", ".."} or not _REPORT_ID_RE.fullmatch(rid):
        raise ValidationError(
            f"report_id inválido (charset ^[A-Za-z0-9][A-Za-z0-9_-]{{0,63}}$): {report_id!r}"
        )
    if "/" in rid or "\\" in rid or ".." in rid:
        raise ValidationError(f"report_id con path traversal rechazado: {report_id!r}")
    return rid


def reports_dir_for(session_root: Path) -> Path:
    return Path(session_root) / "reports"


def _safe_report_dir(reports_root: Path, report_id: str) -> Path:
    rid = validate_report_id(report_id)
    root = reports_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    target = (root / rid).resolve()
    if not target.is_relative_to(root):
        raise ValidationError(f"report path fuera de sandbox: {report_id!r}")
    return target


def _make_report_id(experiment_id: str, created_at: datetime) -> str:
    stamp = created_at.strftime("%Y%m%dT%H%M%S%f")[:-3] + "Z"
    base = f"{experiment_id}-{stamp}"
    # experiment_id ya es charset seguro; stamp también — truncar a 64.
    if len(base) > 64:
        # Preferir stamp al final.
        keep = 64 - 1 - len(stamp)
        base = stamp[:64] if keep < 1 else f"{experiment_id[:keep]}-{stamp}"
    return validate_report_id(base)


def persist_backtest_report(
    reports_root: Path,
    *,
    metrics: MetricsResult,
    simulation: SimulationResult | None,
    summary: dict[str, Any],
    report_id: str | None = None,
) -> dict[str, Any]:
    """Persiste summary JSON + HTML (ReportGenerator) bajo ``reports/<id>/``.

    El ``report_id`` es único por corrida (experiment_id + timestamp UTC).
    HTML usa un MetricsResult con ``experiment_id=report_id`` solo para path
    del generador; el experiment_id original queda en summary/metrics_result.
    """
    created_at = datetime.now(tz=UTC)
    rid = (
        validate_report_id(report_id)
        if report_id
        else _make_report_id(metrics.experiment_id, created_at)
    )
    out_dir = _safe_report_dir(reports_root, rid)
    out_dir.mkdir(parents=True, exist_ok=True)

    metrics_dict = to_jsonable(metrics.to_dict())
    if not isinstance(metrics_dict, dict):
        raise ValidationError("metrics_result serialización inválida")

    html_relpath: str | None = None
    html_bytes = 0
    try:
        # Carpeta = report_id vía experiment_id temporal del generador.
        metrics_for_html = replace(metrics, experiment_id=rid)
        gen = ReportGenerator(reports_root.resolve())
        result = gen.generate(metrics=metrics_for_html, simulation=simulation)
        html_path = Path(result.path)
        # Esperado: reports_root / rid / report_default_v1.html
        if html_path.is_file() and html_path.parent.resolve() == out_dir.resolve():
            html_relpath = html_path.name
            html_bytes = result.bytes_written
        elif (out_dir / _HTML_NAME).is_file():
            html_relpath = _HTML_NAME
            html_bytes = (out_dir / _HTML_NAME).stat().st_size
    except (OSError, ValidationError, TypeError, ValueError):
        # JSON mínimo siempre; HTML es best-effort.
        html_relpath = None

    payload: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "report_id": rid,
        "created_at": created_at.isoformat(),
        "kind": "backtest",
        "experiment_id": metrics.experiment_id,
        "metrics_version": metrics.metrics_version,
        "metrics_result": metrics_dict,
        "summary": dict(summary),
        "html_relpath": html_relpath,
        "html_bytes": html_bytes,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
    }
    converted = to_jsonable(payload)
    if not isinstance(converted, dict):
        raise ValidationError("report summary serialización inválida")
    text = json.dumps(converted, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    atomic_write_text(out_dir / _SUMMARY_NAME, text)
    return {
        "ok": True,
        "report_id": rid,
        "path": str(out_dir / _SUMMARY_NAME),
        "dir": str(out_dir),
        "has_html": html_relpath is not None,
        "html_relpath": html_relpath,
        "created_at": created_at.isoformat(),
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
    }


def list_lab_reports(reports_root: Path, *, limit: int = 50) -> dict[str, Any]:
    """Lista reports persistidos (más recientes primero)."""
    if limit < 1 or limit > MAX_REPORTS_LIST:
        raise ValidationError(f"limit debe estar entre 1 y {MAX_REPORTS_LIST}")
    root = Path(reports_root)
    if not root.exists():
        return {
            "ok": True,
            "kind": "reports",
            "count": 0,
            "reports": [],
            "path": str(root),
            "live_blocked": LIVE_BLOCKED is True,
            "live_routing": False,
        }
    root = root.resolve()
    entries: list[dict[str, Any]] = []
    for child in root.iterdir():
        if not child.is_dir():
            continue
        try:
            rid = validate_report_id(child.name)
        except ValidationError:
            continue
        summary_path = child / _SUMMARY_NAME
        if not summary_path.is_file():
            continue
        try:
            raw = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(raw, dict):
            continue
        summary = raw.get("summary") if isinstance(raw.get("summary"), dict) else {}
        entries.append(
            {
                "report_id": rid,
                "created_at": raw.get("created_at"),
                "experiment_id": raw.get("experiment_id"),
                "kind": raw.get("kind", "backtest"),
                "strategy_id": summary.get("strategy_id") if isinstance(summary, dict) else None,
                "metrics_version": raw.get("metrics_version"),
                "has_html": bool(raw.get("html_relpath")) and (child / _HTML_NAME).is_file(),
                "final_equity": summary.get("final_equity") if isinstance(summary, dict) else None,
            }
        )

    def _sort_key(item: dict[str, Any]) -> str:
        ts = item.get("created_at")
        return str(ts) if isinstance(ts, str) else ""

    entries.sort(key=_sort_key, reverse=True)
    truncated = entries[:limit]
    return {
        "ok": True,
        "kind": "reports",
        "count": len(truncated),
        "reports": truncated,
        "path": str(root),
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
    }


def get_lab_report(
    reports_root: Path,
    report_id: str,
    *,
    include_html: bool = True,
) -> dict[str, Any]:
    """Carga un report por id (summary + HTML opcional)."""
    out_dir = _safe_report_dir(reports_root, report_id)
    summary_path = out_dir / _SUMMARY_NAME
    if not summary_path.is_file():
        raise ValidationError(f"report no encontrado: {report_id}")
    try:
        raw = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"summary.json ilegible: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValidationError("summary.json debe ser un objeto")

    html: str | None = None
    html_relpath = raw.get("html_relpath")
    if include_html and isinstance(html_relpath, str) and html_relpath:
        # Solo nombre de archivo bajo out_dir (sin subpaths).
        if "/" in html_relpath or "\\" in html_relpath or html_relpath in {".", ".."}:
            raise ValidationError("html_relpath inválido")
        html_path = (out_dir / html_relpath).resolve()
        if not html_path.is_relative_to(out_dir.resolve()):
            raise ValidationError("html path fuera de sandbox")
        if html_path.is_file():
            try:
                html = html_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                raise ValidationError(f"HTML ilegible: {exc}") from exc

    return {
        "ok": True,
        "kind": "report",
        "report_id": validate_report_id(report_id),
        "path": str(summary_path),
        "report": raw,
        "html": html,
        "has_html": html is not None,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
    }
