"""Content agent — drafts captions/scripts/ideas (DeepSeek by default). Draft only, never posts."""

from __future__ import annotations

from agents.worker_base import WorkerAgent


class ContentAgent(WorkerAgent):
    name = "content_agent"
    default_complexity = "normal"
    system_prompt = WorkerAgent.system_prompt + (
        " Role: content writer for SportsVersusNews. Produce DRAFT content (titles, hooks, "
        "captions, script outlines). Mark it clearly as a draft. Never publish or post."
    )

    def build_user_prompt(self, state) -> str:
        return f"Content request: {state.user_request}\nReturn a clearly-labelled DRAFT for owner review."
