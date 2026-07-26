"""Persistencia de corridas Monte Carlo por sesión — F34."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.serialization import to_jsonable
from quantlab.data.atomic_io import atomic_write_text
from quantlab.execution.live_gate import LIVE_BLOCKED

MONTECARLO_SCHEMA_VERSION = 1
MAX_MONTECARLO_LIST = 100
_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_SUMMARY_NAME = "summary.json"


def validate_run_id(run_id: str) -> str:
    """Valida ``run_id`` seguro como segmento de path (fail-closed)."""
    if not isinstance(run_id, str):
        raise ValidationError(f"run_id inválido (tipo): {type(run_id).__name__}")
    rid = run_id.strip()
    if not rid or rid in {".", ".."} or not _RUN_ID_RE.fullmatch(rid):
        raise ValidationError(
            f"run_id inválido (charset ^[A-Za-z0-9][A-Za-z0-9_-]{{0,63}}$): {run_id!r}"
        )
    if "/" in rid or "\\" in rid or ".." in rid:
        raise ValidationError(f"run_id con path traversal rechazado: {run_id!r}")
    return rid


def montecarlo_dir_for(session_root: Path) -> Path:
    return Path(session_root) / "montecarlo"


def _safe_run_dir(montecarlo_root: Path, run_id: str) -> Path:
    rid = validate_run_id(run_id)
    root = montecarlo_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    target = (root / rid).resolve()
    if not target.is_relative_to(root):
        raise ValidationError(f"montecarlo path fuera de sandbox: {run_id!r}")
    return target


def _make_run_id(created_at: datetime) -> str:
    stamp = created_at.strftime("%Y%m%dT%H%M%S%f")[:-3] + "Z"
    base = f"mc-{stamp}"
    if len(base) > 64:
        base = stamp[:64]
    return validate_run_id(base)


def persist_montecarlo_run(
    montecarlo_root: Path,
    payload: dict[str, Any],
    *,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Persiste summary JSON bajo ``montecarlo/<run_id>/summary.json``."""
    if not LIVE_BLOCKED:
        raise ValidationError("LIVE_BLOCKED debe ser True; abortando montecarlo persist")
    created_at = datetime.now(tz=UTC)
    rid = validate_run_id(run_id) if run_id else _make_run_id(created_at)
    out_dir = _safe_run_dir(montecarlo_root, rid)
    out_dir.mkdir(parents=True, exist_ok=True)

    body = dict(payload)
    body["schema_version"] = MONTECARLO_SCHEMA_VERSION
    body["run_id"] = rid
    body.setdefault("created_at", created_at.isoformat())
    body["persisted"] = True
    body["path"] = str((out_dir / _SUMMARY_NAME).resolve())
    body["live_routing"] = False
    body["live_blocked"] = True

    jsonable = to_jsonable(body)
    if not isinstance(jsonable, dict):
        raise ValidationError("montecarlo payload serialización inválida")
    text = json.dumps(jsonable, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    atomic_write_text(out_dir / _SUMMARY_NAME, text)
    return jsonable


def list_montecarlo_runs(montecarlo_root: Path) -> dict[str, Any]:
    """Lista corridas persistidas (más reciente primero). Empty-ok."""
    root = Path(montecarlo_root)
    runs: list[dict[str, Any]] = []
    if root.is_dir():
        candidates = sorted(
            (p for p in root.iterdir() if p.is_dir() and (p / _SUMMARY_NAME).is_file()),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for folder in candidates[:MAX_MONTECARLO_LIST]:
            try:
                raw = json.loads((folder / _SUMMARY_NAME).read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(raw, dict):
                continue
            runs.append(
                {
                    "run_id": raw.get("run_id", folder.name),
                    "created_at": raw.get("created_at"),
                    "n_scenarios": raw.get("n_scenarios"),
                    "n_bars": raw.get("n_bars"),
                    "seed": raw.get("seed"),
                    "mean_equity": raw.get("mean_equity"),
                    "std_equity": raw.get("std_equity"),
                    "ci_low": raw.get("ci_low"),
                    "ci_high": raw.get("ci_high"),
                    "path": str((folder / _SUMMARY_NAME).resolve()),
                }
            )
    latest = None
    if runs:
        try:
            latest = get_montecarlo_run(montecarlo_root, str(runs[0]["run_id"]))
        except ValidationError:
            latest = None
    return {
        "ok": True,
        "kind": "montecarlo_history",
        "count": len(runs),
        "runs": runs,
        "latest": latest,
        "live_routing": False,
        "live_blocked": LIVE_BLOCKED is True,
        "read_only": True,
    }


def get_montecarlo_run(montecarlo_root: Path, run_id: str) -> dict[str, Any]:
    rid = validate_run_id(run_id)
    summary = _safe_run_dir(montecarlo_root, rid) / _SUMMARY_NAME
    if not summary.is_file():
        raise ValidationError(f"montecarlo run no encontrado: {rid}")
    raw = json.loads(summary.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValidationError("summary.json inválido")
    return raw
