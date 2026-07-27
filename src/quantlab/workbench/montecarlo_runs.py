"""Persistencia de corridas Monte Carlo por sesión — F34 + trazabilidad v2."""

from __future__ import annotations

import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.serialization import to_jsonable
from quantlab.data.atomic_io import atomic_write_text
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.montecarlo.traceability import (
    MONTECARLO_SCHEMA_VERSION_CURRENT,
    hash_mapping,
    normalize_montecarlo_payload,
)

MAX_MONTECARLO_LIST = 100
_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_SUMMARY_NAME = "summary.json"

# Re-export para callers legacy.
MONTECARLO_SCHEMA_VERSION = MONTECARLO_SCHEMA_VERSION_CURRENT


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
    """Persiste summary JSON bajo ``montecarlo/<run_id>/summary.json`` (schema v2)."""
    if not LIVE_BLOCKED:
        raise ValidationError("LIVE_BLOCKED debe ser True; abortando montecarlo persist")
    created_at = datetime.now(tz=UTC)
    rid = validate_run_id(run_id) if run_id else _make_run_id(created_at)
    out_dir = _safe_run_dir(montecarlo_root, rid)
    out_dir.mkdir(parents=True, exist_ok=True)

    body = dict(payload)
    body["schema_version"] = MONTECARLO_SCHEMA_VERSION_CURRENT
    body["run_id"] = rid
    body.setdefault("created_at", created_at.isoformat())
    body["persisted"] = True
    body["path"] = str((out_dir / _SUMMARY_NAME).resolve())
    body["live_routing"] = False
    body["live_blocked"] = True

    # Hashes de reproducibilidad
    cfg = body.get("config") if isinstance(body.get("config"), dict) else {}
    body["config_hash"] = hash_mapping(cfg) if cfg else body.get("config_hash")
    ctx = body.get("context") if isinstance(body.get("context"), dict) else {}
    if isinstance(ctx, dict) and ctx.get("run_id") is None:
        ctx = dict(ctx)
        ctx["run_id"] = rid
        body["context"] = ctx
    relations = body.get("relations") if isinstance(body.get("relations"), dict) else {}
    relations = dict(relations)
    relations.setdefault("config_hash", body.get("config_hash"))
    if isinstance(ctx, dict):
        relations.setdefault("backtest_id", ctx.get("backtest_id"))
        relations.setdefault("scan_id", ctx.get("scan_id"))
        relations.setdefault("dataset_id", ctx.get("dataset_id"))
        relations.setdefault("strategy_config_id", ctx.get("strategy_config_id"))
        relations.setdefault("strategy_params_hash", ctx.get("strategy_params_hash"))
        relations.setdefault("dataset_hash", ctx.get("dataset_hash"))
        relations.setdefault("code_commit", ctx.get("code_commit"))
    body["relations"] = relations

    jsonable = to_jsonable(body)
    if not isinstance(jsonable, dict):
        raise ValidationError("montecarlo payload serialización inválida")
    text = json.dumps(jsonable, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    atomic_write_text(out_dir / _SUMMARY_NAME, text)
    return normalize_montecarlo_payload(jsonable)


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
            norm = normalize_montecarlo_payload(raw)
            ctx = norm.get("context") if isinstance(norm.get("context"), dict) else {}
            runs.append(
                {
                    "run_id": norm.get("run_id", folder.name),
                    "created_at": norm.get("created_at"),
                    "n_scenarios": norm.get("n_scenarios"),
                    "n_bars": norm.get("n_bars"),
                    "seed": norm.get("seed"),
                    "mean_equity": norm.get("mean_equity"),
                    "std_equity": norm.get("std_equity"),
                    "ci_low": norm.get("ci_low"),
                    "ci_high": norm.get("ci_high"),
                    "method": norm.get("method"),
                    "strategy_id": ctx.get("strategy_id"),
                    "symbols": ctx.get("symbols"),
                    "timeframe": ctx.get("timeframe"),
                    "backtest_id": ctx.get("backtest_id"),
                    "scan_id": ctx.get("scan_id"),
                    "orphan_technical_mode": ctx.get("orphan_technical_mode"),
                    "schema_version": norm.get("schema_version"),
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
    return normalize_montecarlo_payload(raw)


def delete_montecarlo_run(montecarlo_root: Path, run_id: str) -> dict[str, Any]:
    """Elimina corrida completa del sandbox de sesión."""
    if not LIVE_BLOCKED:
        raise ValidationError("LIVE_BLOCKED debe ser True; abortando montecarlo delete")
    rid = validate_run_id(run_id)
    target = _safe_run_dir(montecarlo_root, rid)
    if not target.is_dir():
        raise ValidationError(f"montecarlo run no encontrado: {rid}")
    shutil.rmtree(target)
    return {
        "ok": True,
        "kind": "montecarlo_deleted",
        "run_id": rid,
        "live_routing": False,
        "live_blocked": True,
    }
