"""CLI de certificación A3 F89; no usa red."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import a3_md_certify


def _clear_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("QUANTLAB_RUN_A3_SANDBOX_CERT", raising=False)
    monkeypatch.delenv("QUANTLAB_A3_MD_READONLY", raising=False)


def test_fake_lane_writes_pass_report(tmp_path: Path) -> None:
    output = tmp_path / "fake.json"

    exit_code = a3_md_certify.main(["--lane", "fake", "--output", str(output)])
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert payload["phase"] == 89
    assert payload["quantlab_version"] == "0.93.0"
    assert payload["live_blocked"] is True
    assert payload["lanes"][0]["status"] == "PASS"
    assert payload["lanes"][0]["write_calls"] == 0


def test_sandbox_skip_is_exit_two(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_opt_in(monkeypatch)
    output = tmp_path / "sandbox.json"

    exit_code = a3_md_certify.main(["--lane", "sandbox", "--output", str(output)])
    lane = json.loads(output.read_text(encoding="utf-8"))["lanes"][0]

    assert exit_code == 2
    assert lane["status"] == "SKIPPED_NOT_REQUESTED"
    assert lane["status"] != "PASS"


def test_all_allows_explicit_sandbox_skip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _clear_opt_in(monkeypatch)
    output = tmp_path / "all.json"

    exit_code = a3_md_certify.main(["--lane", "all", "--output", str(output)])
    lanes = {
        lane["lane"]: lane["status"]
        for lane in json.loads(output.read_text(encoding="utf-8"))["lanes"]
    }

    assert exit_code == 0
    assert lanes == {"fake": "PASS", "sandbox": "SKIPPED_NOT_REQUESTED"}


def test_timeout_is_sandbox_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def timeout(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise subprocess.TimeoutExpired(cmd="worker", timeout=0.1)

    monkeypatch.setattr("a3_md_certify.subprocess.run", timeout)
    report = a3_md_certify._run_sandbox_subprocess(0.1)

    assert report["status"] == "FAIL"
    assert report["issues"] == ["sandbox_timeout"]


def test_worker_environment_drops_unrelated_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UNRELATED_SECRET", "must-not-cross")
    monkeypatch.setenv("QUANTLAB_A3_USER", "required-worker-value")

    env = a3_md_certify._sanitized_worker_env()

    assert "UNRELATED_SECRET" not in env
    assert env["QUANTLAB_A3_USER"] == "required-worker-value"
