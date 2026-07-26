"""Listado path-safe de exports Hummingbot en session/exports — F34."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED

MAX_EXPORTS_LIST = 100
_EXPORT_STEM_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,120}$")


def validate_export_stem(stem: str) -> str:
    """Valida nombre de archivo (sin extensión) como segmento seguro."""
    if not isinstance(stem, str):
        raise ValidationError(f"export id inválido (tipo): {type(stem).__name__}")
    name = stem.strip()
    if not name or name in {".", ".."} or not _EXPORT_STEM_RE.fullmatch(name):
        raise ValidationError(f"export id inválido: {stem!r}")
    if "/" in name or "\\" in name or ".." in name:
        raise ValidationError(f"export id con path traversal rechazado: {stem!r}")
    return name


def exports_dir_for(session_root: Path) -> Path:
    return Path(session_root) / "exports"


def _safe_export_path(exports_root: Path, filename: str) -> Path:
    stem = filename[:-5] if filename.endswith(".json") else filename
    safe = validate_export_stem(stem)
    root = exports_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    target = (root / f"{safe}.json").resolve()
    if not target.is_relative_to(root):
        raise ValidationError(f"export path fuera de sandbox: {filename!r}")
    return target


def list_hb_exports(exports_root: Path) -> dict[str, Any]:
    """Lista JSON de export HB en sandbox (más reciente primero). Empty-ok."""
    root = Path(exports_root)
    exports: list[dict[str, Any]] = []
    if root.is_dir():
        candidates = sorted(
            (p for p in root.iterdir() if p.is_file() and p.suffix == ".json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for path in candidates[:MAX_EXPORTS_LIST]:
            try:
                validate_export_stem(path.stem)
            except ValidationError:
                continue
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(raw, dict):
                continue
            # Solo packages HB (o legacy sin target pero con live_routing gate).
            target = raw.get("target")
            if target is not None and target != "hummingbot":
                continue
            exports.append(
                {
                    "export_id": raw.get("export_id", path.stem),
                    "filename": path.name,
                    "experiment_id": raw.get("experiment_id"),
                    "strategy_version": raw.get("strategy_version"),
                    "created_at": raw.get("created_at"),
                    "live_routing": raw.get("live_routing", False) is True,
                    "blocked": raw.get("blocked", True) is not False,
                    "path": str(path.resolve()),
                    "is_latest_alias": not str(raw.get("export_id", "")).startswith("hb-")
                    and path.stem == str(raw.get("experiment_id", "")),
                }
            )
    return {
        "ok": True,
        "kind": "exports",
        "count": len(exports),
        "exports": exports,
        "live_routing": False,
        "live_blocked": LIVE_BLOCKED is True,
        "read_only": True,
        "banner": "live_routing:false — export research-safe; sin order routing LIVE",
    }


def get_hb_export(exports_root: Path, export_id: str) -> dict[str, Any]:
    """Lee un export por stem / export_id (fail-closed sandbox)."""
    path = _safe_export_path(
        exports_root, export_id if export_id.endswith(".json") else f"{export_id}.json"
    )
    if not path.is_file():
        raise ValidationError(f"export no encontrado: {export_id}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValidationError("export JSON inválido")
    return {
        "ok": True,
        "kind": "export_hb",
        "export_id": raw.get("export_id", path.stem),
        "path": str(path.resolve()),
        "payload": raw,
        "live_routing": False,
        "live_blocked": LIVE_BLOCKED is True,
    }
