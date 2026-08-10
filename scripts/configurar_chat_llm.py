"""Escribe QUANTLAB_LLM_* en .env (Gemini / NVIDIA / OpenAI).

Uso interactivo:
  .venv\\Scripts\\python.exe scripts\\configurar_chat_llm.py

Uso no interactivo:
  python scripts/configurar_chat_llm.py gemini TU_API_KEY
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ENV_PATH = REPO / ".env"
EXAMPLE = REPO / ".env.example"

PROVIDERS = {
    "1": ("gemini", "https://aistudio.google.com/apikey"),
    "2": ("nvidia", "https://build.nvidia.com"),
    "3": ("openai", "https://platform.openai.com/api-keys"),
    "gemini": ("gemini", "https://aistudio.google.com/apikey"),
    "nvidia": ("nvidia", "https://build.nvidia.com"),
    "openai": ("openai", "https://platform.openai.com/api-keys"),
}

LLM_KEYS = (
    "QUANTLAB_LLM_PROVIDER",
    "QUANTLAB_LLM_API_KEY",
    "QUANTLAB_LLM_BASE_URL",
    "QUANTLAB_LLM_MODEL",
)


def upsert_env(path: Path, updates: dict[str, str]) -> None:
    if not path.is_file():
        if EXAMPLE.is_file():
            text = EXAMPLE.read_text(encoding="utf-8")
        else:
            text = ""
    else:
        text = path.read_text(encoding="utf-8")

    lines = text.splitlines()
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            out.append(line)
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in updates:
            out.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            out.append(line)

    for key, val in updates.items():
        if key not in seen:
            out.append(f"{key}={val}")

    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    if len(argv) >= 3:
        provider_key = argv[1].strip().lower()
        api_key = argv[2].strip()
    else:
        print("Configurar Chat IA — QuantLab")
        print()
        print("1) Gemini  (gratis — aistudio.google.com/apikey)")
        print("2) NVIDIA  (gratis — build.nvidia.com)")
        print("3) OpenAI  (paga)")
        print()
        choice = input("Elegí 1-3: ").strip()
        if choice not in PROVIDERS:
            print("Cancelado.")
            return 1
        provider_key = choice
        _, url = PROVIDERS[choice]
        print(f"Obtené la key en: {url}")
        api_key = input("Pegá la API key: ").strip()

    if provider_key not in PROVIDERS:
        print(f"Provider inválido: {provider_key}")
        return 1
    if not api_key or api_key.upper() == "DISABLED":
        print("API key vacía.")
        return 1
    # Evitar inyección accidental de saltos de línea
    if re.search(r"[\r\n]", api_key):
        print("API key inválida.")
        return 1

    provider, _ = PROVIDERS[provider_key]
    updates = {
        "QUANTLAB_LLM_PROVIDER": provider,
        "QUANTLAB_LLM_API_KEY": api_key,
        "QUANTLAB_LLM_BASE_URL": "",
        "QUANTLAB_LLM_MODEL": "",
    }
    upsert_env(ENV_PATH, updates)
    print(f"OK: .env actualizado → provider={provider}")
    print("Ahora ejecutá este.bat")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
