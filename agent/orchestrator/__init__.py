"""Public exports for the orchestrator package.

Keep imports lazy to avoid circular imports with `agent.reasoning.engine`.
"""

from __future__ import annotations

from typing import Any

__all__ = ["Orchestrator", "run_chat_loop"]


def __getattr__(name: str) -> Any:
    if name == "Orchestrator":
        from agent.orchestrator.orchestrator import Orchestrator

        return Orchestrator
    if name == "run_chat_loop":
        from agent.orchestrator.chat_loop import run_chat_loop

        return run_chat_loop
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
