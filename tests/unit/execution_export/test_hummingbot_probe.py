"""Tests detección Hummingbot (sin runtime real)."""

from __future__ import annotations

from unittest.mock import patch

from quantlab.execution_export.hummingbot_probe import (
    hummingbot_status,
    verify_hummingbot_testnet_safety,
)


def test_hummingbot_not_installed_by_default() -> None:
    with patch(
        "quantlab.execution_export.hummingbot_probe._docker_hummingbot_running",
        return_value=False,
    ), patch(
        "quantlab.execution_export.hummingbot_probe._native_hummingbot_hint",
        return_value=False,
    ), patch(
        "quantlab.execution_export.hummingbot_probe._wsl_hummingbot_hint",
        return_value=False,
    ), patch(
        "quantlab.execution_export.hummingbot_probe._conf_paths",
        return_value=[],
    ):
        status = hummingbot_status()
    assert status["installed"] is False
    assert status["spot_testnet_connector_available"] is False
    assert status["quantlab_export_only"] is True


def test_hummingbot_docker_detected() -> None:
    with patch(
        "quantlab.execution_export.hummingbot_probe._docker_hummingbot_running",
        return_value=True,
    ), patch(
        "quantlab.execution_export.hummingbot_probe._conf_paths",
        return_value=[],
    ):
        status = hummingbot_status()
    assert status["installed"] is True
    assert status["detection_method"] == "docker"


def test_verify_safety_ok_when_no_conf() -> None:
    with patch(
        "quantlab.execution_export.hummingbot_probe.hummingbot_status",
        return_value={"installed": False, "conf_scan": []},
    ):
        result = verify_hummingbot_testnet_safety()
    assert result["ok"] is True
