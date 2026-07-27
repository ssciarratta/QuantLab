"""Tests presets LLM (Gemini / NVIDIA) — sin red."""

from __future__ import annotations

import pytest

from quantlab.workbench.chat.llm_http import resolve_llm_endpoint


def test_resolve_gemini_preset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QUANTLAB_LLM_PROVIDER", "gemini")
    monkeypatch.delenv("QUANTLAB_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("QUANTLAB_LLM_MODEL", raising=False)
    base, model = resolve_llm_endpoint()
    assert "generativelanguage.googleapis.com" in base
    assert "openai" in base
    assert not base.endswith("/v1")
    assert "gemini" in model.lower()


def test_resolve_nvidia_preset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QUANTLAB_LLM_PROVIDER", "nvidia")
    monkeypatch.delenv("QUANTLAB_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("QUANTLAB_LLM_MODEL", raising=False)
    base, model = resolve_llm_endpoint()
    assert "integrate.api.nvidia.com" in base
    assert base.endswith("/v1")
    assert "llama" in model.lower() or "meta/" in model


def test_env_overrides_preset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QUANTLAB_LLM_PROVIDER", "gemini")
    monkeypatch.setenv("QUANTLAB_LLM_BASE_URL", "http://127.0.0.1:1234/v1")
    monkeypatch.setenv("QUANTLAB_LLM_MODEL", "local-model")
    base, model = resolve_llm_endpoint()
    assert base == "http://127.0.0.1:1234/v1"
    assert model == "local-model"
