"""Coding agent — basic edits via DeepSeek; complex architecture escalates to Nemotron.

It proposes code/diffs as DRAFTS for human review. It never modifies production code, installs
tools, or runs shell commands (those are gated actions handled elsewhere).
"""

from __future__ import annotations

from agents.worker_base import WorkerAgent


class CodingAgent(WorkerAgent):
    name = "coding_agent"
    default_complexity = "normal"  # router escalates to Nemotron when state.complexity == "complex"
    system_prompt = WorkerAgent.system_prompt + (
        " Role: software assistant. Propose code or diffs as a DRAFT only, with a short rationale. "
        "Do not modify production code, install packages, or run commands — those need approval."
    )

    def build_user_prompt(self, state) -> str:
        return f"Coding request: {state.user_request}\nReturn a proposed change as a DRAFT (code + brief rationale)."
