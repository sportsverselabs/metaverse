"""Phase 4 provider layer.

Builds on ``core.providers`` (the LLMProvider interface + DeepSeek/mock) and adds:
- a Nemotron/NeMo adapter (optional; disabled by default),
- a cost-aware :class:`~providers.model_router.ModelRouter` that picks DeepSeek for routine
  work and Nemotron for complex reasoning, tracks tokens/cost, and gates over-budget tasks to
  human approval.

Providers are pluggable via the ``LLMProvider`` interface — no provider logic is hard-coded
into agents.
"""

from providers.deepseek_provider import DeepSeekProvider  # noqa: F401
from providers.nemotron_provider import NemotronProvider  # noqa: F401
from providers.model_router import (  # noqa: F401
    COMPLEX_TASK_TYPES,
    CostTracker,
    ModelResult,
    ModelRouter,
)

__all__ = [
    "DeepSeekProvider",
    "NemotronProvider",
    "ModelRouter",
    "ModelResult",
    "CostTracker",
    "COMPLEX_TASK_TYPES",
]
