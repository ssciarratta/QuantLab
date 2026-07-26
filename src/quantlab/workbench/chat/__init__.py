"""Chat IA safe-by-default del workbench (Fase 22 / DEC-063).

Solo herramientas de lectura/explicación. Nunca opera mercado ni flippea LIVE.
"""

from __future__ import annotations

from quantlab.workbench.chat.orchestrator import ChatOrchestrator, build_orchestrator
from quantlab.workbench.chat.providers import FakeProvider, OptionalEnvProvider
from quantlab.workbench.chat.tools import ALLOWED_TOOLS, FORBIDDEN_TOOLS, ToolRegistry

__all__ = [
    "ALLOWED_TOOLS",
    "FORBIDDEN_TOOLS",
    "ChatOrchestrator",
    "FakeProvider",
    "OptionalEnvProvider",
    "ToolRegistry",
    "build_orchestrator",
]
