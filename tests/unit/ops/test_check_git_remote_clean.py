"""Tests del scanner de remotes (sin tocar git real)."""

from __future__ import annotations

from check_git_remote_clean import remote_has_embedded_secret


def test_detects_github_pat() -> None:
    assert remote_has_embedded_secret(
        "origin https://ghp_abcdefghijklmnopqrstuvwxyz0123456789@github.com/x/y.git (fetch)"
    )


def test_detects_userinfo_password() -> None:
    assert remote_has_embedded_secret(
        "origin https://user:secretpass@github.com/x/y.git (fetch)"
    )


def test_clean_https_ok() -> None:
    assert not remote_has_embedded_secret(
        "origin https://github.com/ssciarratta/QuantLab.git (fetch)"
    )
