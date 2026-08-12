"""Persistencia y reproducibilidad de scans (FASE 7)."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from quantlab.core.types.market import Bar
from quantlab.research.alpha.models import AlphaScanRequest, AlphaScanResult
from quantlab.research.alpha.scoring import ScoredRow


def _stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def sha256_hex(payload: str | bytes) -> str:
    data = payload.encode("utf-8") if isinstance(payload, str) else payload
    return hashlib.sha256(data).hexdigest()


def hash_request(request: AlphaScanRequest | Mapping[str, Any]) -> str:
    raw = request.to_dict() if isinstance(request, AlphaScanRequest) else dict(request)
    return sha256_hex(_stable_json(raw))


def hash_bars_fingerprint(bars_by_instrument: Mapping[str, Sequence[Bar]]) -> str:
    """Fingerprint determinista: instrument → close/volume/ts (no serializa Decimal crudo)."""
    rows: list[dict[str, Any]] = []
    for iid in sorted(bars_by_instrument):
        bars = bars_by_instrument[iid]
        rows.append(
            {
                "instrument_id": iid,
                "n": len(bars),
                "closes": [str(b.close) for b in bars],
                "volumes": [str(b.volume) for b in bars],
                "ts": [b.timestamp_close.isoformat() for b in bars],
            }
        )
    return sha256_hex(_stable_json(rows))


def hash_scored_rows(rows: Sequence[ScoredRow]) -> str:
    return sha256_hex(_stable_json([r.to_dict() for r in rows]))


@dataclass(frozen=True, slots=True)
class PersistedScanMeta:
    scan_id: str
    scanner_version: str
    profile: str
    profile_version: str
    formula_version: str
    request_hash: str
    bars_hash: str
    result_hash: str
    created_at: str
    path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "scan_id": self.scan_id,
            "scanner_version": self.scanner_version,
            "profile": self.profile,
            "profile_version": self.profile_version,
            "formula_version": self.formula_version,
            "request_hash": self.request_hash,
            "bars_hash": self.bars_hash,
            "result_hash": self.result_hash,
            "created_at": self.created_at,
            "path": self.path,
        }


@dataclass(frozen=True, slots=True)
class ScanDiff:
    same_request: bool
    same_bars: bool
    same_result: bool
    rank_changes: tuple[tuple[str, int | None, int | None], ...]
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "same_request": self.same_request,
            "same_bars": self.same_bars,
            "same_result": self.same_result,
            "rank_changes": [
                {"instrument_id": i, "rank_a": a, "rank_b": b} for i, a, b in self.rank_changes
            ],
            "detail": self.detail,
        }


class ScanStore:
    """Almacenamiento JSON local de resultados de scan (session/lab)."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, scan_id: str) -> Path:
        safe = "".join(c for c in scan_id if c.isalnum() or c in "_-")
        if not safe:
            raise ValueError(f"scan_id invalido: {scan_id!r}")
        return self.root / f"{safe}.json"

    def save_alpha_result(
        self,
        result: AlphaScanResult,
        *,
        bars_hash: str,
        request_hash: str | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> PersistedScanMeta:
        req_hash = request_hash or hash_request(result.request)
        payload = result.to_dict()
        result_hash = sha256_hex(_stable_json(payload.get("candidates", [])))
        created = datetime.now(tz=UTC).isoformat()
        meta = {
            "scan_id": result.scan_id,
            "scanner_version": result.scanner_version,
            "profile": result.profile,
            "profile_version": result.profile_version,
            "formula_version": result.formula_version,
            "request_hash": req_hash,
            "bars_hash": bars_hash,
            "result_hash": result_hash,
            "created_at": created,
        }
        doc = {"meta": meta, "result": payload, "extra": dict(extra or {})}
        path = self._path(result.scan_id)
        path.write_text(_stable_json(doc), encoding="utf-8")
        return PersistedScanMeta(
            scan_id=result.scan_id,
            scanner_version=result.scanner_version,
            profile=result.profile,
            profile_version=result.profile_version,
            formula_version=result.formula_version,
            request_hash=req_hash,
            bars_hash=bars_hash,
            result_hash=result_hash,
            created_at=created,
            path=str(path),
        )

    def save_scored(
        self,
        *,
        profile: str,
        rows: Sequence[ScoredRow | Mapping[str, Any]],
        bars_hash: str,
        request: Mapping[str, Any] | None = None,
        scan_id: str | None = None,
        scanner_version: str = "alpha-v2-contracts",
        profile_version: str = "profiles-v1",
        formula_version: str = "composite-scorer-v1",
    ) -> PersistedScanMeta:
        sid = scan_id or f"scan_{uuid4().hex[:12]}"
        req = dict(request or {"profile": profile})
        req_hash = sha256_hex(_stable_json(req))
        rows_payload = [
            r.to_dict() if isinstance(r, ScoredRow) else dict(r)
            for r in rows
        ]
        result_hash = sha256_hex(_stable_json(rows_payload))
        created = datetime.now(tz=UTC).isoformat()
        meta = {
            "scan_id": sid,
            "scanner_version": scanner_version,
            "profile": profile,
            "profile_version": profile_version,
            "formula_version": formula_version,
            "request_hash": req_hash,
            "bars_hash": bars_hash,
            "result_hash": result_hash,
            "created_at": created,
        }
        doc = {"meta": meta, "rows": rows_payload, "request": req}
        path = self._path(sid)
        path.write_text(_stable_json(doc), encoding="utf-8")
        return PersistedScanMeta(
            scan_id=sid,
            scanner_version=scanner_version,
            profile=profile,
            profile_version=profile_version,
            formula_version=formula_version,
            request_hash=req_hash,
            bars_hash=bars_hash,
            result_hash=result_hash,
            created_at=created,
            path=str(path),
        )

    def load(self, scan_id: str) -> dict[str, Any]:
        path = self._path(scan_id)
        if not path.is_file():
            raise FileNotFoundError(f"scan no encontrado: {scan_id}")
        raw: Any = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError(f"scan corrupto (no dict): {scan_id}")
        return dict(raw)

    def list_scans(self) -> tuple[PersistedScanMeta, ...]:
        out: list[PersistedScanMeta] = []
        for path in sorted(self.root.glob("*.json")):
            try:
                doc = json.loads(path.read_text(encoding="utf-8"))
                meta = doc.get("meta") or {}
                out.append(
                    PersistedScanMeta(
                        scan_id=str(meta.get("scan_id", path.stem)),
                        scanner_version=str(meta.get("scanner_version", "")),
                        profile=str(meta.get("profile", "")),
                        profile_version=str(meta.get("profile_version", "")),
                        formula_version=str(meta.get("formula_version", "")),
                        request_hash=str(meta.get("request_hash", "")),
                        bars_hash=str(meta.get("bars_hash", "")),
                        result_hash=str(meta.get("result_hash", "")),
                        created_at=str(meta.get("created_at", "")),
                        path=str(path),
                    )
                )
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                continue
        return tuple(out)


def compare_persisted(a: Mapping[str, Any], b: Mapping[str, Any]) -> ScanDiff:
    meta_a = dict(a.get("meta") or {})
    meta_b = dict(b.get("meta") or {})
    same_req = meta_a.get("request_hash") == meta_b.get("request_hash")
    same_bars = meta_a.get("bars_hash") == meta_b.get("bars_hash")
    same_res = meta_a.get("result_hash") == meta_b.get("result_hash")

    def _ranks(doc: Mapping[str, Any]) -> dict[str, int]:
        if "rows" in doc:
            rows = list(doc.get("rows") or [])
            return {
                str(r.get("instrument_id")): i + 1
                for i, r in enumerate(rows)
                if not r.get("excluded")
            }
        cands = list((doc.get("result") or {}).get("candidates") or [])
        return {
            str(c.get("normalized_instrument") or c.get("symbol")): int(c.get("rank", i + 1))
            for i, c in enumerate(cands)
        }

    ra, rb = _ranks(a), _ranks(b)
    keys = sorted(set(ra) | set(rb))
    changes = tuple((k, ra.get(k), rb.get(k)) for k in keys if ra.get(k) != rb.get(k))
    detail = "identical" if same_res and not changes else f"rank_changes={len(changes)}"
    return ScanDiff(
        same_request=bool(same_req),
        same_bars=bool(same_bars),
        same_result=bool(same_res),
        rank_changes=changes,
        detail=detail,
    )


__all__ = [
    "PersistedScanMeta",
    "ScanDiff",
    "ScanStore",
    "compare_persisted",
    "hash_bars_fingerprint",
    "hash_request",
    "hash_scored_rows",
    "sha256_hex",
]
