#!/usr/bin/env python3
"""Demo scanner QuantLab — SOLO research (playground).

Uso (desde la raíz del repo):
  uv run python playground/scan_demo.py
"""

from __future__ import annotations

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.lab_services import run_lab_scanner


def main() -> None:
    assert LIVE_BLOCKED is True, "LIVE debe permanecer bloqueado"
    print(f"QuantLab {__version__} · LIVE_BLOCKED={LIVE_BLOCKED}")

    result = run_lab_scanner(top_n=3)
    print("ok:", result.get("ok"))
    print("selected:", result.get("selected"))
    for score in result.get("scores") or []:
        iid = score.get("instrument_id") or score.get("symbol")
        print(f"  - {iid}: {score}")


if __name__ == "__main__":
    main()
