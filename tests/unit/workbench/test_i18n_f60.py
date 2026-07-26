"""F60 — i18n scaffold (es default, en stub) del workbench."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from quantlab import __version__
from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import ApiError, WorkbenchState, handle_get_i18n
from quantlab.workbench.i18n import (
    DEFAULT_LOCALE,
    SUPPORTED_LOCALES,
    build_i18n_payload,
    load_messages,
    normalize_locale,
)
from quantlab.workbench.settings import ALLOWED_LOCALES, default_settings, normalize_settings

_ROOT = Path(__file__).resolve().parents[3]
_STATIC = _ROOT / "src" / "quantlab" / "workbench" / "static"
_INDEX = _STATIC / "index.html"
_I18N_JS = _STATIC / "js" / "i18n.js"
_SHELL_JS = _STATIC / "js" / "shell.js"
_ES_JSON = _STATIC / "i18n" / "es.json"
_EN_JSON = _STATIC / "i18n" / "en.json"


def test_live_blocked_and_version_f60() -> None:
    assert LIVE_BLOCKED is True
    assert __version__ == "0.62.0"
    assert PHASES_SUMMARY == "F19–F70 INTERNAL"


def test_default_locale_es() -> None:
    assert DEFAULT_LOCALE == "es"
    assert "es" in SUPPORTED_LOCALES
    assert "en" in SUPPORTED_LOCALES
    assert frozenset({"es", "en"}) == ALLOWED_LOCALES
    assert default_settings()["locale"] == "es"


def test_normalize_locale() -> None:
    assert normalize_locale("es") == "es"
    assert normalize_locale("EN") == "en"
    assert normalize_locale("es-AR") == "es"
    with pytest.raises(ValidationError):
        normalize_locale("fr")


def test_load_messages_parity_json() -> None:
    es = load_messages("es")
    en = load_messages("en")
    assert es["skip_to_content"] == "Ir al contenido"
    assert en["skip_to_content"] == "Skip to content"
    assert set(es.keys()) == set(en.keys())
    assert "pane.health" in es
    assert "btn.save" in es
    disk_es = json.loads(_ES_JSON.read_text(encoding="utf-8"))
    disk_en = json.loads(_EN_JSON.read_text(encoding="utf-8"))
    assert disk_es == es
    assert disk_en == en


def test_build_i18n_payload() -> None:
    payload = build_i18n_payload("es")
    assert payload["ok"] is True
    assert payload["kind"] == "i18n"
    assert payload["locale"] == "es"
    assert payload["default_locale"] == "es"
    assert payload["live_blocked"] is True
    assert payload["live_routing"] is False
    assert "menu.workspaces" in payload["messages"]


def test_handle_get_i18n() -> None:
    state = WorkbenchState()
    body = handle_get_i18n(state, "en")
    assert body["locale"] == "en"
    assert body["messages"]["pane.about"] == "About"
    with pytest.raises(ApiError) as exc:
        handle_get_i18n(state, "de")
    assert exc.value.status == 400


def test_settings_accepts_en_locale() -> None:
    saved = normalize_settings(
        {
            "version": 1,
            "theme": "slate",
            "default_venue": "paper",
            "default_strategy": "momentum",
            "slippage_bps": "0",
            "locale": "en",
        }
    )
    assert saved["locale"] == "en"


def test_i18n_js_and_shell_wired() -> None:
    js = _I18N_JS.read_text(encoding="utf-8")
    assert "function t(" in js or "t: t" in js
    assert "QLi18n" in js
    assert "applyDom" in js
    assert "DEFAULT_LOCALE = \"es\"" in js
    assert "es:" in js and "en:" in js
    shell = _SHELL_JS.read_text(encoding="utf-8")
    assert "applyLocale" in shell
    assert "QLi18n" in shell
    assert "settings.locale" in shell or "settingsData.settings.locale" in shell


def test_index_html_data_i18n_and_script() -> None:
    html = _INDEX.read_text(encoding="utf-8")
    assert 'src="/static/js/i18n.js"' in html
    assert 'data-i18n="skip_to_content"' in html
    assert 'data-i18n="pane.health"' in html
    assert 'data-i18n="menu.workspaces"' in html
    assert 'lang="es"' in html
    assert "Ir al contenido" in html


def test_no_fase_60_approved() -> None:
    assert not (_ROOT / "docs" / "audit" / "FASE_60_APPROVED.md").exists()
