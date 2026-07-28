"""Jobs async Monte Carlo (progreso + cancelación) para N grandes."""

from __future__ import annotations

import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from quantlab.montecarlo.cancel import CancellationToken

JobRunner = Callable[..., dict[str, Any]]


@dataclass
class MonteCarloJob:
    job_id: str
    status: str = "queued"  # queued|running|cancelling|cancelled|completed|failed
    created_at: str = field(default_factory=lambda: datetime.now(tz=UTC).isoformat())
    progress: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] | None = None
    error: str | None = None
    token: CancellationToken = field(default_factory=CancellationToken)
    _thread: threading.Thread | None = field(default=None, repr=False)


class MonteCarloJobStore:
    """Store en memoria por proceso workbench (sesión)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, MonteCarloJob] = {}

    def start(
        self,
        *,
        runner: JobRunner,
        kwargs: dict[str, Any],
    ) -> MonteCarloJob:
        job_id = f"mcjob-{uuid.uuid4().hex[:12]}"
        job = MonteCarloJob(job_id=job_id)

        def _run() -> None:
            job.status = "running"
            try:

                def on_progress(p: dict[str, Any]) -> None:
                    job.progress = dict(p)
                    if job.token.is_cancelled:
                        job.status = "cancelling"

                run_kwargs = dict(kwargs)
                run_kwargs["cancellation"] = job.token
                run_kwargs["on_progress"] = on_progress
                result = runner(**run_kwargs)
                job.result = result
                if job.token.is_cancelled or result.get("partial"):
                    job.status = "cancelled"
                else:
                    job.status = "completed"
            except Exception as exc:  # noqa: BLE001
                if job.token.is_cancelled:
                    job.status = "cancelled"
                    job.error = str(exc)
                else:
                    job.status = "failed"
                    job.error = str(exc)

        t = threading.Thread(target=_run, name=job_id, daemon=True)
        job._thread = t
        with self._lock:
            self._jobs[job_id] = job
        t.start()
        return job

    def get(self, job_id: str) -> MonteCarloJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def cancel(self, job_id: str) -> MonteCarloJob | None:
        job = self.get(job_id)
        if job is None:
            return None
        job.status = "cancelling"
        job.token.cancel()
        return job

    def to_public(self, job: MonteCarloJob) -> dict[str, Any]:
        return {
            "ok": True,
            "kind": "montecarlo_job",
            "job_id": job.job_id,
            "status": job.status,
            "created_at": job.created_at,
            "progress": job.progress,
            "error": job.error,
            "result": job.result if job.status in ("completed", "cancelled") else None,
            "live_routing": False,
        }


_STORE: MonteCarloJobStore | None = None
_STORE_LOCK = threading.Lock()


def get_job_store() -> MonteCarloJobStore:
    global _STORE
    with _STORE_LOCK:
        if _STORE is None:
            _STORE = MonteCarloJobStore()
        return _STORE


def reset_job_store() -> None:
    """Solo tests."""
    global _STORE
    with _STORE_LOCK:
        _STORE = MonteCarloJobStore()
