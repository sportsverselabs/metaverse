"""Nemotron reasoning agent — complex reasoning / planning / high-value decisions.

Defaults to ``complexity="complex"`` so the model router prefers Nemotron. If Nemotron is
disabled or unavailable, the router transparently falls back to DeepSeek. Output is analysis /
a recommendation DRAFT for the owner — never an executed action.
"""

from __future__ import annotations

from agents.worker_base import WorkerAgent


class NemotronReasoningAgent(WorkerAgent):
    name = "nemotron_reasoning_agent"
    default_complexity = "complex"
    system_prompt = WorkerAgent.system_prompt + (
        " Role: senior strategist/architect. Do careful step-by-step reasoning for complex "
        "analysis, planning, architecture, or high-value business decisions. Present options, "
        "trade-offs, and a recommendation as a DRAFT for the owner to decide. Take no action."
    )

    def build_user_prompt(self, state) -> str:
        return (f"Reasoning task: {state.user_request}\n"
                "Think step by step. Give options, trade-offs, and a clear recommendation (DRAFT).")
