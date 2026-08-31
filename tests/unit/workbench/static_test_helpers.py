"""Helpers para tests de assets estáticos del workbench."""

from __future__ import annotations

from pathlib import Path


def static_root() -> Path:
    return Path(__file__).resolve().parents[3] / "src" / "quantlab" / "workbench" / "static"


def read_static(rel: str) -> str:
    return (static_root() / rel).read_text(encoding="utf-8")


def assert_panel_registered(pane_id: str) -> None:
    registry = read_static("js/panel_registry.js")
    assert f'id: "{pane_id}"' in registry
