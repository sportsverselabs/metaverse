"""Sportsverse OS — LangGraph orchestration layer (Phase 4).

The stateful agent graph that Hermes routes tasks through. Import the engine lazily via
``run_task`` to avoid heavy imports when only the state/types are needed.
"""

from orchestration.routes import NODE_NAMES  # noqa: F401
from orchestration.state import OrchestrationState  # noqa: F401

__all__ = ["OrchestrationState", "NODE_NAMES", "run_task", "build_services", "engine_name"]


def __getattr__(name):  # lazy re-export to avoid importing agents/providers at package import
    if name in {"run_task", "build_services", "engine_name"}:
        from orchestration import langgraph_app
        return getattr(langgraph_app, name)
    raise AttributeError(name)
