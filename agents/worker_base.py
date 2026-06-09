"""Shared base for Phase 4 worker agents.

A worker takes the orchestration state, builds a prompt, and calls the cost-aware
:class:`~providers.model_router.ModelRouter`. Workers produce DRAFTS / analysis only — they
never publish, post, email, spend, install, or touch production systems. The router decides
DeepSeek vs Nemotron and enforces the cost gate; a worker just consumes the result.

Uses duck typing on ``state`` (no import of the state class) to avoid import cycles.
"""

from __future__ import annotations

from typing import Any

from core.logging_setup import get_logger

_SAFE_SYSTEM = (
    "You are an agent in the SportsVersusNews operating system (a low-cost, gated, "
    "human-in-the-loop sports/news business). Produce a DRAFT or analysis ONLY. You must "
    "never publish, post, send email, spend money, install tools, run shell commands, or "
    "change production systems. Flag anything that needs compliance review."
)


class WorkerAgent:
    name = "worker"
    default_complexity = "normal"
    system_prompt = _SAFE_SYSTEM

    def __init__(self, model_router, logger=None) -> None:
        self.model_router = model_router
        self.log = logger or get_logger(f"agent.{self.name}")

    def build_user_prompt(self, state: Any) -> str:
        return state.user_request

    def run(self, state: Any) -> Any:
        complexity = getattr(state, "complexity", None) or self.default_complexity
        task_type = getattr(state, "task_type", None) or self.name
        user = self.build_user_prompt(state)
        result = self.model_router.complete(user, task_type=task_type, system=self.system_prompt, complexity=complexity)

        state.model_provider = result.provider
        state.model_name = result.model
        state.est_tokens = result.est_tokens
        state.est_cost = result.est_cost
        state.is_mock = result.is_mock
        state.tools_used.append(self.name)

        if result.needs_approval:
            # Cost gate tripped inside the router — produce nothing; route to approval.
            state.needs_approval = True
            state.approval_kind = "cost"
            state.approval_reasons.append(result.note or "estimated cost exceeds budget threshold")
            state.output = ""
        else:
            state.output = result.text
        return state
