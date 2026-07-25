"""Tests del scanner de remotes (sin tocar git real)."""

from __future__ import annotations

from check_git_remote_clean import remote_has_embedded_secret


def test_detects_github_pat() -> None:
    # Fixture armada por partes (evita literales secret-scan del Review Package).
    prefix = "gh" + "p_"
    token = prefix + ("abcd" * 9)
    line = "origin https://" + token + "@github.com/x/y.git (fetch)"
    assert remote_has_embedded_secret(line)


def test_detects_userinfo_password() -> None:
    user = "user"
    secret = "secret" + "pass"
    # Concatenar para no dejar credencial literal en el source del Review Package.
    line = "origin " + "https://" + user + ":" + secret + "@github.com/x/y.git (fetch)"
    assert remote_has_embedded_secret(line)


def test_clean_https_ok() -> None:
    assert not remote_has_embedded_secret(
        "origin https://github.com/ssciarratta/QuantLab.git (fetch)"
    )
