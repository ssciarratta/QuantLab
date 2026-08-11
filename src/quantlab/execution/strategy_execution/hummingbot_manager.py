"""Gestor de proceso Hummingbot (MVP read-only + deploy stub)."""

from __future__ import annotations

from typing import Any

from quantlab.execution_export.hummingbot_probe import (
    hummingbot_status,
    verify_hummingbot_testnet_safety,
)


class HummingbotProcessManager:
    """MVP: health/readiness sin spawn ni order routing."""

    def status(self) -> dict[str, Any]:
        base = hummingbot_status()
        safety = verify_hummingbot_testnet_safety()
        return {
            "ok": True,
            "process_running": bool(base.get("installed")),
            "detection_method": base.get("detection_method"),
            "spot_testnet_connector_available": base.get("spot_testnet_connector_available"),
            "recommended_perp_testnet_connector": base.get("recommended_perp_testnet_connector"),
            "recommended_spot_paper_connector": base.get("recommended_spot_paper_connector"),
            "safety_ok": safety.get("ok"),
            "safety_issues": safety.get("issues"),
            "quantlab_export_only": True,
            "ipc_available": False,
            "note": "IPC/deploy HB pendiente — Fase H del roadmap.",
        }

    def preflight_for_futures(self) -> dict[str, Any]:
        st = self.status()
        ready = bool(st.get("process_running")) and bool(st.get("safety_ok"))
        return {
            "hummingbot_detected": st.get("process_running"),
            "safety_ok": st.get("safety_ok"),
            "ready_for_strategy_load": ready,
            "blockers": [] if ready else ["Hummingbot no detectado o configs inseguras"],
        }


def get_hummingbot_manager() -> HummingbotProcessManager:
    return HummingbotProcessManager()
