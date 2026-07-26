#!/usr/bin/env python3
"""Check o rebuild offline de una sesión paper; nunca modifica el journal."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from quantlab.brokers.paper.book import DEFAULT_INITIAL_CASH
from quantlab.brokers.paper.journal import PaperFillJournal
from quantlab.brokers.paper.reconciliation import ReconciliationReport, rebuild_book, reconcile_book
from quantlab.core.exceptions import ValidationError
from quantlab.workbench.session import WorkbenchSession


def _session(root: Path) -> WorkbenchSession:
    resolved = root.expanduser().resolve()
    if not resolved.is_dir():
        raise ValidationError(f"session no existe o no es directorio: {resolved}")
    return WorkbenchSession(resolved, resolved.name)


def _config_from_session(session: WorkbenchSession) -> tuple[Decimal, str, bool]:
    try:
        loaded = session.load_book_state()
    except ValidationError:
        meta = session.load_meta()
        return Decimal(str(meta.get("initial_cash", DEFAULT_INITIAL_CASH))), "USD", False
    book = loaded.book
    return book.initial_cash, book.currency, book.allow_short


def check_session(root: Path) -> ReconciliationReport:
    session = _session(root)
    loaded = session.load_book_state()
    journal = PaperFillJournal(session.journal_path)
    report = reconcile_book(loaded.book, journal)
    if (
        report.ok
        and loaded.schema_version == 2
        and loaded.checkpoint != report.checkpoint
    ):
        issue = "checkpoint_mismatch"
        if loaded.checkpoint is not None and report.checkpoint is not None:
            if (
                loaded.checkpoint.record_count < report.checkpoint.record_count
                and journal.contains_checkpoint(loaded.checkpoint)
            ):
                issue = "journal_ahead"
            elif loaded.checkpoint.record_count > report.checkpoint.record_count:
                issue = "book_ahead"
        return ReconciliationReport(
            ok=False,
            status="rebuild_required",
            record_count=report.record_count,
            issues=(issue,),
            expected_book=report.expected_book,
            persisted_book=report.persisted_book,
            checkpoint=report.checkpoint,
        )
    return report


def rebuild_session(root: Path) -> tuple[ReconciliationReport, Path | None]:
    session = _session(root)
    journal = PaperFillJournal(session.journal_path)
    fills = journal.read_strict()
    checkpoint = journal.checkpoint()
    initial_cash, currency, allow_short = _config_from_session(session)
    rebuilt = rebuild_book(initial_cash, currency, allow_short, fills)

    backup: Path | None = None
    if session.book_path.exists():
        stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S%fZ")
        backup = session.book_path.with_name(f"{session.book_path.name}.bak-{stamp}")
        shutil.copy2(session.book_path, backup)
        # "rb+" (no "rb"): en Windows fsync exige handle con acceso de escritura.
        with backup.open("rb+") as handle:
            os.fsync(handle.fileno())

    session.save_book(rebuilt, checkpoint)
    report = reconcile_book(rebuilt, journal)
    if not report.ok:
        raise ValidationError(f"rebuild no reconcilió: {'; '.join(report.issues)}")
    return report, backup


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, type=Path, help="directorio raíz de sesión")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true", help="sólo verificar; no muta archivos")
    action.add_argument(
        "--rebuild",
        action="store_true",
        help="backup + reconstrucción de book.json",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.rebuild:
            report, backup = rebuild_session(args.session)
            payload: dict[str, Any] = report.to_dict()
            payload["backup"] = str(backup) if backup is not None else None
            payload["rebuilt"] = True
        else:
            report = check_session(args.session)
            payload = report.to_dict()
            payload["rebuilt"] = False
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if report.ok else 2
    except (OSError, UnicodeError, ValidationError) as exc:
        print(json.dumps({"ok": False, "status": "error", "issues": [str(exc)]}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
