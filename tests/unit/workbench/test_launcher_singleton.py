"""Tests launcher_singleton — cierre de instancias previas."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from quantlab.workbench.launcher_singleton import (
    LauncherLockRecord,
    claim_launcher_singleton,
    clear_launcher_lock,
    read_launcher_lock,
    write_launcher_lock,
)


def test_launcher_lock_roundtrip(tmp_path: Path) -> None:
    lock = tmp_path / "launcher.pid"
    write_launcher_lock(lock, launcher_pid=9999, parent_pid=8888)
    rec = read_launcher_lock(lock)
    assert rec is not None
    assert rec.launcher_pid == 9999
    assert rec.parent_pid == 8888
    clear_launcher_lock(lock, only_if_pid=9999)
    assert read_launcher_lock(lock) is None


def test_claim_skips_current_parent(tmp_path: Path) -> None:
    lock = tmp_path / "launcher.pid"
    write_launcher_lock(lock, launcher_pid=111, parent_pid=222)
    killed: list[int] = []

    def fake_kill(pid: int, bucket: list[int]) -> None:
        bucket.append(pid)

    with (
        patch("quantlab.workbench.launcher_singleton.os.getpid", return_value=333),
        patch("quantlab.workbench.launcher_singleton._get_parent_pid", return_value=222),
        patch("quantlab.workbench.launcher_singleton.pid_is_alive", return_value=True),
        patch("quantlab.workbench.launcher_singleton.terminate_pid", return_value=True),
        patch("quantlab.workbench.launcher_singleton._kill_pid_if_alive", side_effect=fake_kill),
        patch("quantlab.workbench.launcher_singleton.port_in_use", return_value=False),
        patch("quantlab.workbench.launcher_singleton._find_pid_listening", return_value=None),
        patch("quantlab.workbench.launcher_singleton._sweep_quantlab_cmdline", return_value=[]),
        patch("quantlab.workbench.launcher_singleton.clear_lock"),
        patch("quantlab.workbench.launcher_singleton.read_lock_pid", return_value=None),
    ):
        claim_launcher_singleton(port=8765, lock_path=lock)

    assert 222 not in killed


def test_claim_kills_old_parent_cmd(tmp_path: Path) -> None:
    lock = tmp_path / "launcher.pid"
    write_launcher_lock(lock, launcher_pid=111, parent_pid=555)

    with (
        patch("quantlab.workbench.launcher_singleton.os.getpid", return_value=333),
        patch("quantlab.workbench.launcher_singleton._get_parent_pid", return_value=777),
        patch("quantlab.workbench.launcher_singleton.pid_is_alive", return_value=True),
        patch("quantlab.workbench.launcher_singleton.terminate_pid", return_value=True),
        patch("quantlab.workbench.launcher_singleton._kill_pid_if_alive") as mock_kill,
        patch("quantlab.workbench.launcher_singleton.port_in_use", return_value=False),
        patch("quantlab.workbench.launcher_singleton._find_pid_listening", return_value=None),
        patch("quantlab.workbench.launcher_singleton._sweep_quantlab_cmdline", return_value=[]),
        patch("quantlab.workbench.launcher_singleton.clear_lock"),
        patch("quantlab.workbench.launcher_singleton.read_lock_pid", return_value=None),
    ):
        claim_launcher_singleton(port=8765, lock_path=lock)

    killed_pids = [call.args[0] for call in mock_kill.call_args_list if call.args]
    assert 555 in killed_pids
